import sqlite3
from datetime import timedelta

from flask import (
  Flask,
  request,
)
from werkzeug.exceptions import Forbidden

from .logging import configure_logging
from .routes import register_routes
from .services.data.db import (
  get_db,
  init_db,
)
from .services.data.setup import is_first_run
from .templatetags import format_datetime


def _database_initialized():
  connection = None

  try:
    connection = get_db()

    result = connection.execute(
      """
      SELECT 1
      FROM sqlite_master
      WHERE type = 'table'
        AND name = 'inventory_items'
      """
    ).fetchone()

    return result is not None

  except sqlite3.OperationalError as oe:
    if oe.sqlite_errorcode == sqlite3.SQLITE_CANTOPEN:
      return False

    # Any other database failure means we cannot confirm initialization.
    return False

  finally:
    if connection is not None:
      connection.close()


_SAFE_METHODS = ("GET", "HEAD", "OPTIONS", "TRACE")
_ALLOWED_FETCH_SITES = ("same-origin", "none")


def _csrf_protect():
  if request.method in _SAFE_METHODS:
    return None

  sec_fetch_site = request.headers.get("Sec-Fetch-Site")

  if sec_fetch_site is None:
    # Older browsers do not send the header; SameSite=Lax still protects them.
    return None

  if sec_fetch_site in _ALLOWED_FETCH_SITES:
    return None

  raise Forbidden("Cross-site request blocked")


def create_app():
  app = Flask(__name__)

  configure_logging()

  app.config.from_object("config")
  app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=30)
  app.config["SESSION_COOKIE_SAMESITE"] = "Lax"

  app.before_request(_csrf_protect)

  app.jinja_env.filters["datetime"] = format_datetime

  if not _database_initialized():
    app.logger.warning("Database not initialized.")
    init_db(app.logger)

  app.config["FIRST_RUN"] = is_first_run()

  register_routes(app)

  return app

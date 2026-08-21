import sqlite3
from datetime import timedelta

from flask import Flask

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
  finally:
    if connection is not None:
      connection.close()


def create_app():
  app = Flask(__name__)
  app.config.from_object("config")

  app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=30)

  app.jinja_env.filters["datetime"] = format_datetime
  if not _database_initialized():
    app.logger.warning("Database not initialized.")
    init_db(app.logger)

  app.config["FIRST_RUN"] = is_first_run()

  register_routes(app)

  return app

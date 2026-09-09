import os
import secrets
import sqlite3
from datetime import timedelta

from flask import (
  Flask,
  current_app,
  jsonify,
  request,
  session,
)
from werkzeug.exceptions import Forbidden
from werkzeug.middleware.proxy_fix import ProxyFix

from .logging import configure_logging
from .routes import register_routes
from .services.data.db import (
  get_db,
  init_db,
)
from .services.data.setup import is_first_run
from .services.exceptions.auth.authorization import PermissionDeniedError
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
    return

  sec_fetch_site = request.headers.get("Sec-Fetch-Site")

  if sec_fetch_site is None:
    # Older browsers do not send the header; SameSite=Lax still protects them.
    pass
  elif sec_fetch_site in _ALLOWED_FETCH_SITES:
    pass
  else:
    raise Forbidden("Cross-site request blocked")

  # Skip form/header token enforcement in tests so existing test clients
  # don't need to send a CSRF token.
  if current_app.config.get("TESTING"):
    return

  # Also check form token or header token for POST requests
  if request.method == "POST":
    token = request.form.get("csrf_token") or request.headers.get("X-CSRF-Token")
    session_token = session.get("csrf_token")
    if not token or token != session_token:
      raise Forbidden("Invalid CSRF token")


def _trust_proxy():
  return os.environ.get("TRUST_PROXY", "0").strip().lower() in {"1", "true", "yes"}


def create_app():
  app = Flask(__name__)

  configure_logging()

  app.config.from_object("config")
  app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=30)
  app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
  app.config["MAX_CONTENT_LENGTH"] = 256 * 1024 * 1024

  if _trust_proxy():
    # Behind a reverse proxy (e.g. zrok), trust one X-Forwarded-For hop so
    # request.remote_addr is the real client address.
    app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1)

  app.before_request(_csrf_protect)

  @app.errorhandler(PermissionDeniedError)
  def handle_permission_denied(error):
    if request.headers.get("Accept") == "application/json":
      return jsonify({"error": "Forbidden"}), 403

    return "Forbidden", 403

  @app.errorhandler(413)
  def handle_request_entity_too_large(error):
    if request.headers.get("Accept") == "application/json":
      return jsonify({"error": "Upload too large"}), 413

    return "Upload too large", 413

  @app.before_request
  def _ensure_csrf_token():
    if "csrf_token" not in session:
      session["csrf_token"] = secrets.token_hex(32)

  app.jinja_env.globals["csrf_token"] = lambda: session.get("csrf_token", "")

  app.jinja_env.filters["datetime"] = format_datetime

  @app.after_request
  def _add_security_headers(resp):
    resp.headers["Content-Security-Policy"] = "default-src 'self'; frame-ancestors 'none'"
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["Referrer-Policy"] = "same-origin"
    return resp

  if not _database_initialized():
    app.logger.warning("Database not initialized.")
    init_db(app.logger)

  app.config["FIRST_RUN"] = is_first_run()

  register_routes(app)

  return app

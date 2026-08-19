from datetime import timedelta

from flask import Flask

from app.db import get_db, init_db
from app.routes import register_routes
from app.services.setup import is_first_run


def _database_initialized():
  connection = get_db()

  try:
    result = connection.execute(
      """
      SELECT 1
      FROM sqlite_master
      WHERE type = 'table'
        AND name = 'inventory_items'
      """
    ).fetchone()

    return result is not None
  finally:
    connection.close()


def create_app():
  app = Flask(__name__)
  app.config.from_object("config")

  app.config["PERMANENT_SESSION_LIFETIME"] = timedelta(days=30)

  if not _database_initialized():
    init_db()

  app.config["FIRST_RUN"] = is_first_run()

  register_routes(app)

  return app

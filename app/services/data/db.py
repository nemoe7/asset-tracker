import sqlite3
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path

import config

SCHEMA_PATH = Path(__file__).resolve().parents[3] / "database" / "schema.sql"

_connection_context = ContextVar(
  "database_connection",
  default=None,
)


def get_db(db_path=None):
  connection = _connection_context.get()

  if connection is not None:
    return connection

  db_path = db_path or config.DB_PATH

  connection = sqlite3.connect(db_path)
  connection.row_factory = sqlite3.Row
  connection.execute("PRAGMA foreign_keys = ON")

  return connection


@contextmanager
def db_connection(db_path=None):
  connection = _connection_context.get()

  if connection is not None:
    yield connection
    return

  connection = get_db(db_path)
  token = _connection_context.set(connection)

  try:
    yield connection
  finally:
    _connection_context.reset(token)
    connection.close()


@contextmanager
def db_transaction(db_path=None):
  connection = get_db(db_path)

  owns_connection = _connection_context.get() is None

  if not owns_connection:
    yield connection
    return

  token = _connection_context.set(connection)

  try:
    yield connection
    connection.commit()
  except Exception:
    connection.rollback()
    raise
  finally:
    _connection_context.reset(token)
    connection.close()


def init_db(logger=None, db_path=None):
  if logger:
    logger.warning(f"Initializing database: {db_path}")

  db_path = db_path or config.DB_PATH
  db_path.parent.mkdir(parents=True, exist_ok=True)

  connection = get_db(db_path)

  with SCHEMA_PATH.open() as file:
    connection.executescript(file.read())

  connection.close()

  if logger:
    logger.warning(f"Database initialized: {db_path}")


if __name__ == "__main__":
  init_db()

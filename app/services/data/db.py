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
  connection.execute("PRAGMA journal_mode = WAL")
  connection.execute("PRAGMA busy_timeout = 5000")

  return connection


@contextmanager
def db_connection(db_path=None):
  connection = _connection_context.get()

  if connection is not None:
    if db_path is not None:
      raise ValueError("db_path is ignored when a connection is already open")

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
    if db_path is not None:
      raise ValueError("db_path is ignored when a connection is already open")

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

  # Open a dedicated connection so init_db never closes one owned by an
  # outer db_connection/db_transaction context.
  connection = sqlite3.connect(db_path)

  try:
    with SCHEMA_PATH.open() as file:
      connection.executescript(file.read())
  finally:
    connection.close()

  if logger:
    logger.warning(f"Database initialized: {db_path}")


def reset_database(db_path=None):
  db_path = db_path or config.DB_PATH
  db_path.parent.mkdir(parents=True, exist_ok=True)

  connection = sqlite3.connect(db_path)
  connection.execute("PRAGMA foreign_keys = ON")

  tables = connection.execute(
    "SELECT name FROM sqlite_master WHERE type='table'"
  ).fetchall()

  connection.execute("PRAGMA foreign_keys = OFF")

  for table in tables:
    connection.execute(f"DROP TABLE IF EXISTS {table[0]}")

  connection.execute("PRAGMA foreign_keys = ON")
  connection.commit()
  connection.close()

  init_db(db_path=db_path)


if __name__ == "__main__":
  init_db()

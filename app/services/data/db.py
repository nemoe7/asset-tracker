import sqlite3
from pathlib import Path

import config

SCHEMA_PATH = Path("database/schema.sql")


def get_db(db_path=None):
  db_path = db_path or config.DB_PATH

  connection = sqlite3.connect(db_path)
  connection.row_factory = sqlite3.Row
  connection.execute("PRAGMA foreign_keys = ON")

  return connection


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

import sqlite3
from pathlib import Path

DB_PATH = Path("data/inventory.db")
SCHEMA_PATH = Path("database/schema.sql")


def init_db():
  DB_PATH.parent.mkdir(parents=True, exist_ok=True)

  connection = get_db()

  with SCHEMA_PATH.open() as file:
    connection.executescript(file.read())

  connection.close()


def get_db():
  connection = sqlite3.connect(DB_PATH)
  connection.row_factory = sqlite3.Row
  connection.execute("PRAGMA foreign_keys = ON")

  return connection


if __name__ == "__main__":
  init_db()

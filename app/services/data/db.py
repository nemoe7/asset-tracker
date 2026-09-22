import sqlite3
from contextlib import contextmanager
from contextvars import ContextVar
from pathlib import Path

import config

SCHEMA_PATH = Path(__file__).resolve().parents[3] / "database" / "schema.sql"
MIGRATIONS_DIR = Path(__file__).resolve().parents[3] / "database" / "migrations"

# Encodes schema vX.Y.Z as major*10000 + minor*100 + patch.
# 0.1.0 -> 100 (baseline), 0.2.0 -> 200 (current)..
_BASELINE_VERSION = 100
_CURRENT_VERSION = 200

_connection_context = ContextVar(
  "database_connection",
  default=None,
)


def get_db(db_path=None):
  connection = _connection_context.get()

  if connection is not None:
    return connection

  db_path = db_path or config.DB_PATH
  db_path.parent.mkdir(parents=True, exist_ok=True)

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


def current_schema_version():
  return _CURRENT_VERSION


def _version_from_filename(path):
  # vMAJOR.MINOR.PATCH.sql
  stem = path.stem.removeprefix("v")

  parts = stem.split(".")

  if len(parts) != 3 or not all(part.isdigit() for part in parts):
    raise ValueError(f"Invalid migration filename: {path.name}")

  major, minor, patch = (int(part) for part in parts)

  return major * 1000 + minor * 100 + patch


def _pending_migrations(version):
  files = sorted(MIGRATIONS_DIR.glob("v*.sql"), key=_version_from_filename)

  return [path for path in files if _version_from_filename(path) > version]


def _migration_statements(script):
  statement = ""

  for character in script:
    statement += character

    if sqlite3.complete_statement(statement):
      if statement.strip().strip(";").strip():
        yield statement

      statement = ""

  if statement.strip():
    raise sqlite3.OperationalError("incomplete migration statement")


def _custom_field_name_allocator(connection):
  rows = connection.execute("SELECT id, name FROM custom_fields ORDER BY id").fetchall()
  used_names = set()
  names = {}

  for row in rows:
    old_name = row[1]
    new_name = old_name
    suffix = 2

    while new_name.casefold() in used_names:
      new_name = f"{old_name} ({suffix})"
      suffix += 1

    used_names.add(new_name.casefold())
    names[row[0]] = new_name

  return lambda field_id, _name: names[field_id]


def _prepare_migration(connection, migration_version):
  if migration_version == 103:
    connection.create_function(
      "migration_custom_field_name",
      2,
      _custom_field_name_allocator(connection),
    )


def apply_pending_migrations(logger=None, db_path=None):
  db_path = db_path or config.DB_PATH

  # Open a dedicated connection so migrations never close one owned by an
  # outer db_connection/db_transaction context.
  connection = sqlite3.connect(db_path)

  try:
    connection.execute("PRAGMA foreign_keys = ON")

    version = connection.execute("PRAGMA user_version").fetchone()[0]

    has_tables = (
      connection.execute(
        """
      SELECT 1
      FROM sqlite_master
      WHERE type = 'table'
        AND name NOT LIKE 'sqlite_%'
      LIMIT 1
      """
      ).fetchone()
      is not None
    )

    if not has_tables:
      # Fresh/empty database: init_db() creates the current schema directly.
      connection.close()
      init_db(logger=logger, db_path=db_path)
      return

    if version == 0:
      # Pre-migration database: schema matches the v0.1.0 baseline.
      version = _BASELINE_VERSION

    pending = _pending_migrations(version)

    for path in pending:
      migration_version = _version_from_filename(path)

      if logger:
        logger.warning(f"Applying migration {path.name} (version {migration_version})")

      try:
        # PRAGMA foreign_keys cannot change inside a transaction. Disable it
        # first, then execute each statement without executescript(), which
        # would commit the active transaction before running the script.
        connection.execute("PRAGMA foreign_keys = OFF")
        connection.execute("BEGIN")
        _prepare_migration(connection, migration_version)

        for statement in _migration_statements(path.read_text()):
          connection.execute(statement)

        connection.execute(f"PRAGMA user_version = {migration_version}")
        connection.commit()
      except Exception:
        connection.rollback()
        raise
      finally:
        connection.execute("PRAGMA foreign_keys = ON")

    if logger and pending:
      logger.warning(f"Migrations applied: database at version {_CURRENT_VERSION}")
  finally:
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

    connection.execute(f"PRAGMA user_version = {_CURRENT_VERSION}")
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

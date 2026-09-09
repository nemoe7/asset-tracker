import pytest

from app.services.data.db import db_connection, db_transaction


def test_db_transaction_rejects_db_path_when_nested(gen_test_data_admin):
  with db_connection():
    with pytest.raises(ValueError):
      with db_transaction(db_path="other.db"):
        pass


def test_db_connection_rejects_db_path_when_nested(gen_test_data_admin):
  with db_transaction():
    with pytest.raises(ValueError):
      with db_connection(db_path="other.db"):
        pass


def test_db_connection_enables_wal_mode(gen_test_data_admin):
  with db_connection() as connection:
    mode = connection.execute("PRAGMA journal_mode").fetchone()[0]

    assert mode == "wal"


def test_db_connection_sets_busy_timeout(gen_test_data_admin):
  with db_connection() as connection:
    timeout = connection.execute("PRAGMA busy_timeout").fetchone()[0]

    assert timeout == 5000

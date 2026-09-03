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

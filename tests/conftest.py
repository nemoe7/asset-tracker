import sqlite3
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config
from app.context import reset_current_user, set_current_user
from app.db import init_db


@pytest.fixture
def test_db(tmp_path, monkeypatch):
  db_path = tmp_path / "test.db"

  monkeypatch.setattr(config, "DB_PATH", db_path)

  init_db()

  connection = sqlite3.connect(db_path)

  result = connection.execute(
    """
    INSERT INTO users (
      username,
      password_hash,
      created_at,
      updated_at
    )
    VALUES (
      'test_user',
      'test_password_hash',
      datetime('now'),
      datetime('now')
    )
    """
  )

  user_id = result.lastrowid

  connection.commit()
  connection.close()

  token = set_current_user(user_id)

  try:
    yield db_path
  finally:
    reset_current_user(token)

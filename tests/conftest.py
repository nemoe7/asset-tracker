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

  connection.execute(
    """
    INSERT INTO users (
      username,
      password_hash,
      created_at,
      updated_at
    )
    VALUES (
      'test_admin',
      'test_password_hash',
      datetime('now'),
      datetime('now')
    )
    """
  )

  connection.commit()
  connection.close()

  yield db_path


@pytest.fixture
def test_user_id(test_db):
  connection = sqlite3.connect(test_db)

  try:
    result = connection.execute(
      """
      SELECT id
      FROM users
      WHERE username = 'test_admin'
      """
    ).fetchone()

    return result[0]
  finally:
    connection.close()


@pytest.fixture
def authenticated_test_user(test_user_id):
  token = set_current_user(test_user_id)

  try:
    yield test_user_id
  finally:
    reset_current_user(token)

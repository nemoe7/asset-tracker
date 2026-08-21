import sqlite3
import sys
from pathlib import Path

import pytest
from werkzeug.security import generate_password_hash

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import config
from app.services.auth.context import reset_current_user, set_current_user
from app.services.data.db import init_db
from app.services.data.users import create_user, get_user_by_username


@pytest.fixture
def gen_test_db(tmp_path, monkeypatch):
  db_path = tmp_path / "test.db"

  monkeypatch.setattr(config, "DB_PATH", db_path)

  init_db()

  connection = sqlite3.connect(db_path)

  connection.execute(
    """
    INSERT INTO users (
      username,
      name,
      password_hash,
      created_at,
      updated_at
    )
    VALUES (?, ?, ?, datetime('now'), datetime('now'))
    """,
    ("test_admin", "Test Admin", generate_password_hash("test_password")),
  )

  connection.commit()
  connection.close()

  yield db_path


@pytest.fixture
def gen_test_admin(gen_test_db):
  user = get_user_by_username("test_admin")
  test_admin_id = user["id"]

  token = set_current_user(test_admin_id)

  try:
    yield test_admin_id
  finally:
    reset_current_user(token)


@pytest.fixture
def gen_test_user(gen_test_admin, gen_test_password):
  def _create(username, name=None, password=None):
    if name is None:
      name = username.capitalize()

    if password is None:
      password = gen_test_password(username)

    return create_user(
      username=username,
      name=name,
      password=password,
    )

  return _create


@pytest.fixture
def gen_test_password():
  def _create(username):
    password = username
    count = 0

    while len(password) < 8:
      count += 1
      password = f"{username}{count}"

    return password

  return _create

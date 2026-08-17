from app.db import get_db
from app.services.users import (
  archive_user,
  create_user,
  get_user,
  get_user_by_username,
  get_users,
  verify_password,
)


def test_valid_credentials_are_accepted(test_db):
  user_id = create_user(
    username="alice",
    password="correct-password",
  )

  assert (
    verify_password(
      user_id,
      "correct-password",
    )
    is True
  )


def test_invalid_password_is_rejected(test_db):
  user_id = create_user(
    username="alice",
    password="correct-password",
  )

  assert (
    verify_password(
      user_id,
      "wrong-password",
    )
    is False
  )


def test_nonexistent_user_is_rejected(test_db):
  assert (
    verify_password(
      999,
      "correct-password",
    )
    is False
  )


def test_archived_user_is_rejected(test_db):
  user_id = create_user(
    username="alice",
    password="correct-password",
  )

  assert archive_user(user_id) is True

  assert (
    verify_password(
      user_id,
      "correct-password",
    )
    is False
  )


def test_password_hash_is_not_returned_by_user_queries(test_db):
  user_id = create_user(
    username="alice",
    password="correct-password",
  )

  user = get_user(user_id)
  user_by_username = get_user_by_username("alice")
  users = get_users()

  assert "password_hash" not in user
  assert "password_hash" not in user_by_username

  for result in users:
    assert "password_hash" not in result


def test_password_is_stored_as_a_hash(test_db):
  user_id = create_user(
    username="alice",
    password="correct-password",
  )

  connection = get_db()

  try:
    user = connection.execute(
      """
      SELECT password_hash
      FROM users
      WHERE id = ?
      """,
      (user_id,),
    ).fetchone()
  finally:
    connection.close()

  assert user["password_hash"] != "correct-password"
  assert user["password_hash"] is not None

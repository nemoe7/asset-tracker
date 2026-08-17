from app.context import get_current_user, reset_current_user, set_current_user
from app.services.users import (
  archive_user,
  create_user,
  get_user,
  get_user_by_username,
  get_users,
  verify_password,
)


def test_valid_credentials_are_accepted(test_db, authenticated_test_user):
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


def test_invalid_password_is_rejected(test_db, authenticated_test_user):
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


def test_archived_user_is_rejected(test_db, authenticated_test_user):
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


def test_password_hash_is_not_returned_by_user_queries(
  test_db, authenticated_test_user
):
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


def test_password_is_stored_as_a_hash(test_db, authenticated_test_user):
  user_id = create_user(
    username="alice",
    password="correct-password",
  )

  from app.db import get_db

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


def test_set_current_user_sets_user_id(test_db):
  token = set_current_user(1)

  try:
    assert get_current_user() == 1
  finally:
    reset_current_user(token)


def test_reset_current_user_restores_previous_user(test_db):
  token = set_current_user(1)

  try:
    assert get_current_user() == 1
  finally:
    reset_current_user(token)

  assert get_current_user() is None


def test_authentication_contract_valid_credentials_set_current_user(
  test_db, authenticated_test_user
):
  user_id = create_user(
    username="alice",
    password="correct-password",
  )

  token = set_current_user(user_id)

  try:
    assert get_current_user() == user_id
  finally:
    reset_current_user(token)


def test_failed_authentication_does_not_establish_user(
  test_db, authenticated_test_user
):
  user_id = create_user(
    username="alice",
    password="correct-password",
  )

  token = set_current_user(None)

  try:
    assert (
      verify_password(
        user_id,
        "wrong-password",
      )
      is False
    )

    assert get_current_user() is None
  finally:
    reset_current_user(token)


def test_current_user_can_be_replaced(test_db, authenticated_test_user):
  first_user_id = create_user(
    username="alice",
    password="password-one",
  )

  second_user_id = create_user(
    username="bob",
    password="password-two",
  )

  first_token = set_current_user(first_user_id)

  try:
    assert get_current_user() == first_user_id

    second_token = set_current_user(second_user_id)

    try:
      assert get_current_user() == second_user_id
    finally:
      reset_current_user(second_token)
  finally:
    reset_current_user(first_token)

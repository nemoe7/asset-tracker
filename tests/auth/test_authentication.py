from app.services.auth.context import (
  get_current_user,
  reset_current_user,
  set_current_user,
)
from app.services.data.users import (
  archive_user,
  get_user,
  get_user_by_username,
  get_users,
  verify_password,
)


def test_valid_credentials_are_accepted(gen_test_user, gen_test_password):
  user_id = gen_test_user("alice")
  password = gen_test_password("alice")

  assert (
    verify_password(
      user_id,
      password,
    )
    is True
  )


def test_invalid_password_is_rejected(gen_test_user, gen_test_password):
  user_id = gen_test_user("alice")
  wrong_password = gen_test_password("bob")

  assert (
    verify_password(
      user_id,
      wrong_password,
    )
    is False
  )


def test_nonexistent_user_is_rejected(gen_test_db):
  assert (
    verify_password(
      999,
      "correct-password",
    )
    is False
  )


def test_archived_user_is_rejected(gen_test_user, gen_test_password):
  user_id = gen_test_user("alice")
  password = gen_test_password("alice")

  assert archive_user(user_id) is True

  assert (
    verify_password(
      user_id,
      password,
    )
    is False
  )


def test_password_hash_is_not_returned_by_user_queries(gen_test_user):
  user_id = gen_test_user("alice")

  user = get_user(user_id)
  user_by_username = get_user_by_username("alice")
  users = get_users()

  assert "password_hash" not in user
  assert "password_hash" not in user_by_username

  for result in users:
    assert "password_hash" not in result


def test_password_is_stored_as_a_hash(
  gen_test_user,
  gen_test_password,
):
  user_id = gen_test_user("alice")
  password = gen_test_password("alice")

  from app.services.data.db import get_db

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

  assert user["password_hash"] != password
  assert user["password_hash"] is not None


def test_set_current_user_sets_user_id(gen_test_admin):
  user_id = gen_test_admin
  token = set_current_user(user_id)

  try:
    assert get_current_user() == user_id
  finally:
    reset_current_user(token)


def test_authentication_contract_valid_credentials_set_current_user(gen_test_user):
  user_id = gen_test_user("alice")

  token = set_current_user(user_id)

  try:
    assert get_current_user() == user_id
  finally:
    reset_current_user(token)


def test_failed_authentication_does_not_establish_user(gen_test_user):
  user_id = gen_test_user("alice")

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


def test_current_user_can_be_replaced(gen_test_user):
  first_user_id = gen_test_user("alice")

  second_user_id = gen_test_user("bob")

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

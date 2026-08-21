import pytest

from app.services.data.audit import get_audit_logs
from app.services.data.users import (
  archive_user,
  create_user,
  get_user,
  get_user_by_username,
  get_users,
  restore_user,
  update_user,
  verify_password,
)
from app.services.exceptions.data.common import InvalidInputError
from app.services.exceptions.data.users import *


def test_create_user(gen_test_user):
  user_id = gen_test_user("alice")

  assert user_id is not None

  user = get_user(user_id)

  assert user["id"] == user_id
  assert user["username"] == "alice"
  assert user["archived_at"] is None


def test_create_user_with_duplicate_username_fails(gen_test_user):
  gen_test_user("alice")

  with pytest.raises(UsernameAlreadyExistsError):
    gen_test_user("alice")


def test_create_user_with_empty_username_fails(gen_test_user):
  with pytest.raises(
    InvalidUsernameError,
    match="Username cannot be empty",
  ):
    gen_test_user("")


def test_create_user_with_all_whitespace_username_fails(gen_test_user):
  with pytest.raises(
    InvalidUsernameError,
    match="Username cannot be empty",
  ):
    gen_test_user("   ")


def test_create_user_with_whitespace_username_fails(gen_test_user):
  with pytest.raises(
    InvalidUsernameError,
    match="Username can only contain letters, numbers, periods, underscores, and hyphens",
  ):
    gen_test_user("ali ce")


def test_create_user_with_username_too_short_fails(gen_test_user):
  with pytest.raises(
    InvalidUsernameError,
    match="Username must be at least 3 characters",
  ):
    gen_test_user("ab")


def test_create_user_with_username_too_long_fails(gen_test_user):
  with pytest.raises(
    InvalidUsernameError,
    match="Username must be at most 32 characters",
  ):
    gen_test_user("a" * 33)


def test_create_user_with_invalid_username_characters_fails(gen_test_user):
  with pytest.raises(
    InvalidUsernameError,
    match="Username can only contain letters, numbers, periods, underscores, and hyphens",
  ):
    gen_test_user("alice@123")


def test_create_user_with_non_ascii_username_fails(gen_test_user):
  with pytest.raises(
    InvalidUsernameError,
    match="Username can only contain letters, numbers, periods, underscores, and hyphens",
  ):
    gen_test_user("alicé")


def test_create_user_with_username_only_special_characters_fails(
  gen_test_user,
):
  with pytest.raises(
    InvalidUsernameError,
    match="Username must contain at least one letter or number",
  ):
    gen_test_user("---")


def test_create_user_with_minimum_length_username_succeeds(gen_test_user):
  user_id = gen_test_user("abc")

  assert get_user(user_id)["username"] == "abc"


def test_create_user_with_maximum_length_username_succeeds(gen_test_user):
  username = "a" * 32
  user_id = gen_test_user(username)

  assert get_user(user_id)["username"] == username


def test_create_user_with_valid_special_characters_succeeds(gen_test_user):
  username = "alice_dev-123.test"
  user_id = gen_test_user(username)

  assert get_user(user_id)["username"] == username


def test_create_user_with_empty_password_fails(gen_test_user):
  with pytest.raises(
    InvalidPasswordError,
    match="Password cannot be empty",
  ):
    gen_test_user("alice", password="")


def test_create_user_with_password_too_short_fails(gen_test_user):
  with pytest.raises(
    InvalidPasswordError,
    match="Password must be at least 8 characters",
  ):
    gen_test_user("alice", password="1234567")


def test_create_user_with_password_too_long_fails(gen_test_user):
  with pytest.raises(
    InvalidPasswordError,
    match="Password must be at most 128 characters",
  ):
    gen_test_user("alice", password="a" * 129)


def test_create_user_with_minimum_length_password_succeeds(gen_test_user):
  password = "12345678"
  user_id = gen_test_user("alice", password=password)

  assert verify_password(user_id, password)


def test_create_user_with_maximum_length_password_succeeds(gen_test_user):
  password = "a" * 128
  user_id = gen_test_user("alice", password=password)

  assert verify_password(user_id, password)


def test_create_user_with_unicode_password_succeeds(gen_test_user):
  password = "密码密码密码密码"
  user_id = gen_test_user("alice", password=password)

  assert verify_password(user_id, password)


def test_create_user_with_spaces_in_password_succeeds(gen_test_user):
  password = "correct horse battery staple"
  user_id = gen_test_user("alice", password=password)

  assert verify_password(user_id, password)


def test_get_user(gen_test_user):
  user_id = gen_test_user("alice")
  user = get_user(user_id)

  assert user["id"] == user_id
  assert user["username"] == "alice"


def test_get_user_by_username(gen_test_user):
  user_id = gen_test_user("alice")
  user = get_user_by_username("alice")

  assert user["id"] == user_id
  assert user["username"] == "alice"
  assert user["archived_at"] is None


def test_get_users(gen_test_user):
  gen_test_user("alice")
  gen_test_user("bob")

  users = get_users()

  assert len(users) == 3  # admin, alice, bob
  assert users[0]["username"] == "alice"
  assert users[1]["username"] == "bob"


def test_get_nonexistent_user(gen_test_db):
  assert get_user(999) is None


def test_get_nonexistent_username(gen_test_db):
  assert get_user_by_username("does-not-exist") is None


def test_update_user_username(gen_test_user):
  user_id = gen_test_user("alice")

  assert update_user(user_id, username="alice2") is True

  user = get_user(user_id)

  assert user["username"] == "alice2"


def test_update_user_name(gen_test_user):
  user_id = gen_test_user("alice")

  assert update_user(user_id, name="Alice Smith") is True

  user = get_user(user_id)

  assert user["name"] == "Alice Smith"


def test_update_user_password(gen_test_user, gen_test_password):
  user_id = gen_test_user("alice")

  assert update_user(user_id, password="newpassword") is True

  assert verify_password(user_id, "newpassword")
  assert not verify_password(user_id, gen_test_password("alice"))


def test_update_user_with_same_username_creates_no_audit_log(gen_test_user):
  user_id = gen_test_user("alice")

  assert update_user(user_id, username="alice") is True

  logs = get_audit_logs(
    entity_type="user",
    entity_id=user_id,
  )

  assert len(logs) == 1
  assert logs[0]["action"] == "created"


def test_update_user_with_same_name_creates_no_audit_log(gen_test_user):
  user_id = gen_test_user("alice")

  assert update_user(user_id, name="Alice") is True

  logs = get_audit_logs(
    entity_type="user",
    entity_id=user_id,
  )

  assert len(logs) == 1
  assert logs[0]["action"] == "created"


def test_update_user_with_same_password_creates_no_audit_log(
  gen_test_user,
  gen_test_password,
):
  user_id = gen_test_user("alice")

  assert (
    update_user(
      user_id,
      password=gen_test_password("alice"),
    )
    is True
  )

  logs = get_audit_logs(
    entity_type="user",
    entity_id=user_id,
  )

  assert len(logs) == 1
  assert logs[0]["action"] == "created"


def test_update_user_to_existing_username_fails(gen_test_user):
  gen_test_user("alice")
  user_id = gen_test_user("bob")

  with pytest.raises(UsernameAlreadyExistsError):
    update_user(user_id, username="alice")


def test_failed_username_update_creates_no_audit_log(gen_test_user):
  gen_test_user("alice")
  user_id = gen_test_user("bob")

  with pytest.raises(UsernameAlreadyExistsError):
    update_user(user_id, username="alice")

  logs = get_audit_logs(
    entity_type="user",
    entity_id=user_id,
  )

  assert len(logs) == 1
  assert logs[0]["action"] == "created"


def test_update_user_with_no_fields_fails(gen_test_user):
  user_id = gen_test_user("alice")

  with pytest.raises(
    InvalidInputError,
    match="No fields to update",
  ):
    update_user(user_id)


def test_update_user_with_empty_username_fails(gen_test_user):
  user_id = gen_test_user("alice")

  with pytest.raises(
    InvalidUsernameError,
    match="Username cannot be empty",
  ):
    update_user(user_id, username="")


def test_update_user_with_all_whitespace_username_fails(gen_test_user):
  user_id = gen_test_user("alice")

  with pytest.raises(
    InvalidUsernameError,
    match="Username cannot be empty",
  ):
    update_user(
      user_id,
      username="   ",
    )


def test_update_user_with_whitespace_username_fails(gen_test_user):
  user_id = gen_test_user("alice")

  with pytest.raises(
    InvalidUsernameError,
    match="Username can only contain letters, numbers, periods, underscores, and hyphens",
  ):
    update_user(
      user_id,
      username="ali ce",
    )


def test_update_user_with_too_short_username_fails(gen_test_user):
  user_id = gen_test_user("alice")

  with pytest.raises(
    InvalidUsernameError,
    match="Username must be at least 3 characters",
  ):
    update_user(user_id, username="al")


def test_update_user_with_too_long_username_fails(gen_test_user):
  user_id = gen_test_user("alice")

  with pytest.raises(
    InvalidUsernameError,
    match="Username must be at most 32 characters",
  ):
    update_user(user_id, username="a" * 33)


def test_update_user_with_invalid_username_characters_fails(gen_test_user):
  user_id = gen_test_user("alice")

  with pytest.raises(
    InvalidUsernameError,
    match="Username can only contain letters, numbers, periods, underscores, and hyphens",
  ):
    update_user(user_id, username="alice@123")


def test_update_user_with_non_ascii_username_fails(gen_test_user):
  user_id = gen_test_user("alice")

  with pytest.raises(
    InvalidUsernameError,
    match="Username can only contain letters, numbers, periods, underscores, and hyphens",
  ):
    update_user(user_id, username="alicé")


def test_update_user_with_only_special_characters_username_fails(gen_test_user):
  user_id = gen_test_user("alice")

  with pytest.raises(
    InvalidUsernameError,
    match="Username must contain at least one letter or number",
  ):
    update_user(
      user_id,
      username="---",
    )


def test_update_user_with_minimum_length_username(gen_test_user):
  user_id = gen_test_user("alice")

  assert update_user(user_id, username="a" * 3) is True


def test_update_user_with_maximum_length_username(gen_test_user):
  user_id = gen_test_user("alice")

  assert update_user(user_id, username="a" * 32) is True


def test_update_user_with_empty_password_fails(gen_test_user):
  user_id = gen_test_user("alice")

  with pytest.raises(
    InvalidPasswordError,
    match="Password cannot be empty",
  ):
    update_user(user_id, password="")


def test_update_user_with_too_short_password_fails(gen_test_user):
  user_id = gen_test_user("alice")

  with pytest.raises(
    InvalidPasswordError,
    match="Password must be at least 8 characters",
  ):
    update_user(user_id, password="1" * 7)


def test_update_user_with_too_long_password_fails(gen_test_user):
  user_id = gen_test_user("alice")

  with pytest.raises(
    InvalidPasswordError,
    match="Password must be at most 128 characters",
  ):
    update_user(user_id, password="a" * 129)


def test_update_nonexistent_user(gen_test_db):
  with pytest.raises(UserNotFoundError):
    update_user(999, username="alice")


def test_update_archived_user_fails(gen_test_user):
  user_id = gen_test_user("alice")

  assert archive_user(user_id) is True

  with pytest.raises(UserIsArchivedError):
    update_user(user_id, username="alice2")


def test_archive_user(gen_test_user):
  user_id = gen_test_user("alice")

  assert archive_user(user_id) is True

  user = get_user(user_id)

  assert user is not None
  assert user["username"] == "alice"
  assert user["archived_at"] is not None


def test_archive_user_excludes_user_from_active_queries(gen_test_user):
  user_id = gen_test_user("alice")

  assert archive_user(user_id) is True
  assert get_user_by_username("alice") is None
  assert len(get_users()) == 1  # only admin


def test_cannot_archive_already_archived_user(gen_test_user):
  user_id = gen_test_user("alice")

  assert archive_user(user_id) is True

  with pytest.raises(UserIsArchivedError):
    archive_user(user_id)


def test_archive_nonexistent_user(gen_test_db):
  with pytest.raises(UserNotFoundError):
    archive_user(999)


def test_restore_archived_user(gen_test_user):
  user_id = gen_test_user("alice")

  assert archive_user(user_id) is True
  assert restore_user(user_id) is True

  user = get_user(user_id)

  assert user is not None
  assert user["username"] == "alice"
  assert user["archived_at"] is None
  assert len(get_users()) == 2


def test_cannot_restore_active_user(gen_test_user):
  user_id = gen_test_user("alice")

  with pytest.raises(UserIsNotArchivedError):
    restore_user(user_id)


def test_restore_nonexistent_user(gen_test_db):
  with pytest.raises(UserNotFoundError):
    restore_user(999)


def test_password_can_be_verified(gen_test_user, gen_test_password):
  user_id = gen_test_user("alice")

  assert verify_password(
    user_id,
    gen_test_password("alice"),
  )


def test_wrong_password_cannot_be_verified(gen_test_user):
  user_id = gen_test_user("alice")

  assert not verify_password(
    user_id,
    "wrongpassword",
  )


def test_archived_user_password_cannot_be_verified(gen_test_user):
  user_id = gen_test_user("alice")

  assert archive_user(user_id) is True
  assert not verify_password(user_id, "alice123")


def test_create_user_with_archived_username_fails(gen_test_user):
  user_id = gen_test_user("alice")

  assert archive_user(user_id) is True

  with pytest.raises(UsernameIsArchivedError):
    create_user(
      username="alice",
      password="password456",
    )


def test_update_user_to_archived_username_fails(gen_test_user):
  archived_user_id = gen_test_user("alice")

  assert archive_user(archived_user_id) is True

  user_id = gen_test_user("bob")

  with pytest.raises(UsernameIsArchivedError):
    update_user(
      user_id,
      username="alice",
    )

import json

import pytest

from app.services.audit import get_audit_logs
from app.services.users import (
  archive_user,
  create_user,
  get_user,
  get_user_by_username,
  get_users,
  restore_user,
  update_user,
  verify_password,
)

# Create


def test_create_user(test_db, authenticated_test_user):
  user_id = create_user(
    username="alice",
    password="password123",
  )

  assert user_id is not None

  user = get_user(user_id)

  assert user["id"] == user_id
  assert user["username"] == "alice"
  assert user["archived_at"] is None


def test_create_user_creates_audit_log(test_db, authenticated_test_user):
  user_id = create_user(
    username="alice",
    password="password123",
  )

  logs = get_audit_logs(
    entity_type="user",
    entity_id=user_id,
  )

  assert len(logs) == 1
  assert logs[0]["user_id"] == 1
  assert logs[0]["action"] == "created"


def test_create_user_with_duplicate_username_fails(test_db, authenticated_test_user):
  create_user(
    username="alice",
    password="password123",
  )

  with pytest.raises(
    ValueError,
    match="Username already exists",
  ):
    create_user(
      username="alice",
      password="password456",
    )


def test_create_user_with_empty_username_fails(test_db):
  with pytest.raises(
    ValueError,
    match="Username cannot be empty",
  ):
    create_user(
      username="",
      password="password123",
    )


def test_create_user_with_whitespace_username_fails(test_db):
  with pytest.raises(
    ValueError,
    match="Username cannot be empty",
  ):
    create_user(
      username="   ",
      password="password123",
    )


def test_create_user_with_empty_password_fails(test_db):
  with pytest.raises(
    ValueError,
    match="Password cannot be empty",
  ):
    create_user(
      username="alice",
      password="",
    )


# Read


def test_get_user(test_db, authenticated_test_user):
  user_id = create_user(
    username="alice",
    password="password123",
  )

  user = get_user(user_id)

  assert user["id"] == user_id
  assert user["username"] == "alice"


def test_get_user_by_username(test_db, authenticated_test_user):
  user_id = create_user(
    username="alice",
    password="password123",
  )

  user = get_user_by_username("alice")

  assert user["id"] == user_id
  assert user["username"] == "alice"


def test_get_users(test_db, authenticated_test_user):
  create_user(
    username="alice",
    password="password123",
  )

  create_user(
    username="bob",
    password="password456",
  )

  users = get_users()

  assert len(users) == 3
  assert users[0]["username"] == "alice"
  assert users[1]["username"] == "bob"


def test_get_nonexistent_user(test_db):
  assert get_user(999) is None


def test_get_nonexistent_username(test_db):
  assert get_user_by_username("does-not-exist") is None


# Update


def test_update_user_username(test_db, authenticated_test_user):
  user_id = create_user(
    username="alice",
    password="password123",
  )

  assert (
    update_user(
      user_id,
      username="alice2",
    )
    is True
  )

  user = get_user(user_id)

  assert user["username"] == "alice2"


def test_update_user_password(test_db, authenticated_test_user):
  user_id = create_user(
    username="alice",
    password="password123",
  )

  assert (
    update_user(
      user_id,
      password="newpassword",
    )
    is True
  )

  assert verify_password(
    user_id,
    "newpassword",
  )

  assert not verify_password(
    user_id,
    "password123",
  )


def test_update_user_creates_audit_log(test_db, authenticated_test_user):
  user_id = create_user(
    username="alice",
    password="password123",
  )

  assert (
    update_user(
      user_id,
      username="alice2",
      password="newpassword",
    )
    is True
  )

  logs = get_audit_logs(
    entity_type="user",
    entity_id=user_id,
  )

  assert len(logs) == 2
  assert logs[0]["action"] == "created"
  assert logs[1]["action"] == "updated"
  assert logs[1]["user_id"] == 1

  details = json.loads(logs[1]["details"])

  assert details["username"] == {
    "old": "alice",
    "new": "alice2",
  }

  assert details["password"] == "changed"


def test_update_user_with_same_username_creates_no_audit_log(
  test_db, authenticated_test_user
):
  user_id = create_user(
    username="alice",
    password="password123",
  )

  assert (
    update_user(
      user_id,
      username="alice",
    )
    is True
  )

  logs = get_audit_logs(
    entity_type="user",
    entity_id=user_id,
  )

  assert len(logs) == 1
  assert logs[0]["action"] == "created"


def test_update_user_to_existing_username_fails(test_db, authenticated_test_user):
  create_user(
    username="alice",
    password="password123",
  )

  user_id = create_user(
    username="bob",
    password="password456",
  )

  with pytest.raises(
    ValueError,
    match="Username already exists",
  ):
    update_user(
      user_id,
      username="alice",
    )


def test_failed_username_update_creates_no_audit_log(test_db, authenticated_test_user):
  create_user(
    username="alice",
    password="password123",
  )

  user_id = create_user(
    username="bob",
    password="password456",
  )

  with pytest.raises(
    ValueError,
    match="Username already exists",
  ):
    update_user(
      user_id,
      username="alice",
    )

  logs = get_audit_logs(
    entity_type="user",
    entity_id=user_id,
  )

  assert len(logs) == 1
  assert logs[0]["action"] == "created"


def test_update_user_with_no_fields_fails(test_db, authenticated_test_user):
  user_id = create_user(
    username="alice",
    password="password123",
  )

  with pytest.raises(
    ValueError,
    match="No fields to update",
  ):
    update_user(user_id)


def test_update_user_with_empty_username_fails(test_db, authenticated_test_user):
  user_id = create_user(
    username="alice",
    password="password123",
  )

  with pytest.raises(
    ValueError,
    match="Username cannot be empty",
  ):
    update_user(
      user_id,
      username="",
    )


def test_update_user_with_empty_password_fails(test_db, authenticated_test_user):
  user_id = create_user(
    username="alice",
    password="password123",
  )

  with pytest.raises(
    ValueError,
    match="Password cannot be empty",
  ):
    update_user(
      user_id,
      password="",
    )


def test_update_nonexistent_user(test_db):
  assert (
    update_user(
      999,
      username="alice",
    )
    is False
  )


# Archive


def test_archive_user(test_db, authenticated_test_user):
  user_id = create_user(
    username="alice",
    password="password123",
  )

  assert archive_user(user_id) is True

  user = get_user(user_id)

  assert user is not None
  assert user["username"] == "alice"
  assert user["archived_at"] is not None


def test_archive_user_excludes_user_from_active_queries(
  test_db, authenticated_test_user
):
  user_id = create_user(
    username="alice",
    password="password123",
  )

  assert archive_user(user_id) is True

  assert get_user_by_username("alice") is None
  assert len(get_users()) == 1


def test_archive_user_creates_audit_log(test_db, authenticated_test_user):
  user_id = create_user(
    username="alice",
    password="password123",
  )

  assert archive_user(user_id) is True

  logs = get_audit_logs(
    entity_type="user",
    entity_id=user_id,
  )

  assert len(logs) == 2
  assert logs[0]["action"] == "created"
  assert logs[1]["action"] == "archived"
  assert logs[1]["user_id"] == 1


def test_cannot_archive_already_archived_user(test_db, authenticated_test_user):
  user_id = create_user(
    username="alice",
    password="password123",
  )

  assert archive_user(user_id) is True
  assert archive_user(user_id) is False


def test_archive_nonexistent_user(test_db):
  assert archive_user(999) is False


# Restore


def test_restore_user(test_db, authenticated_test_user):
  user_id = create_user(
    username="alice",
    password="password123",
  )

  assert archive_user(user_id) is True
  assert restore_user(user_id) is True

  user = get_user(user_id)

  assert user is not None
  assert user["username"] == "alice"
  assert user["archived_at"] is None

  assert len(get_users()) == 2


def test_restore_user_creates_audit_log(test_db, authenticated_test_user):
  user_id = create_user(
    username="alice",
    password="password123",
  )

  assert archive_user(user_id) is True
  assert restore_user(user_id) is True

  logs = get_audit_logs(
    entity_type="user",
    entity_id=user_id,
  )

  assert len(logs) == 3
  assert logs[0]["action"] == "created"
  assert logs[1]["action"] == "archived"
  assert logs[2]["action"] == "restored"
  assert logs[2]["user_id"] == 1


def test_cannot_restore_active_user(test_db, authenticated_test_user):
  user_id = create_user(
    username="alice",
    password="password123",
  )

  assert restore_user(user_id) is False


def test_restore_nonexistent_user(test_db):
  assert restore_user(999) is False


# Password verification


def test_password_is_hashed(test_db, authenticated_test_user):
  user_id = create_user(
    username="alice",
    password="password123",
  )

  assert verify_password(user_id, "password123")


def test_password_can_be_verified(test_db, authenticated_test_user):
  user_id = create_user(
    username="alice",
    password="password123",
  )

  assert verify_password(
    user_id,
    "password123",
  )


def test_wrong_password_cannot_be_verified(test_db, authenticated_test_user):
  user_id = create_user(
    username="alice",
    password="password123",
  )

  assert not verify_password(
    user_id,
    "wrongpassword",
  )


def test_archived_user_password_cannot_be_verified(test_db, authenticated_test_user):
  user_id = create_user(
    username="alice",
    password="password123",
  )

  assert archive_user(user_id) is True

  assert not verify_password(
    user_id,
    "password123",
  )


def test_create_user_with_archived_username_fails(test_db, authenticated_test_user):
  user_id = create_user(
    username="alice",
    password="password123",
  )

  assert archive_user(user_id) is True

  with pytest.raises(
    ValueError,
    match="Username belongs to an archived user",
  ):
    create_user(
      username="alice",
      password="password456",
    )


def test_update_user_to_archived_username_fails(test_db, authenticated_test_user):
  archived_user_id = create_user(
    username="alice",
    password="password123",
  )

  assert archive_user(archived_user_id) is True

  user_id = create_user(
    username="bob",
    password="password456",
  )

  with pytest.raises(
    ValueError,
    match="Username already exists",
  ):
    update_user(
      user_id,
      username="alice",
    )

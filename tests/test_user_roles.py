import pytest

from app.services.audit import get_audit_logs
from app.services.roles import create_role, delete_role
from app.services.user_roles import (
  UserRoleAlreadyExistsError,
  assign_role_to_user,
  get_user_roles,
  remove_role_from_user,
)
from app.services.users import create_user


def test_assign_role_to_user(test_db):
  role_id = create_role(
    name="admin",
  )

  assert (
    assign_role_to_user(
      1,
      role_id,
    )
    is True
  )

  roles = get_user_roles(1)

  assert len(roles) == 1
  assert roles[0]["id"] == role_id
  assert roles[0]["name"] == "admin"


def test_get_user_roles_returns_empty_for_user_without_roles(
  test_db,
):
  assert get_user_roles(1) == []


def test_user_can_have_multiple_roles(test_db):
  first_role_id = create_role(
    name="admin",
  )

  second_role_id = create_role(
    name="manager",
  )

  assign_role_to_user(
    1,
    first_role_id,
  )

  assign_role_to_user(
    1,
    second_role_id,
  )

  roles = get_user_roles(1)

  role_ids = [role["id"] for role in roles]

  assert role_ids == sorted(
    [
      first_role_id,
      second_role_id,
    ]
  )


def test_role_can_be_assigned_to_multiple_users(test_db):
  second_user_id = create_user(
    username="second_user",
    password="test_password",
  )

  role_id = create_role(
    name="admin",
  )

  assign_role_to_user(
    1,
    role_id,
  )

  assign_role_to_user(
    second_user_id,
    role_id,
  )

  assert get_user_roles(1)[0]["id"] == role_id
  assert get_user_roles(second_user_id)[0]["id"] == role_id


def test_duplicate_role_assignment_is_rejected(test_db):
  role_id = create_role(
    name="admin",
  )

  assign_role_to_user(
    1,
    role_id,
  )

  with pytest.raises(UserRoleAlreadyExistsError):
    assign_role_to_user(
      1,
      role_id,
    )


def test_assign_role_to_nonexistent_user_is_rejected(test_db):
  role_id = create_role(
    name="admin",
  )

  with pytest.raises(ValueError):
    assign_role_to_user(
      999,
      role_id,
    )


def test_assign_nonexistent_role_to_user_is_rejected(test_db):
  with pytest.raises(ValueError):
    assign_role_to_user(
      1,
      999,
    )


def test_remove_role_from_user(test_db):
  role_id = create_role(
    name="admin",
  )

  assign_role_to_user(
    1,
    role_id,
  )

  assert (
    remove_role_from_user(
      1,
      role_id,
    )
    is True
  )

  assert get_user_roles(1) == []


def test_remove_missing_role_from_user_returns_false(test_db):
  role_id = create_role(
    name="admin",
  )

  assert (
    remove_role_from_user(
      1,
      role_id,
    )
    is False
  )


def test_get_user_roles_for_nonexistent_user_returns_empty(
  test_db,
):
  assert get_user_roles(999) == []


def test_assign_role_creates_audit_log(test_db):
  role_id = create_role(
    name="admin",
  )

  assign_role_to_user(
    1,
    role_id,
  )

  logs = get_audit_logs(
    entity_type="user_role",
    entity_id=f"1:{role_id}",
  )

  assert len(logs) == 1
  assert logs[0]["user_id"] == 1
  assert logs[0]["action"] == "created"


def test_remove_role_creates_audit_log(test_db):
  role_id = create_role(
    name="admin",
  )

  assign_role_to_user(
    1,
    role_id,
  )

  remove_role_from_user(
    1,
    role_id,
  )

  logs = get_audit_logs(
    entity_type="user_role",
    entity_id=f"1:{role_id}",
  )

  assert len(logs) == 2
  assert logs[0]["action"] == "created"
  assert logs[1]["action"] == "deleted"
  assert logs[1]["user_id"] == 1


def test_failed_duplicate_assignment_creates_no_audit_log(
  test_db,
):
  role_id = create_role(
    name="admin",
  )

  assign_role_to_user(
    1,
    role_id,
  )

  with pytest.raises(UserRoleAlreadyExistsError):
    assign_role_to_user(
      1,
      role_id,
    )

  logs = get_audit_logs(
    entity_type="user_role",
    entity_id=f"1:{role_id}",
  )

  assert len(logs) == 1
  assert logs[0]["action"] == "created"


def test_delete_role_cascades_user_roles(test_db):
  role_id = create_role(
    name="admin",
  )

  assign_role_to_user(
    1,
    role_id,
  )

  assert delete_role(role_id) is True

  assert get_user_roles(1) == []

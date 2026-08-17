import pytest

from app.services.audit import get_audit_logs
from app.services.permissions import (
  create_permission,
  delete_permission,
)
from app.services.user_permissions import (
  UserPermissionAlreadyExistsError,
  assign_permission_to_user,
  get_user_permissions,
  remove_permission_from_user,
)
from app.services.users import create_user


def test_assign_permission_to_user(test_db):
  permission_id = create_permission(
    name="inventory.view",
  )

  assert (
    assign_permission_to_user(
      1,
      permission_id,
    )
    is True
  )

  permissions = get_user_permissions(1)

  assert len(permissions) == 1
  assert permissions[0]["id"] == permission_id
  assert permissions[0]["name"] == "inventory.view"
  assert permissions[0]["allowed"] == 1


def test_get_user_permissions_returns_empty_for_user_without_permissions(
  test_db,
):
  assert get_user_permissions(1) == []


def test_user_can_have_multiple_permissions(test_db):
  first_permission_id = create_permission(
    name="inventory.view",
  )

  second_permission_id = create_permission(
    name="inventory.edit",
  )

  assign_permission_to_user(
    1,
    first_permission_id,
  )

  assign_permission_to_user(
    1,
    second_permission_id,
  )

  permissions = get_user_permissions(1)

  permission_ids = [permission["id"] for permission in permissions]

  assert permission_ids == [
    first_permission_id,
    second_permission_id,
  ]


def test_permission_can_be_assigned_to_multiple_users(test_db):
  second_user_id = create_user(
    username="second_user",
    password="test_password",
  )

  permission_id = create_permission(
    name="inventory.view",
  )

  assign_permission_to_user(
    1,
    permission_id,
  )

  assign_permission_to_user(
    second_user_id,
    permission_id,
  )

  assert get_user_permissions(1)[0]["id"] == permission_id
  assert get_user_permissions(second_user_id)[0]["id"] == permission_id


def test_duplicate_permission_assignment_is_rejected(test_db):
  permission_id = create_permission(
    name="inventory.view",
  )

  assign_permission_to_user(
    1,
    permission_id,
  )

  with pytest.raises(UserPermissionAlreadyExistsError):
    assign_permission_to_user(
      1,
      permission_id,
    )


def test_assign_permission_to_nonexistent_user_is_rejected(test_db):
  permission_id = create_permission(
    name="inventory.view",
  )

  with pytest.raises(ValueError):
    assign_permission_to_user(
      999,
      permission_id,
    )


def test_assign_nonexistent_permission_to_user_is_rejected(test_db):
  with pytest.raises(ValueError):
    assign_permission_to_user(
      1,
      999,
    )


def test_remove_permission_from_user(test_db):
  permission_id = create_permission(
    name="inventory.view",
  )

  assign_permission_to_user(
    1,
    permission_id,
  )

  assert (
    remove_permission_from_user(
      1,
      permission_id,
    )
    is True
  )

  assert get_user_permissions(1) == []


def test_remove_missing_permission_from_user_returns_false(test_db):
  permission_id = create_permission(
    name="inventory.view",
  )

  assert (
    remove_permission_from_user(
      1,
      permission_id,
    )
    is False
  )


def test_get_user_permissions_for_nonexistent_user_returns_empty(
  test_db,
):
  assert get_user_permissions(999) == []


def test_assign_permission_creates_audit_log(test_db):
  permission_id = create_permission(
    name="inventory.view",
  )

  assign_permission_to_user(
    1,
    permission_id,
  )

  logs = get_audit_logs(
    entity_type="user_permission",
    entity_id=f"1:{permission_id}",
  )

  assert len(logs) == 1
  assert logs[0]["user_id"] == 1
  assert logs[0]["action"] == "created"


def test_remove_permission_creates_audit_log(test_db):
  permission_id = create_permission(
    name="inventory.view",
  )

  assign_permission_to_user(
    1,
    permission_id,
  )

  remove_permission_from_user(
    1,
    permission_id,
  )

  logs = get_audit_logs(
    entity_type="user_permission",
    entity_id=f"1:{permission_id}",
  )

  assert len(logs) == 2
  assert logs[0]["action"] == "created"
  assert logs[1]["action"] == "deleted"
  assert logs[1]["user_id"] == 1


def test_failed_duplicate_assignment_creates_no_audit_log(
  test_db,
):
  permission_id = create_permission(
    name="inventory.view",
  )

  assign_permission_to_user(
    1,
    permission_id,
  )

  with pytest.raises(UserPermissionAlreadyExistsError):
    assign_permission_to_user(
      1,
      permission_id,
    )

  logs = get_audit_logs(
    entity_type="user_permission",
    entity_id=f"1:{permission_id}",
  )

  assert len(logs) == 1
  assert logs[0]["action"] == "created"


def test_delete_permission_cascades_user_permissions(test_db):
  permission_id = create_permission(
    name="inventory.view",
  )

  assign_permission_to_user(
    1,
    permission_id,
  )

  assert delete_permission(permission_id) is True

  assert get_user_permissions(1) == []

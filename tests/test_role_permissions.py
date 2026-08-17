import pytest
from app.services.role_permissions import (
  RolePermissionAlreadyExistsError,
  assign_permission_to_role,
  get_role_permissions,
  remove_permission_from_role,
)

from app.services.audit import get_audit_logs
from app.services.permissions import (
  create_permission,
  delete_permission,
)
from app.services.roles import (
  create_role,
  delete_role,
)


def test_assign_permission_to_role(test_db):
  role_id = create_role(
    name="Admin",
  )

  permission_id = create_permission(
    name="inventory.view",
  )

  assert (
    assign_permission_to_role(
      role_id,
      permission_id,
    )
    is True
  )

  permissions = get_role_permissions(role_id)

  assert len(permissions) == 1
  assert permissions[0]["id"] == permission_id
  assert permissions[0]["name"] == "inventory.view"


def test_get_role_permissions_returns_empty_for_role_without_permissions(
  test_db,
):
  role_id = create_role(
    name="Viewer",
  )

  assert get_role_permissions(role_id) == []


def test_role_can_have_multiple_permissions(test_db):
  role_id = create_role(
    name="Admin",
  )

  first_permission_id = create_permission(
    name="inventory.view",
  )

  second_permission_id = create_permission(
    name="inventory.edit",
  )

  assign_permission_to_role(
    role_id,
    first_permission_id,
  )

  assign_permission_to_role(
    role_id,
    second_permission_id,
  )

  permissions = get_role_permissions(role_id)

  permission_ids = [permission["id"] for permission in permissions]

  assert permission_ids == [
    first_permission_id,
    second_permission_id,
  ]


def test_permission_can_be_assigned_to_multiple_roles(test_db):
  first_role_id = create_role(
    name="Admin",
  )

  second_role_id = create_role(
    name="Manager",
  )

  permission_id = create_permission(
    name="inventory.view",
  )

  assign_permission_to_role(
    first_role_id,
    permission_id,
  )

  assign_permission_to_role(
    second_role_id,
    permission_id,
  )

  assert get_role_permissions(first_role_id)[0]["id"] == permission_id
  assert get_role_permissions(second_role_id)[0]["id"] == permission_id


def test_duplicate_permission_assignment_is_rejected(test_db):
  role_id = create_role(
    name="Admin",
  )

  permission_id = create_permission(
    name="inventory.view",
  )

  assign_permission_to_role(
    role_id,
    permission_id,
  )

  with pytest.raises(RolePermissionAlreadyExistsError):
    assign_permission_to_role(
      role_id,
      permission_id,
    )


def test_assign_permission_to_nonexistent_role_is_rejected(test_db):
  permission_id = create_permission(
    name="inventory.view",
  )

  with pytest.raises(ValueError):
    assign_permission_to_role(
      999,
      permission_id,
    )


def test_assign_nonexistent_permission_to_role_is_rejected(test_db):
  role_id = create_role(
    name="Admin",
  )

  with pytest.raises(ValueError):
    assign_permission_to_role(
      role_id,
      999,
    )


def test_remove_permission_from_role(test_db):
  role_id = create_role(
    name="Admin",
  )

  permission_id = create_permission(
    name="inventory.view",
  )

  assign_permission_to_role(
    role_id,
    permission_id,
  )

  assert (
    remove_permission_from_role(
      role_id,
      permission_id,
    )
    is True
  )

  assert get_role_permissions(role_id) == []


def test_remove_missing_permission_from_role_returns_false(test_db):
  role_id = create_role(
    name="Admin",
  )

  permission_id = create_permission(
    name="inventory.view",
  )

  assert (
    remove_permission_from_role(
      role_id,
      permission_id,
    )
    is False
  )


def test_get_role_permissions_for_nonexistent_role_returns_empty(
  test_db,
):
  assert get_role_permissions(999) == []


def test_assign_permission_creates_audit_log(test_db):
  role_id = create_role(
    name="Admin",
  )

  permission_id = create_permission(
    name="inventory.view",
  )

  assign_permission_to_role(
    role_id,
    permission_id,
  )

  logs = get_audit_logs(
    entity_type="role_permission",
    entity_id=f"{role_id}:{permission_id}",
  )

  assert len(logs) == 1
  assert logs[0]["user_id"] == 1
  assert logs[0]["action"] == "created"


def test_remove_permission_creates_audit_log(test_db):
  role_id = create_role(
    name="Admin",
  )

  permission_id = create_permission(
    name="inventory.view",
  )

  assign_permission_to_role(
    role_id,
    permission_id,
  )

  remove_permission_from_role(
    role_id,
    permission_id,
  )

  logs = get_audit_logs(
    entity_type="role_permission",
    entity_id=f"{role_id}:{permission_id}",
  )

  assert len(logs) == 2
  assert logs[0]["action"] == "created"
  assert logs[1]["action"] == "deleted"
  assert logs[1]["user_id"] == 1


def test_failed_duplicate_assignment_creates_no_audit_log(
  test_db,
):
  role_id = create_role(
    name="Admin",
  )

  permission_id = create_permission(
    name="inventory.view",
  )

  assign_permission_to_role(
    role_id,
    permission_id,
  )

  with pytest.raises(RolePermissionAlreadyExistsError):
    assign_permission_to_role(
      role_id,
      permission_id,
    )

  logs = get_audit_logs(
    entity_type="role_permission",
    entity_id=f"{role_id}:{permission_id}",
  )

  assert len(logs) == 1
  assert logs[0]["action"] == "created"


def test_delete_role_cascades_role_permissions(test_db):
  role_id = create_role(
    name="Admin",
  )

  permission_id = create_permission(
    name="inventory.view",
  )

  assign_permission_to_role(
    role_id,
    permission_id,
  )

  assert delete_role(role_id) is True

  assert get_role_permissions(role_id) == []


def test_delete_permission_cascades_role_permissions(test_db):
  role_id = create_role(
    name="Admin",
  )

  permission_id = create_permission(
    name="inventory.view",
  )

  assign_permission_to_role(
    role_id,
    permission_id,
  )

  assert delete_permission(permission_id) is True

  assert get_role_permissions(role_id) == []

import pytest

from app.services.data.audit import get_audit_logs
from app.services.data.permissions import create_permission
from app.services.data.role_permissions import (
  delete_role_permission,
  get_role_permission,
  get_role_permissions,
  set_role_permission,
)
from app.services.data.roles import create_role
from app.services.exceptions.data.permissions import PermissionNotFoundError
from app.services.exceptions.data.role_permissions import *
from app.services.exceptions.data.roles import RoleNotFoundError


def test_set_role_permission(gen_test_data_admin):
  role_id = create_role(
    name="Checker",
  )
  permission_id = create_permission(
    name="inventory.read",
  )

  assert (
    set_role_permission(
      role_id,
      permission_id,
      True,
    )
    is True
  )

  permission = get_role_permission(
    role_id,
    permission_id,
  )

  assert permission["role_id"] == role_id
  assert permission["permission_id"] == permission_id
  assert permission["allowed"] == 1


def test_set_role_permission_can_deny(gen_test_data_admin):
  role_id = create_role(
    name="Checker",
  )
  permission_id = create_permission(
    name="inventory.read",
  )

  set_role_permission(
    role_id,
    permission_id,
    False,
  )

  permission = get_role_permission(
    role_id,
    permission_id,
  )

  assert permission["allowed"] == 0


def test_set_role_permission_updates_existing_permission(gen_test_data_admin):
  role_id = create_role(
    name="Checker",
  )
  permission_id = create_permission(
    name="inventory.read",
  )

  set_role_permission(
    role_id,
    permission_id,
    True,
  )
  set_role_permission(
    role_id,
    permission_id,
    False,
  )

  permission = get_role_permission(
    role_id,
    permission_id,
  )

  assert permission["allowed"] == 0


@pytest.mark.parametrize(
  "allowed",
  [
    None,
    0,
    1,
    "true",
    "false",
  ],
)
def test_set_role_permission_rejects_non_boolean_allowed(
  gen_test_data_admin,
  allowed,
):
  role_id = create_role(
    name="Checker",
  )
  permission_id = create_permission(
    name="inventory.read",
  )

  with pytest.raises(InvalidRolePermissionAllowedError):
    set_role_permission(
      role_id,
      permission_id,
      allowed,
    )


def test_set_role_permission_rejects_missing_role(gen_test_data_admin):
  permission_id = create_permission(
    name="inventory.read",
  )

  with pytest.raises(RoleNotFoundError):
    set_role_permission(
      999,
      permission_id,
      True,
    )


def test_set_role_permission_rejects_missing_permission(gen_test_data_admin):
  role_id = create_role(
    name="Checker",
  )

  with pytest.raises(PermissionNotFoundError):
    set_role_permission(
      role_id,
      999,
      True,
    )


def test_get_role_permission_returns_none_when_missing(gen_test_data_admin):
  role_id = create_role(
    name="Checker",
  )
  permission_id = create_permission(
    name="inventory.read",
  )

  assert (
    get_role_permission(
      role_id,
      permission_id,
    )
    is None
  )


def test_get_role_permissions(gen_test_data_admin):
  role_id = create_role(
    name="Checker",
  )
  first_permission_id = create_permission(
    name="inventory.read",
  )
  second_permission_id = create_permission(
    name="inventory.update",
  )

  set_role_permission(
    role_id,
    first_permission_id,
    True,
  )
  set_role_permission(
    role_id,
    second_permission_id,
    False,
  )

  permissions = get_role_permissions(
    role_id,
  )

  assert len(permissions) == 2

  assert permissions[0]["role_id"] == role_id
  assert permissions[0]["permission_id"] == first_permission_id
  assert permissions[0]["permission"] == "inventory.read"
  assert permissions[0]["allowed"] == 1

  assert permissions[1]["role_id"] == role_id
  assert permissions[1]["permission_id"] == second_permission_id
  assert permissions[1]["permission"] == "inventory.update"
  assert permissions[1]["allowed"] == 0


def test_get_role_permissions_returns_empty_list(gen_test_data_admin):
  role_id = create_role(
    name="Checker",
  )

  assert get_role_permissions(role_id) == []


def test_get_role_permissions_rejects_missing_role(gen_test_data_admin):
  with pytest.raises(RoleNotFoundError):
    get_role_permissions(999)


def test_delete_role_permission(gen_test_data_admin):
  role_id = create_role(
    name="Checker",
  )
  permission_id = create_permission(
    name="inventory.read",
  )

  set_role_permission(
    role_id,
    permission_id,
    True,
  )

  assert (
    delete_role_permission(
      role_id,
      permission_id,
    )
    is True
  )

  assert (
    get_role_permission(
      role_id,
      permission_id,
    )
    is None
  )


def test_delete_role_permission_rejects_missing_permission_mapping(
  gen_test_data_admin,
):
  role_id = create_role(
    name="Checker",
  )
  permission_id = create_permission(
    name="inventory.read",
  )

  with pytest.raises(RolePermissionNotFoundError):
    delete_role_permission(
      role_id,
      permission_id,
    )


def test_set_role_permission_no_op_does_not_create_audit_log(
  gen_test_data_admin,
):
  role_id = create_role(
    name="Test Role",
  )

  permission_id = create_permission(
    name="inventory.read",
  )

  set_role_permission(
    role_id,
    permission_id,
    True,
  )

  audit_logs_before = get_audit_logs()

  set_role_permission(
    role_id,
    permission_id,
    True,
  )

  audit_logs_after = get_audit_logs()

  assert len(audit_logs_after) == len(audit_logs_before)


def test_set_role_permission_change_creates_audit_log(
  gen_test_data_admin,
):
  role_id = create_role(
    name="Test Role",
  )

  permission_id = create_permission(
    name="inventory.read",
  )

  set_role_permission(
    role_id,
    permission_id,
    True,
  )

  audit_logs_before = get_audit_logs()

  set_role_permission(
    role_id,
    permission_id,
    False,
  )

  audit_logs_after = get_audit_logs()

  assert len(audit_logs_after) == len(audit_logs_before) + 1

import pytest

from app.services.data.audit import get_audit_logs
from app.services.data.permissions import create_permission
from app.services.data.user_permissions import (
  delete_user_permission,
  get_user_permission,
  get_user_permissions,
  set_user_permission,
)
from app.services.exceptions.data.permissions import PermissionNotFoundError
from app.services.exceptions.data.user_permissions import *
from app.services.exceptions.data.users import UserNotFoundError


def test_set_user_permission(gen_test_admin):

  user_id = gen_test_admin

  permission_id = create_permission(
    name="inventory.read",
  )

  assert (
    set_user_permission(
      user_id,
      permission_id,
      True,
    )
    is True
  )

  permission = get_user_permission(
    user_id,
    permission_id,
  )

  assert permission["user_id"] == user_id

  assert permission["permission_id"] == permission_id

  assert permission["allowed"] == 1


def test_set_user_permission_can_deny(gen_test_admin):

  user_id = gen_test_admin

  permission_id = create_permission(
    name="inventory.read",
  )

  set_user_permission(
    user_id,
    permission_id,
    False,
  )

  permission = get_user_permission(
    user_id,
    permission_id,
  )

  assert permission["allowed"] == 0


def test_set_user_permission_updates_existing_permission(gen_test_admin):

  user_id = gen_test_admin

  permission_id = create_permission(
    name="inventory.read",
  )

  set_user_permission(
    user_id,
    permission_id,
    True,
  )

  set_user_permission(
    user_id,
    permission_id,
    False,
  )

  permission = get_user_permission(
    user_id,
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
def test_set_user_permission_rejects_non_boolean_allowed(
  gen_test_admin,
  allowed,
):

  user_id = gen_test_admin

  permission_id = create_permission(
    name="inventory.read",
  )

  with pytest.raises(InvalidUserPermissionAllowedError):
    set_user_permission(
      user_id,
      permission_id,
      allowed,
    )


def test_set_user_permission_rejects_missing_user(gen_test_admin):

  permission_id = create_permission(
    name="inventory.read",
  )

  with pytest.raises(UserNotFoundError):
    set_user_permission(
      999,
      permission_id,
      True,
    )


def test_set_user_permission_rejects_missing_permission(gen_test_admin):

  user_id = gen_test_admin

  with pytest.raises(PermissionNotFoundError):
    set_user_permission(
      user_id,
      999,
      True,
    )


def test_get_user_permission_returns_none_when_missing(gen_test_admin):

  user_id = gen_test_admin

  permission_id = create_permission(
    name="inventory.read",
  )

  assert (
    get_user_permission(
      user_id,
      permission_id,
    )
    is None
  )


def test_get_user_permissions(gen_test_admin):

  user_id = gen_test_admin

  first_permission_id = create_permission(
    name="inventory.read",
  )

  second_permission_id = create_permission(
    name="inventory.update",
  )

  set_user_permission(
    user_id,
    first_permission_id,
    True,
  )

  set_user_permission(
    user_id,
    second_permission_id,
    False,
  )

  permissions = get_user_permissions(
    user_id,
  )

  assert len(permissions) == 2

  assert permissions[0]["user_id"] == user_id

  assert permissions[0]["permission_id"] == first_permission_id

  assert permissions[0]["permission"] == "inventory.read"

  assert permissions[0]["allowed"] == 1

  assert permissions[1]["user_id"] == user_id

  assert permissions[1]["permission_id"] == second_permission_id

  assert permissions[1]["permission"] == "inventory.update"

  assert permissions[1]["allowed"] == 0


def test_get_user_permissions_returns_empty_list(gen_test_admin):

  user_id = gen_test_admin

  assert get_user_permissions(user_id) == []


def test_get_user_permissions_rejects_missing_user(gen_test_admin):

  with pytest.raises(UserNotFoundError):
    get_user_permissions(999)


def test_delete_user_permission(gen_test_admin):

  user_id = gen_test_admin

  permission_id = create_permission(
    name="inventory.read",
  )

  set_user_permission(
    user_id,
    permission_id,
    True,
  )

  assert (
    delete_user_permission(
      user_id,
      permission_id,
    )
    is True
  )

  assert (
    get_user_permission(
      user_id,
      permission_id,
    )
    is None
  )


def test_delete_user_permission_rejects_missing_permission_mapping(
  gen_test_admin,
):

  user_id = gen_test_admin

  permission_id = create_permission(
    name="inventory.read",
  )

  with pytest.raises(UserPermissionNotFoundError):
    delete_user_permission(
      user_id,
      permission_id,
    )


def test_set_user_permission_no_op_does_not_create_audit_log(
  gen_test_user,
):
  user_id = gen_test_user("test_user")

  permission_id = create_permission(
    name="inventory.read",
  )

  set_user_permission(
    user_id,
    permission_id,
    True,
  )

  audit_logs_before = get_audit_logs()

  set_user_permission(
    user_id,
    permission_id,
    True,
  )

  audit_logs_after = get_audit_logs()

  assert len(audit_logs_after) == len(audit_logs_before)


def test_set_user_permission_change_creates_audit_log(
  gen_test_user,
):
  user_id = gen_test_user("test_user")

  permission_id = create_permission(
    name="inventory.read",
  )

  set_user_permission(
    user_id,
    permission_id,
    True,
  )

  audit_logs_before = get_audit_logs()

  set_user_permission(
    user_id,
    permission_id,
    False,
  )

  audit_logs_after = get_audit_logs()

  assert len(audit_logs_after) == len(audit_logs_before) + 1

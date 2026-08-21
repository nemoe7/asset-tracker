import pytest

from app.services.data.audit import get_audit_logs
from app.services.data.permissions import (
  create_permission,
  delete_permission,
  get_permission,
  get_permission_by_name,
  get_permissions,
  update_permission,
)
from app.services.exceptions.data.common import InvalidInputError
from app.services.exceptions.data.permissions import *


def test_create_permission(gen_test_admin):
  permission_id = create_permission("inventory.view")

  assert permission_id is not None

  permission = get_permission(permission_id)

  assert permission["id"] == permission_id
  assert permission["name"] == "inventory.view"
  assert permission["description"] is None


def test_create_permission_with_description(gen_test_admin):
  permission_id = create_permission(
    "inventory.view",
    description="View inventory items",
  )

  permission = get_permission(permission_id)

  assert permission["name"] == "inventory.view"
  assert permission["description"] == "View inventory items"


def test_create_permission_with_empty_name_fails(gen_test_admin):
  with pytest.raises(InvalidPermissionNameError):
    create_permission("")


def test_create_permission_with_whitespace_name_fails(gen_test_admin):
  with pytest.raises(InvalidPermissionNameError):
    create_permission("   ")


def test_create_permission_with_non_string_name_fails(gen_test_admin):
  with pytest.raises(InvalidPermissionNameError):
    create_permission(None)


def test_create_duplicate_permission_fails(gen_test_admin):
  create_permission("inventory.view")

  with pytest.raises(PermissionAlreadyExistsError):
    create_permission("inventory.view")


def test_get_permission(gen_test_admin):
  permission_id = create_permission("inventory.view")

  permission = get_permission(permission_id)

  assert permission["id"] == permission_id
  assert permission["name"] == "inventory.view"


def test_get_permission_by_name(gen_test_admin):
  permission_id = create_permission("inventory.view")

  permission = get_permission_by_name("inventory.view")

  assert permission["id"] == permission_id


def test_get_nonexistent_permission(gen_test_admin):
  assert get_permission(999) is None


def test_get_permissions(gen_test_admin):
  first_id = create_permission("inventory.view")
  second_id = create_permission("inventory.edit")

  permissions = get_permissions()

  assert len(permissions) == 3  # 1 default + 2 created
  assert permissions[1]["id"] == second_id
  assert permissions[2]["id"] == first_id


def test_update_permission_name(gen_test_admin):
  permission_id = create_permission("inventory.view")

  assert (
    update_permission(
      permission_id,
      name="inventory.read",
    )
    is True
  )

  permission = get_permission(permission_id)

  assert permission["name"] == "inventory.read"


def test_update_permission_description(gen_test_admin):
  permission_id = create_permission("inventory.view")

  assert (
    update_permission(
      permission_id,
      description="View inventory items",
    )
    is True
  )

  permission = get_permission(permission_id)

  assert permission["description"] == "View inventory items"


def test_update_permission_name_and_description(gen_test_admin):
  permission_id = create_permission("inventory.view")

  assert (
    update_permission(
      permission_id,
      name="inventory.read",
      description="Read inventory items",
    )
    is True
  )

  permission = get_permission(permission_id)

  assert permission["name"] == "inventory.read"
  assert permission["description"] == "Read inventory items"


def test_update_permission_with_same_name_creates_no_audit_log(
  gen_test_admin,
):
  permission_id = create_permission("inventory.view")

  assert (
    update_permission(
      permission_id,
      name="inventory.view",
    )
    is True
  )

  logs = get_audit_logs(
    entity_type="permission",
    entity_id=permission_id,
  )

  assert len(logs) == 1
  assert logs[0]["action"] == "created"


def test_update_permission_with_same_description_creates_no_audit_log(
  gen_test_admin,
):
  permission_id = create_permission(
    "inventory.view",
    description="View inventory",
  )

  assert (
    update_permission(
      permission_id,
      description="View inventory",
    )
    is True
  )

  logs = get_audit_logs(
    entity_type="permission",
    entity_id=permission_id,
  )

  assert len(logs) == 1
  assert logs[0]["action"] == "created"


def test_update_permission_creates_audit_log(gen_test_admin):
  permission_id = create_permission("inventory.view")

  assert (
    update_permission(
      permission_id,
      name="inventory.read",
    )
    is True
  )

  logs = get_audit_logs(
    entity_type="permission",
    entity_id=permission_id,
  )

  assert len(logs) == 2
  assert logs[0]["action"] == "created"
  assert logs[1]["action"] == "updated"

  assert logs[1]["details"] == {
    "name": {
      "old": "inventory.view",
      "new": "inventory.read",
    },
  }


def test_update_permission_creates_audit_log_for_description_change(
  gen_test_admin,
):
  permission_id = create_permission(
    "inventory.view",
    description="View inventory",
  )

  assert (
    update_permission(
      permission_id,
      description="Read inventory",
    )
    is True
  )

  logs = get_audit_logs(
    entity_type="permission",
    entity_id=permission_id,
  )

  assert len(logs) == 2
  assert logs[0]["action"] == "created"
  assert logs[1]["action"] == "updated"

  assert logs[1]["details"] == {
    "description": {
      "old": "View inventory",
      "new": "Read inventory",
    },
  }


def test_update_permission_with_no_fields_fails(gen_test_admin):
  permission_id = create_permission("inventory.view")

  with pytest.raises(InvalidInputError):
    update_permission(permission_id)


def test_update_permission_with_empty_name_fails(gen_test_admin):
  permission_id = create_permission("inventory.view")

  with pytest.raises(InvalidPermissionNameError):
    update_permission(
      permission_id,
      name="",
    )


def test_update_permission_to_existing_name_fails(gen_test_admin):
  create_permission("inventory.view")
  permission_id = create_permission("inventory.edit")

  with pytest.raises(PermissionAlreadyExistsError):
    update_permission(
      permission_id,
      name="inventory.view",
    )


def test_update_nonexistent_permission_fails(gen_test_admin):
  with pytest.raises(PermissionNotFoundError):
    update_permission(
      999,
      name="inventory.view",
    )


def test_delete_permission(gen_test_admin):
  permission_id = create_permission("inventory.view")

  assert delete_permission(permission_id) is True
  assert get_permission(permission_id) is None


def test_delete_nonexistent_permission_fails(gen_test_admin):
  with pytest.raises(PermissionNotFoundError):
    delete_permission(999)


def test_delete_permission_creates_audit_log(gen_test_admin):
  permission_id = create_permission("inventory.view")

  assert delete_permission(permission_id) is True

  logs = get_audit_logs(
    entity_type="permission",
    entity_id=permission_id,
  )

  assert len(logs) == 2
  assert logs[0]["action"] == "created"
  assert logs[1]["action"] == "deleted"

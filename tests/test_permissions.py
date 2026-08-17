import pytest

from app.services.audit import get_audit_logs
from app.services.permissions import (
  create_permission,
  delete_permission,
  get_permission,
  get_permissions,
  update_permission,
)


def test_create_permission(test_db, authenticated_test_user):
  permission_id = create_permission(
    name="inventory.view",
    description="View inventory",
  )

  permission = get_permission(permission_id)

  assert permission["id"] == permission_id
  assert permission["name"] == "inventory.view"
  assert permission["description"] == "View inventory"


def test_create_permission_creates_audit_log(test_db, authenticated_test_user):
  permission_id = create_permission(
    name="inventory.view",
    description="View inventory",
  )

  logs = get_audit_logs(
    entity_type="permission",
    entity_id=permission_id,
  )

  assert len(logs) == 1
  assert logs[0]["user_id"] == 1
  assert logs[0]["action"] == "created"


def test_get_permission(test_db, authenticated_test_user):
  permission_id = create_permission(
    name="inventory.view",
    description="View inventory",
  )

  permission = get_permission(permission_id)

  assert permission is not None
  assert permission["id"] == permission_id


def test_get_nonexistent_permission(test_db):
  assert get_permission(999) is None


def test_get_permissions(test_db, authenticated_test_user):
  create_permission(
    name="inventory.view",
    description="View inventory",
  )

  create_permission(
    name="inventory.edit",
    description="Edit inventory",
  )

  permissions = get_permissions()

  assert len(permissions) == 2
  assert permissions[0]["name"] == "inventory.edit"
  assert permissions[1]["name"] == "inventory.view"


def test_update_permission(test_db, authenticated_test_user):
  permission_id = create_permission(
    name="inventory.view",
    description="View inventory",
  )

  assert (
    update_permission(
      permission_id,
      name="inventory.read",
      description="Read inventory",
    )
    is True
  )

  permission = get_permission(permission_id)

  assert permission["name"] == "inventory.read"
  assert permission["description"] == "Read inventory"


def test_update_permission_name_only(test_db, authenticated_test_user):
  permission_id = create_permission(
    name="inventory.view",
    description="View inventory",
  )

  assert (
    update_permission(
      permission_id,
      name="inventory.read",
    )
    is True
  )

  permission = get_permission(permission_id)

  assert permission["name"] == "inventory.read"
  assert permission["description"] == "View inventory"


def test_update_permission_description_only(test_db, authenticated_test_user):
  permission_id = create_permission(
    name="inventory.view",
    description="View inventory",
  )

  assert (
    update_permission(
      permission_id,
      description="Read inventory",
    )
    is True
  )

  permission = get_permission(permission_id)

  assert permission["name"] == "inventory.view"
  assert permission["description"] == "Read inventory"


def test_update_permission_creates_audit_log(test_db, authenticated_test_user):
  permission_id = create_permission(
    name="inventory.view",
    description="View inventory",
  )

  update_permission(
    permission_id,
    name="inventory.read",
  )

  logs = get_audit_logs(
    entity_type="permission",
    entity_id=permission_id,
  )

  assert len(logs) == 2
  assert logs[0]["action"] == "created"
  assert logs[1]["action"] == "updated"
  assert logs[1]["user_id"] == 1


def test_update_permission_without_changes_creates_no_audit_log(
  test_db, authenticated_test_user
):
  permission_id = create_permission(
    name="inventory.view",
    description="View inventory",
  )

  assert (
    update_permission(
      permission_id,
      name="inventory.view",
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


def test_update_nonexistent_permission(test_db):
  assert (
    update_permission(
      999,
      name="inventory.view",
    )
    is False
  )


def test_update_permission_with_no_fields_fails(test_db, authenticated_test_user):
  permission_id = create_permission(
    name="inventory.view",
    description="View inventory",
  )

  with pytest.raises(
    ValueError,
    match="No fields to update",
  ):
    update_permission(permission_id)


def test_delete_permission(test_db, authenticated_test_user):
  permission_id = create_permission(
    name="inventory.view",
    description="View inventory",
  )

  assert delete_permission(permission_id) is True
  assert get_permission(permission_id) is None


def test_delete_permission_creates_audit_log(test_db, authenticated_test_user):
  permission_id = create_permission(
    name="inventory.view",
    description="View inventory",
  )

  assert delete_permission(permission_id) is True

  logs = get_audit_logs(
    entity_type="permission",
    entity_id=permission_id,
  )

  assert len(logs) == 2
  assert logs[0]["action"] == "created"
  assert logs[1]["action"] == "deleted"
  assert logs[1]["user_id"] == 1


def test_delete_nonexistent_permission(test_db):
  assert delete_permission(999) is False


def test_create_permission_with_empty_name_fails(test_db):
  with pytest.raises(ValueError):
    create_permission(
      name="",
      description="View inventory",
    )


def test_create_permission_with_whitespace_name_fails(test_db):
  with pytest.raises(ValueError):
    create_permission(
      name="   ",
      description="View inventory",
    )


def test_create_duplicate_permission_fails(test_db, authenticated_test_user):
  create_permission(
    name="inventory.view",
    description="View inventory",
  )

  with pytest.raises(
    ValueError,
    match="Permission already exists",
  ):
    create_permission(
      name="inventory.view",
      description="Another description",
    )

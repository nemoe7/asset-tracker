import pytest

from app.services.audit import get_audit_logs
from app.services.roles import (
  create_role,
  delete_role,
  get_role,
  get_roles,
  update_role,
)


def test_create_role(test_db, authenticated_test_user):
  role_id = create_role(
    name="Admin",
    description="Administrator",
  )

  role = get_role(role_id)

  assert role["id"] == role_id
  assert role["name"] == "Admin"
  assert role["description"] == "Administrator"


def test_create_role_creates_audit_log(test_db, authenticated_test_user):
  role_id = create_role(
    name="Admin",
    description="Administrator",
  )

  logs = get_audit_logs(
    entity_type="role",
    entity_id=role_id,
  )

  assert len(logs) == 1
  assert logs[0]["user_id"] == 1
  assert logs[0]["action"] == "created"


def test_get_role(test_db, authenticated_test_user):
  role_id = create_role(
    name="Admin",
    description="Administrator",
  )

  role = get_role(role_id)

  assert role is not None
  assert role["id"] == role_id


def test_get_nonexistent_role(test_db):
  assert get_role(999) is None


def test_get_roles(test_db, authenticated_test_user):
  create_role(
    name="Admin",
    description="Administrator",
  )

  create_role(
    name="Checker",
    description="Inventory checker",
  )

  roles = get_roles()

  assert len(roles) == 2
  assert roles[0]["name"] == "Admin"
  assert roles[1]["name"] == "Checker"


def test_update_role(test_db, authenticated_test_user):
  role_id = create_role(
    name="Admin",
    description="Administrator",
  )

  assert (
    update_role(
      role_id,
      name="Super Admin",
      description="Full administrator",
    )
    is True
  )

  role = get_role(role_id)

  assert role["name"] == "Super Admin"
  assert role["description"] == "Full administrator"


def test_update_role_name_only(test_db, authenticated_test_user):
  role_id = create_role(
    name="Admin",
    description="Administrator",
  )

  assert (
    update_role(
      role_id,
      name="Super Admin",
    )
    is True
  )

  role = get_role(role_id)

  assert role["name"] == "Super Admin"
  assert role["description"] == "Administrator"


def test_update_role_description_only(test_db, authenticated_test_user):
  role_id = create_role(
    name="Admin",
    description="Administrator",
  )

  assert (
    update_role(
      role_id,
      description="Full administrator",
    )
    is True
  )

  role = get_role(role_id)

  assert role["name"] == "Admin"
  assert role["description"] == "Full administrator"


def test_update_role_creates_audit_log(test_db, authenticated_test_user):
  role_id = create_role(
    name="Admin",
    description="Administrator",
  )

  update_role(
    role_id,
    name="Super Admin",
  )

  logs = get_audit_logs(
    entity_type="role",
    entity_id=role_id,
  )

  assert len(logs) == 2
  assert logs[0]["action"] == "created"
  assert logs[1]["action"] == "updated"
  assert logs[1]["user_id"] == 1


def test_update_role_without_changes_creates_no_audit_log(
  test_db, authenticated_test_user
):
  role_id = create_role(
    name="Admin",
    description="Administrator",
  )

  assert (
    update_role(
      role_id,
      name="Admin",
      description="Administrator",
    )
    is True
  )

  logs = get_audit_logs(
    entity_type="role",
    entity_id=role_id,
  )

  assert len(logs) == 1
  assert logs[0]["action"] == "created"


def test_update_nonexistent_role(test_db):
  assert (
    update_role(
      999,
      name="Admin",
    )
    is False
  )


def test_update_role_with_no_fields_fails(test_db, authenticated_test_user):
  role_id = create_role(
    name="Admin",
    description="Administrator",
  )

  with pytest.raises(
    ValueError,
    match="No fields to update",
  ):
    update_role(role_id)


def test_delete_role(test_db, authenticated_test_user):
  role_id = create_role(
    name="Admin",
    description="Administrator",
  )

  assert delete_role(role_id) is True
  assert get_role(role_id) is None


def test_delete_role_creates_audit_log(test_db, authenticated_test_user):
  role_id = create_role(
    name="Admin",
    description="Administrator",
  )

  assert delete_role(role_id) is True

  logs = get_audit_logs(
    entity_type="role",
    entity_id=role_id,
  )

  assert len(logs) == 2
  assert logs[0]["action"] == "created"
  assert logs[1]["action"] == "deleted"
  assert logs[1]["user_id"] == 1


def test_delete_nonexistent_role(test_db):
  assert delete_role(999) is False


def test_create_role_with_empty_name_fails(test_db):
  with pytest.raises(ValueError):
    create_role(
      name="",
      description="Administrator",
    )


def test_create_role_with_whitespace_name_fails(test_db):
  with pytest.raises(ValueError):
    create_role(
      name="   ",
      description="Administrator",
    )


def test_create_duplicate_role_fails(test_db, authenticated_test_user):
  create_role(
    name="Admin",
    description="Administrator",
  )

  with pytest.raises(
    ValueError,
    match="Role already exists",
  ):
    create_role(
      name="Admin",
      description="Another description",
    )

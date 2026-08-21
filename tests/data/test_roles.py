import pytest

from app.services.data.audit import get_audit_logs
from app.services.data.roles import (
  create_role,
  delete_role,
  get_role,
  get_roles,
  update_role,
)
from app.services.exceptions.data.common import InvalidInputError
from app.services.exceptions.data.roles import *


def test_create_role(gen_test_admin):
  role_id = create_role(
    name="Admin2",
    description="Administrator",
  )

  role = get_role(role_id)

  assert role["id"] == role_id
  assert role["name"] == "Admin2"
  assert role["description"] == "Administrator"


def test_create_role_creates_audit_log(gen_test_admin):
  role_id = create_role(
    name="Admin2",
    description="Administrator",
  )

  logs = get_audit_logs(
    entity_type="role",
    entity_id=role_id,
  )

  assert len(logs) == 1
  assert logs[0]["user_id"] == gen_test_admin
  assert logs[0]["action"] == "created"


def test_get_role(gen_test_admin):
  role_id = create_role(
    name="Admin2",
    description="Administrator",
  )

  role = get_role(role_id)

  assert role is not None
  assert role["id"] == role_id


def test_get_nonexistent_role(gen_test_admin):
  assert get_role(999) is None


def test_get_roles(gen_test_admin):
  create_role(
    name="Admin2",
    description="Administrator",
  )

  create_role(
    name="Checker",
    description="Inventory checker",
  )

  roles = get_roles()

  assert len(roles) == 3
  assert roles[1]["name"] == "Admin2"
  assert roles[2]["name"] == "Checker"


def test_update_role(gen_test_admin):
  role_id = create_role(
    name="Admin2",
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


def test_update_role_name_only(gen_test_admin):
  role_id = create_role(
    name="Admin2",
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


def test_update_role_description_only(gen_test_admin):
  role_id = create_role(
    name="Admin2",
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

  assert role["name"] == "Admin2"
  assert role["description"] == "Full administrator"


def test_update_role_creates_audit_log(gen_test_admin):
  role_id = create_role(
    name="Admin2",
    description="Administrator",
  )

  assert (
    update_role(
      role_id,
      name="Super Admin",
    )
    is True
  )

  logs = get_audit_logs(
    entity_type="role",
    entity_id=role_id,
  )

  assert len(logs) == 2
  assert logs[0]["action"] == "created"
  assert logs[1]["action"] == "updated"
  assert logs[1]["user_id"] == gen_test_admin


def test_update_role_without_changes_creates_no_audit_log(
  gen_test_admin,
):
  role_id = create_role(
    name="Admin2",
    description="Administrator",
  )

  assert (
    update_role(
      role_id,
      name="Admin2",
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


def test_update_nonexistent_role(gen_test_admin):
  with pytest.raises(RoleNotFoundError):
    update_role(
      999,
      name="Admin2",
    )


def test_update_role_with_no_fields_fails(gen_test_admin):
  role_id = create_role(
    name="Admin2",
    description="Administrator",
  )

  with pytest.raises(InvalidInputError):
    update_role(role_id)


def test_delete_role(gen_test_admin):
  role_id = create_role(
    name="Admin2",
    description="Administrator",
  )

  assert delete_role(role_id) is True
  assert get_role(role_id) is None


def test_delete_role_creates_audit_log(gen_test_admin):
  role_id = create_role(
    name="Admin2",
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
  assert logs[1]["user_id"] == gen_test_admin


def test_delete_nonexistent_role(gen_test_admin):
  with pytest.raises(RoleNotFoundError):
    delete_role(999)


def test_create_role_with_empty_name_fails(gen_test_admin):
  with pytest.raises(InvalidRoleNameError):
    create_role(
      name="",
      description="Administrator",
    )


def test_create_role_with_whitespace_name_fails(gen_test_admin):
  with pytest.raises(InvalidRoleNameError):
    create_role(
      name="   ",
      description="Administrator",
    )


def test_create_duplicate_role_fails(gen_test_admin):
  create_role(
    name="Admin2",
    description="Administrator",
  )

  with pytest.raises(RoleAlreadyExistsError):
    create_role(
      name="Admin2",
      description="Another description",
    )

import pytest
from app.services.roles import (
  create_role,
  delete_role,
  get_role,
  get_roles,
  update_role,
)


def test_create_role(test_db):
  role_id = create_role(
    name="Admin",
    description="Administrator",
  )

  assert role_id is not None

  role = get_role(role_id)

  assert role["id"] == role_id
  assert role["name"] == "Admin"
  assert role["description"] == "Administrator"


def test_get_role(test_db):
  role_id = create_role(
    name="Admin",
    description="Administrator",
  )

  role = get_role(role_id)

  assert role["id"] == role_id
  assert role["name"] == "Admin"
  assert role["description"] == "Administrator"


def test_get_roles(test_db):
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


def test_update_role(test_db):
  role_id = create_role(
    name="Admin",
    description="Administrator",
  )

  updated = update_role(
    role_id,
    name="Super Admin",
    description="Full administrator",
  )

  assert updated is True

  role = get_role(role_id)

  assert role["name"] == "Super Admin"
  assert role["description"] == "Full administrator"


def test_update_role_name_only(test_db):
  role_id = create_role(
    name="Admin",
    description="Administrator",
  )

  updated = update_role(
    role_id,
    name="Super Admin",
  )

  assert updated is True

  role = get_role(role_id)

  assert role["name"] == "Super Admin"
  assert role["description"] == "Administrator"


def test_update_role_description_only(test_db):
  role_id = create_role(
    name="Admin",
    description="Administrator",
  )

  updated = update_role(
    role_id,
    description="Full administrator",
  )

  assert updated is True

  role = get_role(role_id)

  assert role["name"] == "Admin"
  assert role["description"] == "Full administrator"


def test_delete_role(test_db):
  role_id = create_role(
    name="Admin",
    description="Administrator",
  )

  assert delete_role(role_id) is True
  assert get_role(role_id) is None


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


def test_create_duplicate_role_fails(test_db):
  create_role(
    name="Admin",
    description="Administrator",
  )

  with pytest.raises(ValueError, match="Role already exists"):
    create_role(
      name="Admin",
      description="Another description",
    )


def test_get_nonexistent_role(test_db):
  assert get_role(999) is None


def test_update_nonexistent_role(test_db):
  assert (
    update_role(
      999,
      name="Admin",
    )
    is False
  )


def test_update_role_with_no_fields_fails(test_db):
  role_id = create_role(
    name="Admin",
    description="Administrator",
  )

  with pytest.raises(ValueError, match="No fields to update"):
    update_role(role_id)

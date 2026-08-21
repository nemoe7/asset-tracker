import pytest

from app.services.data.roles import create_role
from app.services.data.user_roles import (
  delete_user_role,
  get_user_role,
  get_user_roles,
  set_user_role,
)
from app.services.exceptions.data.roles import RoleNotFoundError
from app.services.exceptions.data.user_roles import UserRoleNotFoundError
from app.services.exceptions.data.users import UserNotFoundError


def test_set_user_role(gen_test_admin):
  role_id = create_role(name="Checker")

  user_id = gen_test_admin

  assert set_user_role(user_id, role_id) is True

  role = get_user_role(user_id, role_id)

  assert role["user_id"] == user_id
  assert role["role_id"] == role_id


def test_set_user_role_is_idempotent(gen_test_admin):
  role_id = create_role(name="Checker")

  user_id = gen_test_admin

  assert set_user_role(user_id, role_id) is True

  assert set_user_role(user_id, role_id) is True

  roles = get_user_roles(user_id)

  assert len(roles) == 1


def test_set_user_role_rejects_missing_user(gen_test_admin):
  role_id = create_role(name="Checker")

  with pytest.raises(UserNotFoundError):
    set_user_role(999, role_id)


def test_set_user_role_rejects_missing_role(gen_test_admin):
  user_id = gen_test_admin

  with pytest.raises(RoleNotFoundError):
    set_user_role(user_id, 999)


def test_get_user_role_returns_none_when_missing(gen_test_admin):
  role_id = create_role(name="Checker")

  user_id = gen_test_admin

  assert get_user_role(user_id, role_id) is None


def test_get_user_roles(gen_test_admin):
  first_role_id = create_role(name="Checker")

  second_role_id = create_role(name="Manager")

  user_id = gen_test_admin

  set_user_role(user_id, first_role_id)

  set_user_role(user_id, second_role_id)

  roles = get_user_roles(user_id)

  assert len(roles) == 2

  assert roles[0]["user_id"] == user_id
  assert roles[0]["role_id"] == first_role_id
  assert roles[0]["role"] == "Checker"

  assert roles[1]["user_id"] == user_id
  assert roles[1]["role_id"] == second_role_id
  assert roles[1]["role"] == "Manager"


def test_get_user_roles_returns_empty_list(gen_test_admin):
  user_id = gen_test_admin

  assert get_user_roles(user_id) == []


def test_get_user_roles_rejects_missing_user(gen_test_admin):
  with pytest.raises(UserNotFoundError):
    get_user_roles(999)


def test_delete_user_role(gen_test_admin):
  role_id = create_role(name="Checker")

  user_id = gen_test_admin

  set_user_role(user_id, role_id)

  assert delete_user_role(user_id, role_id) is True

  assert get_user_role(user_id, role_id) is None


def test_delete_user_role_rejects_missing_mapping(gen_test_admin):
  role_id = create_role(name="Checker")

  user_id = gen_test_admin

  with pytest.raises(UserRoleNotFoundError):
    delete_user_role(user_id, role_id)

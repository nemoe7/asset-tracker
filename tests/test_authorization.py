from app.services.authorization import has_permission

from app.services.permissions import create_permission
from app.services.role_permissions import assign_permission_to_role
from app.services.roles import create_role
from app.services.user_permissions import (
  assign_permission_to_user,
)
from app.services.user_roles import assign_role_to_user
from app.services.users import archive_user, create_user


def test_user_without_permission_is_denied(test_db):
  create_permission(
    name="inventory.view",
  )

  assert (
    has_permission(
      1,
      "inventory.view",
    )
    is False
  )


def test_user_with_direct_permission_is_allowed(test_db):
  permission_id = create_permission(
    name="inventory.view",
  )

  assign_permission_to_user(
    1,
    permission_id,
  )

  assert (
    has_permission(
      1,
      "inventory.view",
    )
    is True
  )


def test_user_with_role_permission_is_allowed(test_db):
  permission_id = create_permission(
    name="inventory.view",
  )

  role_id = create_role(
    name="admin",
  )

  assign_permission_to_role(
    role_id,
    permission_id,
  )

  assign_role_to_user(
    1,
    role_id,
  )

  assert (
    has_permission(
      1,
      "inventory.view",
    )
    is True
  )


def test_user_with_unrelated_permission_is_denied(test_db):
  view_permission_id = create_permission(
    name="inventory.view",
  )

  create_permission(
    name="inventory.edit",
  )

  assign_permission_to_user(
    1,
    view_permission_id,
  )

  assert (
    has_permission(
      1,
      "inventory.edit",
    )
    is False
  )


def test_direct_allow_overrides_role_permission(test_db):
  permission_id = create_permission(
    name="inventory.view",
  )

  role_id = create_role(
    name="viewer",
  )

  assign_permission_to_role(
    role_id,
    permission_id,
  )

  assign_role_to_user(
    1,
    role_id,
  )

  assign_permission_to_user(
    1,
    permission_id,
  )

  assert (
    has_permission(
      1,
      "inventory.view",
    )
    is True
  )


def test_direct_deny_overrides_role_permission(test_db):
  permission_id = create_permission(
    name="inventory.view",
  )

  role_id = create_role(
    name="viewer",
  )

  assign_permission_to_role(
    role_id,
    permission_id,
  )

  assign_role_to_user(
    1,
    role_id,
  )

  assign_permission_to_user(
    1,
    permission_id,
    allowed=False,
  )

  assert (
    has_permission(
      1,
      "inventory.view",
    )
    is False
  )


def test_direct_deny_without_role_permission_is_denied(test_db):
  permission_id = create_permission(
    name="inventory.view",
  )

  assign_permission_to_user(
    1,
    permission_id,
    allowed=False,
  )

  assert (
    has_permission(
      1,
      "inventory.view",
    )
    is False
  )


def test_nonexistent_user_is_denied(test_db):
  create_permission(
    name="inventory.view",
  )

  assert (
    has_permission(
      999,
      "inventory.view",
    )
    is False
  )


def test_nonexistent_permission_is_denied(test_db):
  assert (
    has_permission(
      1,
      "inventory.view",
    )
    is False
  )


def test_archived_user_is_denied(test_db):
  permission_id = create_permission(
    name="inventory.view",
  )

  assign_permission_to_user(
    1,
    permission_id,
  )

  assert archive_user(1) is True

  assert (
    has_permission(
      1,
      "inventory.view",
    )
    is False
  )


def test_permission_check_does_not_depend_on_current_user(
  test_db,
):
  permission_id = create_permission(
    name="inventory.view",
  )

  second_user_id = create_user(
    username="second_user",
    password="password",
  )

  assign_permission_to_user(
    second_user_id,
    permission_id,
  )

  assert (
    has_permission(
      second_user_id,
      "inventory.view",
    )
    is True
  )

  assert (
    has_permission(
      1,
      "inventory.view",
    )
    is False
  )


def test_permission_granted_by_any_assigned_role(test_db):
  permission_id = create_permission(
    name="inventory.view",
  )

  first_role_id = create_role(
    name="viewer",
  )

  second_role_id = create_role(
    name="admin",
  )

  assign_role_to_user(
    1,
    first_role_id,
  )

  assign_role_to_user(
    1,
    second_role_id,
  )

  assign_permission_to_role(
    second_role_id,
    permission_id,
  )

  assert (
    has_permission(
      1,
      "inventory.view",
    )
    is True
  )

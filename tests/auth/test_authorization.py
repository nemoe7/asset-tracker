import pytest
from flask import Flask, session
from werkzeug.exceptions import Forbidden

from app.services.auth.authorization import (
  check_permission,
  permission_required,
  require_permission,
)
from app.services.data.permissions import (
  create_permission,
  get_permission_by_name,
)
from app.services.data.user_permissions import (
  set_user_permission,
)
from app.services.data.users import archive_user
from app.services.exceptions.auth.orization import (
  PermissionDeniedError,
)


def test_read_permission_defaults_to_allow(
  gen_test_data_admin,
):
  create_permission(name="inventory.read")

  assert (
    check_permission(
      gen_test_data_admin,
      "inventory.read",
    )
    is True
  )


def test_non_read_permission_defaults_to_deny(
  gen_test_data_admin,
):
  create_permission(name="inventory.create")

  assert (
    check_permission(
      gen_test_data_admin,
      "inventory.create",
    )
    is False
  )


def test_explicit_allow_allows_permission(
  gen_test_data_admin,
):
  permission_id = create_permission(
    name="inventory.create",
  )

  set_user_permission(
    gen_test_data_admin,
    permission_id,
    True,
  )

  assert (
    check_permission(
      gen_test_data_admin,
      "inventory.create",
    )
    is True
  )


def test_explicit_deny_denies_permission(
  gen_test_data_admin,
):
  permission_id = create_permission(
    name="inventory.read",
  )

  set_user_permission(
    gen_test_data_admin,
    permission_id,
    False,
  )

  assert (
    check_permission(
      gen_test_data_admin,
      "inventory.read",
    )
    is False
  )


def test_namespace_wildcard_permission_allows_operations(
  gen_test_data_admin,
):
  permission_id = create_permission(
    name="inventory.*",
  )

  set_user_permission(
    gen_test_data_admin,
    permission_id,
    True,
  )

  create_permission(name="inventory.create")
  create_permission(name="inventory.update")

  assert (
    check_permission(
      gen_test_data_admin,
      "inventory.create",
    )
    is True
  )

  assert (
    check_permission(
      gen_test_data_admin,
      "inventory.update",
    )
    is True
  )


def test_global_wildcard_permission_allows_any_permission(
  gen_test_data_admin,
):
  permission_id = get_permission_by_name(name="*")["id"]

  set_user_permission(
    gen_test_data_admin,
    permission_id,
    True,
  )

  create_permission(name="inventory.create")
  create_permission(name="users.delete")

  assert (
    check_permission(
      gen_test_data_admin,
      "inventory.create",
    )
    is True
  )

  assert (
    check_permission(
      gen_test_data_admin,
      "users.delete",
    )
    is True
  )


def test_exact_permission_takes_precedence_over_namespace_wildcard(
  gen_test_data_admin,
):
  wildcard_id = create_permission(
    name="inventory.*",
  )
  exact_id = create_permission(
    name="inventory.delete",
  )

  set_user_permission(
    gen_test_data_admin,
    wildcard_id,
    True,
  )

  set_user_permission(
    gen_test_data_admin,
    exact_id,
    False,
  )

  assert (
    check_permission(
      gen_test_data_admin,
      "inventory.delete",
    )
    is False
  )


def test_namespace_wildcard_takes_precedence_over_global_wildcard(
  gen_test_data_admin,
):
  global_id = get_permission_by_name(name="*")["id"]
  wildcard_id = create_permission(
    name="inventory.*",
  )

  set_user_permission(
    gen_test_data_admin,
    global_id,
    False,
  )

  set_user_permission(
    gen_test_data_admin,
    wildcard_id,
    True,
  )

  create_permission(name="inventory.create")

  assert (
    check_permission(
      gen_test_data_admin,
      "inventory.create",
    )
    is True
  )


def test_direct_deny_overrides_namespace_wildcard(
  gen_test_data_admin,
):
  wildcard_id = create_permission(
    name="inventory.*",
  )
  exact_id = create_permission(
    name="inventory.delete",
  )

  set_user_permission(
    gen_test_data_admin,
    wildcard_id,
    True,
  )

  set_user_permission(
    gen_test_data_admin,
    exact_id,
    False,
  )

  assert (
    check_permission(
      gen_test_data_admin,
      "inventory.delete",
    )
    is False
  )


def test_nested_namespace_wildcard(
  gen_test_data_admin,
):
  wildcard_id = create_permission(
    name="field.12.*",
  )

  set_user_permission(
    gen_test_data_admin,
    wildcard_id,
    True,
  )

  create_permission(name="field.12.read")
  create_permission(name="field.12.update")
  create_permission(name="field.13.read")

  assert (
    check_permission(
      gen_test_data_admin,
      "field.12.read",
    )
    is True
  )

  assert (
    check_permission(
      gen_test_data_admin,
      "field.12.update",
    )
    is True
  )

  assert (
    check_permission(
      gen_test_data_admin,
      "field.13.read",
    )
    is True
  )


def test_archived_user_is_denied(
  gen_test_data_user,
):
  user_id = gen_test_data_user("alice")
  archive_user(user_id)

  create_permission(name="inventory.read")

  assert (
    check_permission(
      user_id,
      "inventory.read",
    )
    is False
  )


def test_unknown_user_is_denied(gen_test_data_admin):
  create_permission(name="inventory.read")

  assert (
    check_permission(
      999999,
      "inventory.read",
    )
    is False
  )


def test_require_permission_allows_authorized_user(
  gen_test_data_admin,
):
  create_permission(name="inventory.read")

  require_permission(
    gen_test_data_admin,
    "inventory.read",
  )


def test_require_permission_raises_when_denied(
  gen_test_data_admin,
):
  create_permission(name="inventory.create")

  with pytest.raises(PermissionDeniedError):
    require_permission(
      gen_test_data_admin,
      "inventory.create",
    )


def test_require_permission_raises_for_explicit_deny(
  gen_test_data_admin,
):
  permission_id = create_permission(
    name="inventory.read",
  )

  set_user_permission(
    gen_test_data_admin,
    permission_id,
    False,
  )

  with pytest.raises(PermissionDeniedError):
    require_permission(
      gen_test_data_admin,
      "inventory.read",
    )


def test_unknown_read_permission_defaults_to_allow(
  gen_test_data_admin,
):
  assert (
    check_permission(
      gen_test_data_admin,
      "inventory.read",
    )
    is True
  )


def test_permission_required_allows_authorized_user(
  gen_test_data_admin,
):
  create_permission(name="inventory.read")

  app = Flask(__name__)
  app.secret_key = "test"

  @permission_required("inventory.read")
  def view():
    return "allowed"

  with app.test_request_context():
    session["user_id"] = gen_test_data_admin

    assert view() == "allowed"


def test_permission_required_denies_unauthorized_user(
  gen_test_data_admin,
):
  create_permission(name="inventory.create")

  app = Flask(__name__)
  app.secret_key = "test"

  @permission_required("inventory.create")
  def view():
    return "allowed"

  with app.test_request_context():
    session["user_id"] = gen_test_data_admin

    with pytest.raises(PermissionDeniedError):
      view()


def test_permission_required_denies_unauthenticated_user():
  app = Flask(__name__)
  app.secret_key = "test"

  @permission_required("inventory.read")
  def view():
    return "allowed"

  with app.test_request_context(), pytest.raises(Forbidden):
    view()

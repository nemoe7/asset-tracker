from app.services.auth.authorization import has_permission
from app.services.data.custom_fields import create_custom_field
from app.services.data.permissions import (
  create_permission,
  get_permission_by_name,
)
from app.services.data.role_permissions import set_role_permission
from app.services.data.roles import create_role
from app.services.data.user_permissions import set_user_permission
from app.services.data.user_roles import set_user_role
from app.services.data.users import archive_user


def test_user_without_permission_is_denied(gen_test_admin):
  create_permission(name="inventory.read")

  assert (
    has_permission(
      gen_test_admin,
      "inventory.read",
    )
    is False
  )


def test_user_with_direct_permission_is_allowed(gen_test_admin):
  permission_id = create_permission(name="inventory.read")

  set_user_permission(
    gen_test_admin,
    permission_id,
    True,
  )

  assert has_permission(gen_test_admin, "inventory.read") is True


def test_user_with_role_permission_is_allowed(gen_test_admin):
  permission_id = create_permission(name="inventory.read")

  role_id = create_role(name="admin")

  set_role_permission(role_id, permission_id, True)

  set_user_role(gen_test_admin, role_id)

  assert has_permission(gen_test_admin, "inventory.read") is True


def test_user_with_unrelated_permission_is_denied(gen_test_admin):
  view_permission_id = create_permission(name="inventory.read")

  create_permission(name="inventory.update")

  set_user_permission(gen_test_admin, view_permission_id, True)

  assert has_permission(gen_test_admin, "inventory.update") is False


def test_direct_allow_overrides_role_permission(gen_test_admin):
  permission_id = create_permission(name="inventory.read")

  role_id = create_role(name="viewer")

  set_role_permission(role_id, permission_id, True)

  set_user_role(gen_test_admin, role_id)

  set_user_permission(gen_test_admin, permission_id, True)

  assert has_permission(gen_test_admin, "inventory.read") is True


def test_direct_deny_overrides_role_permission(gen_test_admin):
  permission_id = create_permission(name="inventory.read")

  role_id = create_role(name="viewer")

  set_role_permission(role_id, permission_id, True)

  set_user_role(gen_test_admin, role_id)

  set_user_permission(gen_test_admin, permission_id, False)

  assert has_permission(gen_test_admin, "inventory.read") is False


def test_direct_deny_without_role_permission_is_denied(gen_test_admin):
  permission_id = create_permission(name="inventory.read")

  set_user_permission(gen_test_admin, permission_id, False)

  assert has_permission(gen_test_admin, "inventory.read") is False


def test_nonexistent_user_is_denied(gen_test_admin):
  create_permission(name="inventory.read")

  assert has_permission(999, "inventory.read") is False


def test_nonexistent_permission_is_denied(gen_test_admin):
  assert has_permission(gen_test_admin, "inventory.read") is False


def test_archived_user_is_denied(gen_test_admin):
  permission_id = create_permission(name="inventory.read")

  set_user_permission(gen_test_admin, permission_id, True)

  assert archive_user(gen_test_admin) is True

  assert has_permission(gen_test_admin, "inventory.read") is False


def test_permission_check_does_not_depend_on_current_user(
  gen_test_admin, gen_test_user
):
  permission_id = create_permission(name="inventory.read")

  second_user_id = gen_test_user("second_user")

  set_user_permission(second_user_id, permission_id, True)

  assert has_permission(second_user_id, "inventory.read") is True

  assert has_permission(gen_test_admin, "inventory.read") is False


def test_permission_granted_by_any_assigned_role(gen_test_admin):
  permission_id = create_permission(name="inventory.read")

  first_role_id = create_role(name="viewer")

  second_role_id = create_role(name="admin")

  set_user_role(gen_test_admin, first_role_id)

  set_user_role(gen_test_admin, second_role_id)

  set_role_permission(second_role_id, permission_id, True)

  assert has_permission(gen_test_admin, "inventory.read") is True


def test_inventory_crud_permissions_are_independent(gen_test_admin):
  permission_names = [
    "inventory.create",
    "inventory.read",
    "inventory.update",
    "inventory.delete",
  ]

  permission_ids = {name: create_permission(name=name) for name in permission_names}

  set_user_permission(gen_test_admin, permission_ids["inventory.read"], True)

  assert has_permission(gen_test_admin, "inventory.read") is True

  assert has_permission(gen_test_admin, "inventory.create") is False

  assert has_permission(gen_test_admin, "inventory.update") is False

  assert has_permission(gen_test_admin, "inventory.delete") is False


def test_inventory_import_permission_is_independent(gen_test_admin):
  create_permission(name="inventory.read")

  import_permission_id = create_permission(name="inventory.import")

  set_user_permission(gen_test_admin, import_permission_id, True)

  assert has_permission(gen_test_admin, "inventory.import") is True

  assert has_permission(gen_test_admin, "inventory.export") is False


def test_inventory_export_permission_is_independent(gen_test_admin):
  create_permission(name="inventory.read")

  export_permission_id = create_permission(name="inventory.export")

  set_user_permission(gen_test_admin, export_permission_id, True)

  assert has_permission(gen_test_admin, "inventory.export") is True

  assert has_permission(gen_test_admin, "inventory.import") is False


def test_audit_read_permission_is_independent(gen_test_admin):
  audit_permission_id = create_permission(name="audit.read")

  set_user_permission(gen_test_admin, audit_permission_id, True)

  assert has_permission(gen_test_admin, "audit.read") is True

  assert has_permission(gen_test_admin, "inventory.read") is False


def test_backup_permissions_are_independent(gen_test_admin):
  create_permission(name="backup.create")

  restore_permission_id = create_permission(name="backup.restore")

  set_user_permission(gen_test_admin, restore_permission_id, True)

  assert has_permission(gen_test_admin, "backup.restore") is True

  assert has_permission(gen_test_admin, "backup.create") is False


def test_field_read_permission_is_allowed(gen_test_admin):
  field_id = create_custom_field(name="Purchase Price", field_type="decimal")

  permission_id = create_permission(name=f"field.{field_id}.read")

  set_user_permission(gen_test_admin, permission_id, True)

  assert has_permission(gen_test_admin, f"field.{field_id}.read") is True


def test_field_update_permission_is_allowed(gen_test_admin):
  field_id = create_custom_field(name="Purchase Price", field_type="decimal")

  permission_id = create_permission(name=f"field.{field_id}.update")

  set_user_permission(gen_test_admin, permission_id, True)

  assert has_permission(gen_test_admin, f"field.{field_id}.update") is True


def test_field_read_and_update_permissions_are_independent(gen_test_admin):
  field_id = create_custom_field(name="Purchase Price", field_type="decimal")

  read_permission_id = create_permission(name=f"field.{field_id}.read")

  set_user_permission(gen_test_admin, read_permission_id, True)

  assert has_permission(gen_test_admin, f"field.{field_id}.read") is True

  assert has_permission(gen_test_admin, f"field.{field_id}.update") is False


def test_field_permission_can_be_granted_through_role(gen_test_admin):
  field_id = create_custom_field(name="Purchase Price", field_type="decimal")

  permission_id = create_permission(name=f"field.{field_id}.read")

  role_id = create_role(name="checker")

  set_role_permission(role_id, permission_id, True)

  set_user_role(gen_test_admin, role_id)

  assert has_permission(gen_test_admin, f"field.{field_id}.read") is True


def test_direct_field_deny_overrides_role_allow(gen_test_admin):
  field_id = create_custom_field(name="Purchase Price", field_type="decimal")

  permission_id = create_permission(name=f"field.{field_id}.read")

  role_id = create_role(name="checker")

  set_role_permission(role_id, permission_id, True)

  set_user_role(gen_test_admin, role_id)

  set_user_permission(gen_test_admin, permission_id, False)

  assert has_permission(gen_test_admin, f"field.{field_id}.read") is False


def test_namespace_wildcard_permission_allows_operations(gen_test_admin):
  permission_id = create_permission(name="inventory.*")

  set_user_permission(gen_test_admin, permission_id, True)

  assert has_permission(gen_test_admin, "inventory.read") is True

  assert has_permission(gen_test_admin, "inventory.update") is True


def test_namespace_wildcard_permission_does_not_allow_other_namespace(gen_test_admin):
  permission_id = create_permission(name="inventory.*")

  set_user_permission(gen_test_admin, permission_id, True)

  assert has_permission(gen_test_admin, "users.read") is False


def test_global_wildcard_permission_allows_any_permission(gen_test_admin):
  permission_id = get_permission_by_name("*")["id"]

  set_user_permission(gen_test_admin, permission_id, True)

  assert has_permission(gen_test_admin, "inventory.read") is True

  assert has_permission(gen_test_admin, "users.delete") is True


def test_direct_deny_overrides_namespace_wildcard(gen_test_admin):
  wildcard_permission_id = create_permission(name="inventory.*")

  read_permission_id = create_permission(name="inventory.read")

  role_id = create_role(name="inventory_admin")

  set_role_permission(role_id, wildcard_permission_id, True)

  set_user_role(gen_test_admin, role_id)

  set_user_permission(gen_test_admin, read_permission_id, False)

  assert has_permission(gen_test_admin, "inventory.read") is False

  assert has_permission(gen_test_admin, "inventory.update") is True


def test_wildcard_request_is_not_expanded(gen_test_admin):
  read_permission_id = create_permission(name="inventory.read")

  set_user_permission(gen_test_admin, read_permission_id, True)

  assert has_permission(gen_test_admin, "inventory.*") is False


def test_role_permission_deny_is_enforced(gen_test_admin):
  permission_id = create_permission(name="inventory.read")

  role_id = create_role(name="restricted")

  set_role_permission(role_id, permission_id, False)

  set_user_role(gen_test_admin, role_id)

  assert has_permission(gen_test_admin, "inventory.read") is False


def test_role_exact_allow_overrides_role_namespace_deny(gen_test_admin):
  namespace_permission_id = create_permission(name="inventory.*")

  exact_permission_id = create_permission(name="inventory.read")

  namespace_role_id = create_role(name="namespace")

  exact_role_id = create_role(name="exact")

  set_role_permission(namespace_role_id, namespace_permission_id, False)

  set_role_permission(exact_role_id, exact_permission_id, True)

  set_user_role(gen_test_admin, namespace_role_id)

  set_user_role(gen_test_admin, exact_role_id)

  assert has_permission(gen_test_admin, "inventory.read") is True


def test_role_exact_deny_overrides_role_namespace_allow(gen_test_admin):
  namespace_permission_id = create_permission(name="inventory.*")

  exact_permission_id = create_permission(name="inventory.read")

  namespace_role_id = create_role(name="namespace")

  exact_role_id = create_role(name="exact")

  set_role_permission(namespace_role_id, namespace_permission_id, True)

  set_role_permission(exact_role_id, exact_permission_id, False)

  set_user_role(gen_test_admin, namespace_role_id)

  set_user_role(gen_test_admin, exact_role_id)

  assert has_permission(gen_test_admin, "inventory.read") is False


def test_role_namespace_allow_overrides_role_global_deny(gen_test_admin):
  global_permission_id = get_permission_by_name("*")["id"]

  namespace_permission_id = create_permission(name="inventory.*")

  global_role_id = create_role(name="global")

  namespace_role_id = create_role(name="namespace")

  set_role_permission(global_role_id, global_permission_id, False)

  set_role_permission(namespace_role_id, namespace_permission_id, True)

  set_user_role(gen_test_admin, global_role_id)

  set_user_role(gen_test_admin, namespace_role_id)

  assert has_permission(gen_test_admin, "inventory.read") is True

  assert has_permission(gen_test_admin, "users.read") is False


def test_role_namespace_deny_overrides_role_global_allow(gen_test_admin):
  global_permission_id = get_permission_by_name("*")["id"]

  namespace_permission_id = create_permission(name="inventory.*")

  global_role_id = create_role(name="global")

  namespace_role_id = create_role(name="namespace")

  set_role_permission(global_role_id, global_permission_id, True)

  set_role_permission(namespace_role_id, namespace_permission_id, False)

  set_user_role(gen_test_admin, global_role_id)

  set_user_role(gen_test_admin, namespace_role_id)

  assert has_permission(gen_test_admin, "inventory.read") is False

  assert has_permission(gen_test_admin, "users.read") is True


def test_role_global_allow_applies_when_no_more_specific_match_exists(gen_test_admin):
  permission_id = get_permission_by_name("*")["id"]

  role_id = create_role(name="global")

  set_role_permission(role_id, permission_id, True)

  set_user_role(gen_test_admin, role_id)

  assert has_permission(gen_test_admin, "inventory.read") is True

  assert has_permission(gen_test_admin, "users.delete") is True


def test_role_global_deny_applies_when_no_more_specific_match_exists(gen_test_admin):
  permission_id = get_permission_by_name("*")["id"]

  role_id = create_role(name="restricted")

  set_role_permission(role_id, permission_id, False)

  set_user_role(gen_test_admin, role_id)

  assert has_permission(gen_test_admin, "inventory.read") is False

  assert has_permission(gen_test_admin, "users.delete") is False


def test_direct_exact_allow_overrides_role_namespace_deny(gen_test_admin):
  exact_permission_id = create_permission(name="inventory.read")

  namespace_permission_id = create_permission(name="inventory.*")

  role_id = create_role(name="restricted")

  set_role_permission(role_id, namespace_permission_id, False)

  set_user_role(gen_test_admin, role_id)

  set_user_permission(gen_test_admin, exact_permission_id, True)

  assert has_permission(gen_test_admin, "inventory.read") is True


def test_direct_namespace_allow_overrides_role_exact_deny(gen_test_admin):
  namespace_permission_id = create_permission(name="inventory.*")

  exact_permission_id = create_permission(name="inventory.read")

  role_id = create_role(name="restricted")

  set_role_permission(role_id, exact_permission_id, False)

  set_user_role(gen_test_admin, role_id)

  set_user_permission(gen_test_admin, namespace_permission_id, True)

  assert has_permission(gen_test_admin, "inventory.read") is True


def test_direct_global_allow_overrides_role_exact_deny(gen_test_admin):
  global_permission_id = get_permission_by_name("*")["id"]

  exact_permission_id = create_permission(name="inventory.read")

  role_id = create_role(name="restricted")

  set_role_permission(role_id, exact_permission_id, False)

  set_user_role(gen_test_admin, role_id)

  set_user_permission(gen_test_admin, global_permission_id, True)

  assert has_permission(gen_test_admin, "inventory.read") is True


def test_direct_global_deny_overrides_role_namespace_allow(gen_test_admin):
  global_permission_id = get_permission_by_name("*")["id"]

  namespace_permission_id = create_permission(name="inventory.*")

  role_id = create_role(name="inventory")

  set_role_permission(role_id, namespace_permission_id, True)

  set_user_role(gen_test_admin, role_id)

  set_user_permission(gen_test_admin, global_permission_id, False)

  assert has_permission(gen_test_admin, "inventory.read") is False


def test_direct_exact_is_more_specific_than_direct_namespace_and_global(gen_test_admin):
  global_permission_id = get_permission_by_name("*")["id"]

  namespace_permission_id = create_permission(name="inventory.*")

  exact_permission_id = create_permission(name="inventory.read")

  set_user_permission(gen_test_admin, global_permission_id, False)

  set_user_permission(gen_test_admin, namespace_permission_id, False)

  set_user_permission(gen_test_admin, exact_permission_id, True)

  assert has_permission(gen_test_admin, "inventory.read") is True


def test_direct_namespace_is_more_specific_than_direct_global(gen_test_admin):
  global_permission_id = get_permission_by_name("*")["id"]

  namespace_permission_id = create_permission(name="inventory.*")

  set_user_permission(gen_test_admin, global_permission_id, False)

  set_user_permission(gen_test_admin, namespace_permission_id, True)

  assert has_permission(gen_test_admin, "inventory.read") is True


def test_direct_permission_order_does_not_change_result(gen_test_admin):
  global_permission_id = get_permission_by_name("*")["id"]

  namespace_permission_id = create_permission(name="inventory.*")

  exact_permission_id = create_permission(name="inventory.read")

  set_user_permission(gen_test_admin, exact_permission_id, True)

  set_user_permission(gen_test_admin, global_permission_id, False)

  set_user_permission(gen_test_admin, namespace_permission_id, False)

  assert has_permission(gen_test_admin, "inventory.read") is True


def test_role_permission_order_does_not_change_result(gen_test_admin):
  global_permission_id = get_permission_by_name("*")["id"]

  namespace_permission_id = create_permission(name="inventory.*")

  exact_permission_id = create_permission(name="inventory.read")

  global_role_id = create_role(name="global")

  namespace_role_id = create_role(name="namespace")

  exact_role_id = create_role(name="exact")

  set_role_permission(global_role_id, global_permission_id, False)

  set_role_permission(namespace_role_id, namespace_permission_id, False)

  set_role_permission(exact_role_id, exact_permission_id, True)

  set_user_role(gen_test_admin, exact_role_id)

  set_user_role(gen_test_admin, global_role_id)

  set_user_role(gen_test_admin, namespace_role_id)

  assert has_permission(gen_test_admin, "inventory.read") is True


def test_direct_permission_overrides_all_role_permission_levels(gen_test_admin):
  global_permission_id = get_permission_by_name("*")["id"]

  namespace_permission_id = create_permission(name="inventory.*")

  exact_permission_id = create_permission(name="inventory.read")

  global_role_id = create_role(name="global")

  namespace_role_id = create_role(name="namespace")

  exact_role_id = create_role(name="exact")

  set_role_permission(global_role_id, global_permission_id, False)

  set_role_permission(namespace_role_id, namespace_permission_id, False)

  set_role_permission(exact_role_id, exact_permission_id, False)

  set_user_role(gen_test_admin, global_role_id)

  set_user_role(gen_test_admin, namespace_role_id)

  set_user_role(gen_test_admin, exact_role_id)

  set_user_permission(gen_test_admin, exact_permission_id, True)

  assert has_permission(gen_test_admin, "inventory.read") is True


def test_multiple_roles_same_permission_deny_wins(gen_test_admin):
  permission_id = create_permission(name="inventory.read")

  allow_role_id = create_role(name="allow")

  deny_role_id = create_role(name="deny")

  set_role_permission(allow_role_id, permission_id, True)

  set_role_permission(deny_role_id, permission_id, False)

  set_user_role(gen_test_admin, allow_role_id)

  set_user_role(gen_test_admin, deny_role_id)

  assert has_permission(gen_test_admin, "inventory.read") is False

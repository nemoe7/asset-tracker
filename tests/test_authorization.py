from app.services.authorization import has_permission
from app.services.custom_fields import create_custom_field
from app.services.permissions import create_permission
from app.services.role_permissions import assign_permission_to_role
from app.services.roles import create_role
from app.services.user_permissions import assign_permission_to_user
from app.services.user_roles import assign_role_to_user
from app.services.users import archive_user, create_user


def test_user_without_permission_is_denied(test_db, authenticated_test_user):
  create_permission(
    name="inventory.read",
  )

  assert (
    has_permission(
      1,
      "inventory.read",
    )
    is False
  )


def test_user_with_direct_permission_is_allowed(test_db, authenticated_test_user):
  permission_id = create_permission(
    name="inventory.read",
  )

  assign_permission_to_user(
    1,
    permission_id,
  )

  assert (
    has_permission(
      1,
      "inventory.read",
    )
    is True
  )


def test_user_with_role_permission_is_allowed(test_db, authenticated_test_user):
  permission_id = create_permission(
    name="inventory.read",
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
      "inventory.read",
    )
    is True
  )


def test_user_with_unrelated_permission_is_denied(test_db, authenticated_test_user):
  view_permission_id = create_permission(
    name="inventory.read",
  )

  create_permission(
    name="inventory.update",
  )

  assign_permission_to_user(
    1,
    view_permission_id,
  )

  assert (
    has_permission(
      1,
      "inventory.update",
    )
    is False
  )


def test_direct_allow_overrides_role_permission(test_db, authenticated_test_user):
  permission_id = create_permission(
    name="inventory.read",
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
      "inventory.read",
    )
    is True
  )


def test_direct_deny_overrides_role_permission(test_db, authenticated_test_user):
  permission_id = create_permission(
    name="inventory.read",
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
      "inventory.read",
    )
    is False
  )


def test_direct_deny_without_role_permission_is_denied(
  test_db, authenticated_test_user
):
  permission_id = create_permission(
    name="inventory.read",
  )

  assign_permission_to_user(
    1,
    permission_id,
    allowed=False,
  )

  assert (
    has_permission(
      1,
      "inventory.read",
    )
    is False
  )


def test_nonexistent_user_is_denied(test_db, authenticated_test_user):
  create_permission(
    name="inventory.read",
  )

  assert (
    has_permission(
      999,
      "inventory.read",
    )
    is False
  )


def test_nonexistent_permission_is_denied(test_db):
  assert (
    has_permission(
      1,
      "inventory.read",
    )
    is False
  )


def test_archived_user_is_denied(test_db, authenticated_test_user):
  permission_id = create_permission(
    name="inventory.read",
  )

  assign_permission_to_user(
    1,
    permission_id,
  )

  assert archive_user(1) is True

  assert (
    has_permission(
      1,
      "inventory.read",
    )
    is False
  )


def test_permission_check_does_not_depend_on_current_user(
  test_db, authenticated_test_user
):
  permission_id = create_permission(
    name="inventory.read",
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
      "inventory.read",
    )
    is True
  )

  assert (
    has_permission(
      1,
      "inventory.read",
    )
    is False
  )


def test_permission_granted_by_any_assigned_role(test_db, authenticated_test_user):
  permission_id = create_permission(
    name="inventory.read",
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
      "inventory.read",
    )
    is True
  )


def test_inventory_crud_permissions_are_independent(test_db, authenticated_test_user):
  permission_names = [
    "inventory.create",
    "inventory.read",
    "inventory.update",
    "inventory.delete",
  ]

  permission_ids = {name: create_permission(name=name) for name in permission_names}

  assign_permission_to_user(
    1,
    permission_ids["inventory.read"],
  )

  assert (
    has_permission(
      1,
      "inventory.read",
    )
    is True
  )

  assert (
    has_permission(
      1,
      "inventory.create",
    )
    is False
  )

  assert (
    has_permission(
      1,
      "inventory.update",
    )
    is False
  )

  assert (
    has_permission(
      1,
      "inventory.delete",
    )
    is False
  )


def test_inventory_import_permission_is_independent(test_db, authenticated_test_user):
  create_permission(
    name="inventory.read",
  )

  import_permission_id = create_permission(
    name="inventory.import",
  )

  assign_permission_to_user(
    1,
    import_permission_id,
  )

  assert (
    has_permission(
      1,
      "inventory.import",
    )
    is True
  )

  assert (
    has_permission(
      1,
      "inventory.export",
    )
    is False
  )


def test_inventory_export_permission_is_independent(test_db, authenticated_test_user):
  create_permission(
    name="inventory.read",
  )

  export_permission_id = create_permission(
    name="inventory.export",
  )

  assign_permission_to_user(
    1,
    export_permission_id,
  )

  assert (
    has_permission(
      1,
      "inventory.export",
    )
    is True
  )

  assert (
    has_permission(
      1,
      "inventory.import",
    )
    is False
  )


def test_audit_read_permission_is_independent(test_db, authenticated_test_user):
  audit_permission_id = create_permission(
    name="audit.read",
  )

  assign_permission_to_user(
    1,
    audit_permission_id,
  )

  assert (
    has_permission(
      1,
      "audit.read",
    )
    is True
  )

  assert (
    has_permission(
      1,
      "inventory.read",
    )
    is False
  )


def test_backup_permissions_are_independent(test_db, authenticated_test_user):
  create_permission(
    name="backup.create",
  )

  restore_permission_id = create_permission(
    name="backup.restore",
  )

  assign_permission_to_user(
    1,
    restore_permission_id,
  )

  assert (
    has_permission(
      1,
      "backup.restore",
    )
    is True
  )

  assert (
    has_permission(
      1,
      "backup.create",
    )
    is False
  )


def test_field_read_permission_is_allowed(test_db, authenticated_test_user):
  field_id = create_custom_field(
    name="Purchase Price",
    field_type="decimal",
  )

  permission_id = create_permission(
    name=f"field.{field_id}.read",
  )

  assign_permission_to_user(
    1,
    permission_id,
  )

  assert (
    has_permission(
      1,
      f"field.{field_id}.read",
    )
    is True
  )


def test_field_update_permission_is_allowed(test_db, authenticated_test_user):
  field_id = create_custom_field(
    name="Purchase Price",
    field_type="decimal",
  )

  permission_id = create_permission(
    name=f"field.{field_id}.update",
  )

  assign_permission_to_user(
    1,
    permission_id,
  )

  assert (
    has_permission(
      1,
      f"field.{field_id}.update",
    )
    is True
  )


def test_field_read_and_update_permissions_are_independent(
  test_db, authenticated_test_user
):
  field_id = create_custom_field(
    name="Purchase Price",
    field_type="decimal",
  )

  read_permission_id = create_permission(
    name=f"field.{field_id}.read",
  )

  assign_permission_to_user(
    1,
    read_permission_id,
  )

  assert (
    has_permission(
      1,
      f"field.{field_id}.read",
    )
    is True
  )

  assert (
    has_permission(
      1,
      f"field.{field_id}.update",
    )
    is False
  )


def test_field_permission_can_be_granted_through_role(test_db, authenticated_test_user):
  field_id = create_custom_field(
    name="Purchase Price",
    field_type="decimal",
  )

  permission_id = create_permission(
    name=f"field.{field_id}.read",
  )

  role_id = create_role(
    name="checker",
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
      f"field.{field_id}.read",
    )
    is True
  )


def test_direct_field_deny_overrides_role_allow(test_db, authenticated_test_user):
  field_id = create_custom_field(
    name="Purchase Price",
    field_type="decimal",
  )

  permission_id = create_permission(
    name=f"field.{field_id}.read",
  )

  role_id = create_role(
    name="checker",
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
      f"field.{field_id}.read",
    )
    is False
  )

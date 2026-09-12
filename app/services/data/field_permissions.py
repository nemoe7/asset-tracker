from ..exceptions.data.role_permissions import RolePermissionNotFoundError
from .permissions import create_permission, get_permission_by_name
from .role_permissions import (
  delete_role_permission,
  get_role_permissions,
  set_role_permission,
)
from .roles import get_roles
from .user_roles import is_admin_role


def _permission_name(field_id, operation):
  return f"field.{field_id}.{operation}"


def get_field_role_permissions(field_id):
  """Return each configurable role's view/edit grant state for a field.

  Only non-admin roles are configurable. The Admin role holds the global
  wildcard and always has access, so it is excluded.
  """
  roles = [role for role in get_roles() if not is_admin_role(role["id"])]

  result = {}

  for role in roles:
    permissions = {
      permission["permission"]: bool(permission["allowed"])
      for permission in get_role_permissions(role["id"])
    }

    result[role["id"]] = {
      "read": permissions.get(_permission_name(field_id, "read"), False),
      "update": permissions.get(_permission_name(field_id, "update"), False),
    }

  return result


def set_field_role_permissions(field_id, read_role_ids, update_role_ids):
  """Set which non-admin roles may view and edit the field by id.

  ``read_role_ids`` and ``update_role_ids`` name the roles granted the
  ``field.<id>.read`` and ``field.<id>.update`` permissions respectively.
  Roles omitted from a list lose the corresponding grant.
  """
  read_ids = set(read_role_ids)
  update_ids = set(update_role_ids)

  roles = [role for role in get_roles() if not is_admin_role(role["id"])]

  for role in roles:
    role_id = role["id"]
    _set_field_role_permission(field_id, role_id, "read", role_id in read_ids)
    _set_field_role_permission(field_id, role_id, "update", role_id in update_ids)


def _set_field_role_permission(field_id, role_id, operation, allowed):
  name = _permission_name(field_id, operation)
  permission = get_permission_by_name(name)

  if permission is None:
    permission_id = create_permission(name)
  else:
    permission_id = permission["id"]

  if allowed:
    set_role_permission(role_id, permission_id, True)
  else:
    try:
      delete_role_permission(role_id, permission_id)
    except RolePermissionNotFoundError:
      pass

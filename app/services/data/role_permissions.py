from ..exceptions.data.permissions import PermissionNotFoundError
from ..exceptions.data.role_permissions import *
from ..exceptions.data.roles import RoleNotFoundError
from .audit import create_audit_log
from .db import db_connection, db_transaction


def set_role_permission(role_id, permission_id, allowed):
  if not isinstance(allowed, bool):
    raise InvalidRolePermissionAllowedError()

  with db_transaction() as connection:
    role = connection.execute(
      """
      SELECT id
      FROM roles
      WHERE id = ?
      """,
      (role_id,),
    ).fetchone()

    if role is None:
      raise RoleNotFoundError()

    permission = connection.execute(
      """
      SELECT id
      FROM permissions
      WHERE id = ?
      """,
      (permission_id,),
    ).fetchone()

    if permission is None:
      raise PermissionNotFoundError()

    connection.execute(
      """
      INSERT INTO role_permissions (
        role_id,
        permission_id,
        allowed
      )
      VALUES (?, ?, ?)
      ON CONFLICT(role_id, permission_id)
      DO UPDATE SET allowed = excluded.allowed
      """,
      (role_id, permission_id, int(allowed)),
    )

    create_audit_log(
      action="updated",
      entity_type="role_permission",
      entity_id=f"{role_id}:{permission_id}",
      details={
        "role_id": role_id,
        "permission_id": permission_id,
        "allowed": allowed,
      },

    )

    return True


def get_role_permission(role_id, permission_id):
  with db_connection() as connection:
    return connection.execute(
      """
      SELECT
        role_id,
        permission_id,
        allowed
      FROM role_permissions
      WHERE role_id = ?
        AND permission_id = ?
      """,
      (role_id, permission_id),
    ).fetchone()


def get_role_permissions(role_id):
  with db_connection() as connection:
    role = connection.execute(
      """
      SELECT id
      FROM roles
      WHERE id = ?
      """,
      (role_id,),
    ).fetchone()

    if role is None:
      raise RoleNotFoundError()

    return connection.execute(
      """
      SELECT
        rp.role_id,
        rp.permission_id,
        p.name AS permission,
        rp.allowed
      FROM role_permissions rp
      JOIN permissions p
        ON p.id = rp.permission_id
      WHERE rp.role_id = ?
      ORDER BY p.name
      """,
      (role_id,),
    ).fetchall()


def delete_role_permission(role_id, permission_id):
  with db_transaction() as connection:
    existing = connection.execute(
      """
      SELECT 1
      FROM role_permissions
      WHERE role_id = ?
        AND permission_id = ?
      """,
      (role_id, permission_id),
    ).fetchone()

    if existing is None:
      raise RolePermissionNotFoundError()

    connection.execute(
      """
      DELETE FROM role_permissions
      WHERE role_id = ?
        AND permission_id = ?
      """,
      (role_id, permission_id),
    )

    create_audit_log(
      action="deleted",
      entity_type="role_permission",
      entity_id=f"{role_id}:{permission_id}",
      details={
        "role_id": role_id,
        "permission_id": permission_id,
      },

    )

    return True

from ..exceptions.data.permissions import PermissionNotFoundError
from ..exceptions.data.user_permissions import *
from ..exceptions.data.users import UserNotFoundError
from .audit import create_audit_log
from .db import db_connection, db_transaction


def set_user_permission(
  user_id,
  permission_id,
  allowed,
):
  if not isinstance(allowed, bool):
    raise InvalidUserPermissionAllowedError()

  with db_transaction() as connection:
    user = connection.execute(
      """
      SELECT id
      FROM users
      WHERE id = ?
      """,
      (user_id,),
    ).fetchone()

    if user is None:
      raise UserNotFoundError(user_id)

    permission = connection.execute(
      """
      SELECT id
      FROM permissions
      WHERE id = ?
      """,
      (permission_id,),
    ).fetchone()

    if permission is None:
      raise PermissionNotFoundError(permission_id)

    existing = connection.execute(
      """
      SELECT allowed
      FROM user_permissions
      WHERE user_id = ?
        AND permission_id = ?
      """,
      (user_id, permission_id),
    ).fetchone()

    if existing is not None and bool(existing["allowed"]) == allowed:
      return True

    connection.execute(
      """
      INSERT INTO user_permissions (
        user_id,
        permission_id,
        allowed
      )
      VALUES (?, ?, ?)
      ON CONFLICT(user_id, permission_id)
      DO UPDATE SET
        allowed = excluded.allowed
      """,
      (user_id, permission_id, allowed),
    )

    create_audit_log(
      action="updated",
      entity_type="user_permission",
      entity_id=f"{user_id}:{permission_id}",
      details={
        "user_id": user_id,
        "permission_id": permission_id,
        "allowed": allowed,
      },
    )

    return True


def get_user_permission(user_id, permission_id):
  with db_connection() as connection:
    return connection.execute(
      """
      SELECT
        user_id,
        permission_id,
        allowed
      FROM user_permissions
      WHERE user_id = ?
        AND permission_id = ?
      """,
      (user_id, permission_id),
    ).fetchone()


def get_user_permissions(user_id):
  with db_connection() as connection:
    user = connection.execute(
      """
      SELECT id
      FROM users
      WHERE id = ?
      """,
      (user_id,),
    ).fetchone()

    if user is None:
      raise UserNotFoundError()

    return connection.execute(
      """
      SELECT
        up.user_id,
        up.permission_id,
        p.name AS permission,
        up.allowed
      FROM user_permissions up
      JOIN permissions p
        ON p.id = up.permission_id
      WHERE up.user_id = ?
      ORDER BY p.name
      """,
      (user_id,),
    ).fetchall()


def delete_user_permission(user_id, permission_id):
  with db_transaction() as connection:
    existing = connection.execute(
      """
      SELECT 1
      FROM user_permissions
      WHERE user_id = ?
        AND permission_id = ?
      """,
      (user_id, permission_id),
    ).fetchone()

    if existing is None:
      raise UserPermissionNotFoundError()

    connection.execute(
      """
      DELETE FROM user_permissions
      WHERE user_id = ?
        AND permission_id = ?
      """,
      (user_id, permission_id),
    )

    create_audit_log(
      action="deleted",
      entity_type="user_permission",
      entity_id=f"{user_id}:{permission_id}",
      details={
        "user_id": user_id,
        "permission_id": permission_id,
      },
    )

    return True

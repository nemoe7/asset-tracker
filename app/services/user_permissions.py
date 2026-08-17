from app.db import get_db
from app.services.audit import create_audit_log


class UserPermissionAlreadyExistsError(Exception):
  pass


def assign_permission_to_user(
  user_id,
  permission_id,
):
  connection = get_db()

  try:
    user = connection.execute(
      """
      SELECT id
      FROM users
      WHERE id = ?
      """,
      (user_id,),
    ).fetchone()

    if user is None:
      raise ValueError("User does not exist")

    permission = connection.execute(
      """
      SELECT id
      FROM permissions
      WHERE id = ?
      """,
      (permission_id,),
    ).fetchone()

    if permission is None:
      raise ValueError("Permission does not exist")

    existing = connection.execute(
      """
      SELECT 1
      FROM user_permissions
      WHERE user_id = ?
        AND permission_id = ?
      """,
      (
        user_id,
        permission_id,
      ),
    ).fetchone()

    if existing is not None:
      raise UserPermissionAlreadyExistsError("Permission is already assigned to user")

    connection.execute(
      """
      INSERT INTO user_permissions (
        user_id,
        permission_id,
        allowed
      )
      VALUES (?, ?, ?)
      """,
      (
        user_id,
        permission_id,
        1,
      ),
    )

    create_audit_log(
      action="created",
      entity_type="user_permission",
      entity_id=f"{user_id}:{permission_id}",
      connection=connection,
    )

    connection.commit()

    return True
  except:
    connection.rollback()
    raise
  finally:
    connection.close()


def get_user_permissions(user_id):
  connection = get_db()

  try:
    return connection.execute(
      """
      SELECT permissions.*, user_permissions.allowed
      FROM permissions
      INNER JOIN user_permissions
        ON user_permissions.permission_id = permissions.id
      WHERE user_permissions.user_id = ?
      ORDER BY permissions.id
      """,
      (user_id,),
    ).fetchall()
  finally:
    connection.close()


def remove_permission_from_user(
  user_id,
  permission_id,
):
  connection = get_db()

  try:
    existing = connection.execute(
      """
      SELECT 1
      FROM user_permissions
      WHERE user_id = ?
        AND permission_id = ?
      """,
      (
        user_id,
        permission_id,
      ),
    ).fetchone()

    if existing is None:
      return False

    connection.execute(
      """
      DELETE FROM user_permissions
      WHERE user_id = ?
        AND permission_id = ?
      """,
      (
        user_id,
        permission_id,
      ),
    )

    create_audit_log(
      action="deleted",
      entity_type="user_permission",
      entity_id=f"{user_id}:{permission_id}",
      connection=connection,
    )

    connection.commit()

    return True
  except:
    connection.rollback()
    raise
  finally:
    connection.close()

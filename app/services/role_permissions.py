from app.db import get_db
from app.services.audit import create_audit_log


class RolePermissionAlreadyExistsError(Exception):
  pass


def assign_permission_to_role(
  role_id,
  permission_id,
):
  connection = get_db()

  try:
    role = connection.execute(
      """
      SELECT id
      FROM roles
      WHERE id = ?
      """,
      (role_id,),
    ).fetchone()

    if role is None:
      raise ValueError("Role does not exist")

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
      FROM role_permissions
      WHERE role_id = ?
        AND permission_id = ?
      """,
      (
        role_id,
        permission_id,
      ),
    ).fetchone()

    if existing is not None:
      raise RolePermissionAlreadyExistsError("Permission is already assigned to role")

    connection.execute(
      """
      INSERT INTO role_permissions (
        role_id,
        permission_id
      )
      VALUES (?, ?)
      """,
      (
        role_id,
        permission_id,
      ),
    )

    create_audit_log(
      action="created",
      entity_type="role_permission",
      entity_id=f"{role_id}:{permission_id}",
      connection=connection,
    )

    connection.commit()

    return True
  except:
    connection.rollback()
    raise
  finally:
    connection.close()


def get_role_permissions(role_id):
  connection = get_db()

  try:
    return connection.execute(
      """
      SELECT permissions.*
      FROM permissions
      INNER JOIN role_permissions
        ON role_permissions.permission_id = permissions.id
      WHERE role_permissions.role_id = ?
      ORDER BY permissions.id
      """,
      (role_id,),
    ).fetchall()
  finally:
    connection.close()


def remove_permission_from_role(
  role_id,
  permission_id,
):
  connection = get_db()

  try:
    existing = connection.execute(
      """
      SELECT 1
      FROM role_permissions
      WHERE role_id = ?
        AND permission_id = ?
      """,
      (
        role_id,
        permission_id,
      ),
    ).fetchone()

    if existing is None:
      return False

    connection.execute(
      """
      DELETE FROM role_permissions
      WHERE role_id = ?
        AND permission_id = ?
      """,
      (
        role_id,
        permission_id,
      ),
    )

    create_audit_log(
      action="deleted",
      entity_type="role_permission",
      entity_id=f"{role_id}:{permission_id}",
      connection=connection,
    )

    connection.commit()

    return True
  except:
    connection.rollback()
    raise
  finally:
    connection.close()

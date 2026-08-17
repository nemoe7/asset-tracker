from app.db import get_db


def has_permission(user_id, permission_name):
  connection = get_db()

  try:
    user = connection.execute(
      """
      SELECT id
      FROM users
      WHERE id = ?
        AND archived_at IS NULL
      """,
      (user_id,),
    ).fetchone()

    if user is None:
      return False

    permission = connection.execute(
      """
      SELECT id
      FROM permissions
      WHERE name = ?
      """,
      (permission_name,),
    ).fetchone()

    if permission is None:
      return False

    direct = connection.execute(
      """
      SELECT allowed
      FROM user_permissions
      WHERE user_id = ?
        AND permission_id = ?
      """,
      (
        user_id,
        permission["id"],
      ),
    ).fetchone()

    if direct is not None:
      return direct["allowed"] == 1

    role_permission = connection.execute(
      """
      SELECT 1
      FROM user_roles
      INNER JOIN role_permissions
        ON role_permissions.role_id = user_roles.role_id
      WHERE user_roles.user_id = ?
        AND role_permissions.permission_id = ?
      LIMIT 1
      """,
      (
        user_id,
        permission["id"],
      ),
    ).fetchone()

    return role_permission is not None
  finally:
    connection.close()

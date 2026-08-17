from app.db import get_db


def _get_permission_ids(connection, permission_name):
  permission_names = [permission_name]

  if "." in permission_name:
    namespace = permission_name.split(".", 1)[0]
    permission_names.append(f"{namespace}.*")

  permission_names.append("*")

  placeholders = ", ".join("?" for _ in permission_names)

  rows = connection.execute(
    f"""
    SELECT id, name
    FROM permissions
    WHERE name IN ({placeholders})
    """,
    permission_names,
  ).fetchall()

  return {row["name"]: row["id"] for row in rows}


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

    permissions = _get_permission_ids(
      connection,
      permission_name,
    )

    if not permissions:
      return False

    permission_ids = list(permissions.values())
    placeholders = ", ".join("?" for _ in permission_ids)

    direct = connection.execute(
      f"""
      SELECT permission_id, allowed
      FROM user_permissions
      WHERE user_id = ?
        AND permission_id IN ({placeholders})
      """,
      [user_id, *permission_ids],
    ).fetchall()

    direct_by_permission = {row["permission_id"]: row["allowed"] for row in direct}

    for permission_id in permission_ids:
      if permission_id in direct_by_permission:
        return direct_by_permission[permission_id] == 1

    role_permission = connection.execute(
      f"""
      SELECT 1
      FROM user_roles
      INNER JOIN role_permissions
        ON role_permissions.role_id = user_roles.role_id
      WHERE user_roles.user_id = ?
        AND role_permissions.permission_id IN ({placeholders})
      LIMIT 1
      """,
      [user_id, *permission_ids],
    ).fetchone()

    return role_permission is not None
  finally:
    connection.close()

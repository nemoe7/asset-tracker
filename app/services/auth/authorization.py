from functools import wraps

from flask import (
  abort,
  session,
)

from ..data.db import get_db


def _get_permission_precedence(permission_name):
  precedence = [permission_name]

  if "." in permission_name:
    namespace = permission_name.split(".", 1)[0]
    precedence.append(f"{namespace}.*")

  precedence.append("*")

  return precedence


def _get_direct_decision(
  connection,
  user_id,
  precedence,
):
  placeholders = ", ".join("?" for _ in precedence)

  rows = connection.execute(
    f"""
    SELECT
      permissions.name,
      user_permissions.allowed
    FROM user_permissions
    INNER JOIN permissions
      ON permissions.id = user_permissions.permission_id
    WHERE user_permissions.user_id = ?
      AND permissions.name IN ({placeholders})
    """,
    [user_id, *precedence],
  ).fetchall()

  decisions = {row["name"]: row["allowed"] == 1 for row in rows}

  for permission_name in precedence:
    if permission_name in decisions:
      return decisions[permission_name]

  return None


def _get_role_decision(
  connection,
  user_id,
  precedence,
):
  placeholders = ", ".join("?" for _ in precedence)

  rows = connection.execute(
    f"""
    SELECT
      permissions.name,
      role_permissions.allowed
    FROM user_roles
    INNER JOIN role_permissions
      ON role_permissions.role_id = user_roles.role_id
    INNER JOIN permissions
      ON permissions.id = role_permissions.permission_id
    WHERE user_roles.user_id = ?
      AND permissions.name IN ({placeholders})
    """,
    [user_id, *precedence],
  ).fetchall()

  decisions = {}

  for row in rows:
    permission_name = row["name"]
    allowed = row["allowed"] == 1

    if permission_name not in decisions:
      decisions[permission_name] = allowed
    elif not allowed:
      decisions[permission_name] = False

  for permission_name in precedence:
    if permission_name in decisions:
      return decisions[permission_name]

  return None


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

    precedence = _get_permission_precedence(
      permission_name,
    )

    direct_decision = _get_direct_decision(
      connection,
      user_id,
      precedence,
    )

    if direct_decision is not None:
      return direct_decision

    role_decision = _get_role_decision(
      connection,
      user_id,
      precedence,
    )

    if role_decision is not None:
      return role_decision

    return False
  finally:
    connection.close()


def permission_required(permission_name):
  def decorator(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
      user_id = session.get("user_id")

      if user_id is None:
        abort(403)

      if not has_permission(user_id, permission_name):
        abort(403)

      return view(*args, **kwargs)

    return wrapped

  return decorator

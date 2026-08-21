from ..exceptions.data.roles import RoleNotFoundError
from ..exceptions.data.user_roles import *
from ..exceptions.data.users import UserNotFoundError
from .audit import create_audit_log
from .db import get_db


def set_user_role(user_id, role_id):
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
      raise UserNotFoundError()

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

    connection.execute(
      """
      INSERT INTO user_roles (
        user_id,
        role_id
      )
      VALUES (?, ?)
      ON CONFLICT(user_id, role_id)
      DO NOTHING
      """,
      (user_id, role_id),
    )

    create_audit_log(
      action="updated",
      entity_type="user_role",
      entity_id=f"{user_id}:{role_id}",
      details={"user_id": user_id, "role_id": role_id},
      connection=connection,
    )

    connection.commit()

    return True
  except Exception:
    connection.rollback()
    raise
  finally:
    connection.close()


def get_user_role(user_id, role_id):
  connection = get_db()

  try:
    return connection.execute(
      """
      SELECT
        user_id,
        role_id
      FROM user_roles
      WHERE user_id = ?
        AND role_id = ?
      """,
      (user_id, role_id),
    ).fetchone()
  finally:
    connection.close()


def get_user_roles(user_id):
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
      raise UserNotFoundError()

    return connection.execute(
      """
      SELECT
        ur.user_id,
        ur.role_id,
        r.name AS role
      FROM user_roles ur
      JOIN roles r
        ON r.id = ur.role_id
      WHERE ur.user_id = ?
      ORDER BY r.name
      """,
      (user_id,),
    ).fetchall()
  finally:
    connection.close()


def delete_user_role(user_id, role_id):
  connection = get_db()

  try:
    existing = connection.execute(
      """
      SELECT 1
      FROM user_roles
      WHERE user_id = ?
        AND role_id = ?
      """,
      (user_id, role_id),
    ).fetchone()

    if existing is None:
      raise UserRoleNotFoundError()

    connection.execute(
      """
      DELETE FROM user_roles
      WHERE user_id = ?
        AND role_id = ?
      """,
      (user_id, role_id),
    )

    create_audit_log(
      action="deleted",
      entity_type="user_role",
      entity_id=f"{user_id}:{role_id}",
      details={"user_id": user_id, "role_id": role_id},
      connection=connection,
    )

    connection.commit()

    return True
  except Exception:
    connection.rollback()
    raise
  finally:
    connection.close()

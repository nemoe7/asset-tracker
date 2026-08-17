from app.db import get_db
from app.services.audit import create_audit_log


class UserRoleAlreadyExistsError(Exception):
  pass


def assign_role_to_user(user_id, role_id):
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

    existing = connection.execute(
      """
      SELECT 1
      FROM user_roles
      WHERE user_id = ?
        AND role_id = ?
      """,
      (
        user_id,
        role_id,
      ),
    ).fetchone()

    if existing is not None:
      raise UserRoleAlreadyExistsError("Role is already assigned to user")

    connection.execute(
      """
      INSERT INTO user_roles (
        user_id,
        role_id
      )
      VALUES (?, ?)
      """,
      (
        user_id,
        role_id,
      ),
    )

    create_audit_log(
      action="created",
      entity_type="user_role",
      entity_id=f"{user_id}:{role_id}",
      connection=connection,
    )

    connection.commit()

    return True
  except:
    connection.rollback()
    raise
  finally:
    connection.close()


def get_user_roles(user_id):
  connection = get_db()

  try:
    return connection.execute(
      """
      SELECT roles.*
      FROM roles
      INNER JOIN user_roles
        ON user_roles.role_id = roles.id
      WHERE user_roles.user_id = ?
      ORDER BY roles.id
      """,
      (user_id,),
    ).fetchall()
  finally:
    connection.close()


def remove_role_from_user(user_id, role_id):
  connection = get_db()

  try:
    existing = connection.execute(
      """
      SELECT 1
      FROM user_roles
      WHERE user_id = ?
        AND role_id = ?
      """,
      (
        user_id,
        role_id,
      ),
    ).fetchone()

    if existing is None:
      return False

    connection.execute(
      """
      DELETE FROM user_roles
      WHERE user_id = ?
        AND role_id = ?
      """,
      (
        user_id,
        role_id,
      ),
    )

    create_audit_log(
      action="deleted",
      entity_type="user_role",
      entity_id=f"{user_id}:{role_id}",
      connection=connection,
    )

    connection.commit()

    return True
  except:
    connection.rollback()
    raise
  finally:
    connection.close()

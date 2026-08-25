from werkzeug.security import generate_password_hash

from ..auth.context import reset_current_user, set_current_user
from .audit import create_audit_log
from .db import db_connection, db_transaction
from .users import _validate_password, _validate_username


def is_first_run():
  with db_connection() as connection:
    result = connection.execute(
      """
      SELECT 1
      FROM users
      LIMIT 1
      """
    ).fetchone()

    return result is None


def create_initial_admin(username, name, password):
  _validate_username(username)
  _validate_password(password)

  with db_transaction() as connection:
    cursor = connection.execute(
      """
      INSERT INTO users (
        username,
        name,
        password_hash,
        created_at,
        updated_at
      )
      VALUES (?, ?, ?, datetime('now'), datetime('now'))
      """,
      (
        username,
        name,
        generate_password_hash(password),
      ),
    )

    user_id = cursor.lastrowid

    token = set_current_user(user_id)

    try:
      create_audit_log(
        action="created",
        entity_type="user",
        entity_id=user_id,
      )

      admin_role = connection.execute(
        """
        SELECT id
        FROM roles
        WHERE name = 'Admin'
        """
      ).fetchone()

      if admin_role is None:
        raise RuntimeError("Admin role is missing from the database.")

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
          admin_role["id"],
        ),
      )
    finally:
      reset_current_user(token)

    return user_id

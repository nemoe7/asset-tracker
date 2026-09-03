from werkzeug.security import (
  check_password_hash,
  generate_password_hash,
)

from ..exceptions.data.common import InvalidInputError
from ..exceptions.data.users import *  # noqa: F403 -- intentional: full exception surface
from .audit import create_audit_log
from .db import db_connection, db_transaction


def _validate_username(username):
  if not isinstance(username, str) or not username.strip():
    raise InvalidUsernameError("Username cannot be empty")

  if len(username) < 3:
    raise InvalidUsernameError("Username must be at least 3 characters")

  if len(username) > 32:
    raise InvalidUsernameError("Username must be at most 32 characters")

  if not all(
    character.isascii() and (character.isalnum() or character in "._-")
    for character in username
  ):
    raise InvalidUsernameError(
      "Username can only contain letters, numbers, periods, underscores, and hyphens"
    )

  if not any(character.isalnum() for character in username):
    raise InvalidUsernameError("Username must contain at least one letter or number")


def _validate_name(name):
  if not isinstance(name, str) or not name.strip():
    raise InvalidNameError("Name cannot be empty")


def _validate_password(password):
  if not isinstance(password, str) or not password:
    raise InvalidPasswordError("Password cannot be empty")

  if len(password) < 8:
    raise InvalidPasswordError("Password must be at least 8 characters")

  if len(password) > 128:
    raise InvalidPasswordError("Password must be at most 128 characters")


def create_user(username, password, name=None):
  _validate_username(username)
  _validate_password(password)

  if name is None:
    name = username

  _validate_name(name)

  with db_transaction() as connection:
    existing = connection.execute(
      """
      SELECT id, archived_at
      FROM users
      WHERE username = ?
      """,
      (username,),
    ).fetchone()

    if existing is not None:
      if existing["archived_at"] is not None:
        raise UsernameIsArchivedError()

      raise UsernameAlreadyExistsError()

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

    create_audit_log(
      action="created",
      entity_type="user",
      entity_id=user_id,
    )

    return user_id


def get_user(user_id):
  with db_connection() as connection:
    return connection.execute(
      """
      SELECT
        id,
        username,
        name,
        created_at,
        updated_at,
        archived_at
      FROM users
      WHERE id = ?
      """,
      (user_id,),
    ).fetchone()


def get_user_by_username(username, include_archived=False):
  with db_connection() as connection:
    query = """
      SELECT
        id,
        username,
        name,
        created_at,
        updated_at,
        archived_at
      FROM users
      WHERE username = ?
    """

    parameters = [username]

    if not include_archived:
      query += """
        AND archived_at IS NULL
      """

    return connection.execute(
      query,
      parameters,
    ).fetchone()


def get_users():
  with db_connection() as connection:
    return connection.execute(
      """
      SELECT
        id,
        username,
        created_at,
        updated_at,
        archived_at
      FROM users
      WHERE archived_at IS NULL
      ORDER BY username
      """
    ).fetchall()


def update_user(user_id, username=None, name=None, password=None):
  if username is None and name is None and password is None:
    raise InvalidInputError("No fields to update")

  user = get_user(user_id)

  if user is None:
    raise UserNotFoundError()

  if user["archived_at"] is not None:
    raise UserIsArchivedError()

  if username is not None:
    _validate_username(username)

  if name is not None:
    _validate_name(name)

  if password is not None:
    _validate_password(password)

  with db_transaction() as connection:
    updates = []
    values = []
    details = {}

    if username is not None and username != user["username"]:
      duplicate = connection.execute(
        """
        SELECT id, archived_at
        FROM users
        WHERE username = ?
          AND id != ?
        """,
        (username, user_id),
      ).fetchone()

      if duplicate is not None:
        if duplicate["archived_at"] is not None:
          raise UsernameIsArchivedError()

        raise UsernameAlreadyExistsError()

      updates.append("username = ?")
      values.append(username)

      details["username"] = {
        "old": user["username"],
        "new": username,
      }

    if name is not None and name != user["name"]:
      updates.append("name = ?")
      values.append(name)

      details["name"] = {
        "old": user["name"],
        "new": name,
      }

    if password is not None and not verify_password(user_id, password):
      updates.append("password_hash = ?")
      values.append(generate_password_hash(password))

      details["password"] = "changed"

    if not updates:
      return True

    updates.append("updated_at = datetime('now')")
    values.append(user_id)

    connection.execute(
      f"""
      UPDATE users
      SET {", ".join(updates)}
      WHERE id = ?
        AND archived_at IS NULL
      """,
      values,
    )

    create_audit_log(
      action="updated",
      entity_type="user",
      entity_id=user_id,
      details=details,
    )

    return True


def archive_user(user_id):
  with db_transaction() as connection:
    user = connection.execute(
      """
      SELECT archived_at
      FROM users
      WHERE id = ?
      """,
      (user_id,),
    ).fetchone()

    if user is None:
      raise UserNotFoundError()

    if user["archived_at"] is not None:
      raise UserIsArchivedError()

    connection.execute(
      """
      UPDATE users
      SET archived_at = datetime('now'),
          updated_at = datetime('now')
      WHERE id = ?
      """,
      (user_id,),
    )

    create_audit_log(
      action="archived",
      entity_type="user",
      entity_id=user_id,
    )

    return True


def restore_user(user_id):
  with db_transaction() as connection:
    user = connection.execute(
      """
      SELECT archived_at
      FROM users
      WHERE id = ?
      """,
      (user_id,),
    ).fetchone()

    if user is None:
      raise UserNotFoundError()

    if user["archived_at"] is None:
      raise UserIsNotArchivedError()

    connection.execute(
      """
      UPDATE users
      SET archived_at = NULL,
          updated_at = datetime('now')
      WHERE id = ?
      """,
      (user_id,),
    )

    create_audit_log(
      action="restored",
      entity_type="user",
      entity_id=user_id,
    )

    return True


def verify_password(user_id, password):
  with db_connection() as connection:
    user = connection.execute(
      """
      SELECT password_hash
      FROM users
      WHERE id = ?
        AND archived_at IS NULL
      """,
      (user_id,),
    ).fetchone()

    if user is None:
      return False

    return check_password_hash(
      user["password_hash"],
      password,
    )

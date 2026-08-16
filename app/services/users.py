from werkzeug.security import check_password_hash, generate_password_hash

from app.db import get_db
from app.services.audit import create_audit_log


def _validate_username(username):
  if not isinstance(username, str) or not username.strip():
    raise ValueError("Username cannot be empty")


def _validate_password(password):
  if not isinstance(password, str) or not password:
    raise ValueError("Password cannot be empty")


def create_user(username, password):
  _validate_username(username)
  _validate_password(password)

  connection = get_db()

  try:
    existing = connection.execute(
      """
      SELECT id
      FROM users
      WHERE username = ?
        AND archived_at IS NULL
      """,
      (username,),
    ).fetchone()

    if existing is not None:
      raise ValueError("Username already exists")

    cursor = connection.execute(
      """
      INSERT INTO users (
        username,
        password_hash,
        created_at,
        updated_at
      )
      VALUES (?, ?, datetime('now'), datetime('now'))
      """,
      (
        username,
        generate_password_hash(password),
      ),
    )

    user_id = cursor.lastrowid

    create_audit_log(
      action="created",
      entity_type="user",
      entity_id=user_id,
      connection=connection,
    )

    connection.commit()

    return user_id
  except:
    connection.rollback()
    raise
  finally:
    connection.close()


def get_user(user_id):
  connection = get_db()

  try:
    return connection.execute(
      """
      SELECT
        id,
        username,
        password_hash,
        created_at,
        updated_at,
        archived_at
      FROM users
      WHERE id = ?
      """,
      (user_id,),
    ).fetchone()
  finally:
    connection.close()


def get_user_by_username(username):
  connection = get_db()

  try:
    return connection.execute(
      """
      SELECT
        id,
        username,
        password_hash,
        created_at,
        updated_at,
        archived_at
      FROM users
      WHERE username = ?
        AND archived_at IS NULL
      """,
      (username,),
    ).fetchone()
  finally:
    connection.close()


def get_users():
  connection = get_db()

  try:
    return connection.execute(
      """
      SELECT
        id,
        username,
        password_hash,
        created_at,
        updated_at,
        archived_at
      FROM users
      WHERE archived_at IS NULL
      ORDER BY username
      """
    ).fetchall()
  finally:
    connection.close()


def update_user(user_id, username=None, password=None):
  if username is None and password is None:
    raise ValueError("No fields to update")

  if username is not None:
    _validate_username(username)

  if password is not None:
    _validate_password(password)

  connection = get_db()

  try:
    existing = connection.execute(
      """
      SELECT *
      FROM users
      WHERE id = ?
        AND archived_at IS NULL
      """,
      (user_id,),
    ).fetchone()

    if existing is None:
      return False

    updates = []
    values = []
    details = {}

    if username is not None and existing["username"] != username:
      updates.append("username = ?")
      values.append(username)

      details["username"] = {
        "old": existing["username"],
        "new": username,
      }

    if password is not None:
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
      connection=connection,
    )

    connection.commit()

    return True
  except:
    connection.rollback()
    raise
  finally:
    connection.close()


def archive_user(user_id):
  connection = get_db()

  try:
    result = connection.execute(
      """
      UPDATE users
      SET archived_at = datetime('now'),
          updated_at = datetime('now')
      WHERE id = ?
        AND archived_at IS NULL
      """,
      (user_id,),
    )

    if result.rowcount == 0:
      connection.commit()
      return False

    create_audit_log(
      action="archived",
      entity_type="user",
      entity_id=user_id,
      connection=connection,
    )

    connection.commit()

    return True
  except:
    connection.rollback()
    raise
  finally:
    connection.close()


def restore_user(user_id):
  connection = get_db()

  try:
    result = connection.execute(
      """
      UPDATE users
      SET archived_at = NULL,
          updated_at = datetime('now')
      WHERE id = ?
        AND archived_at IS NOT NULL
      """,
      (user_id,),
    )

    if result.rowcount == 0:
      connection.commit()
      return False

    create_audit_log(
      action="restored",
      entity_type="user",
      entity_id=user_id,
      connection=connection,
    )

    connection.commit()

    return True
  except:
    connection.rollback()
    raise
  finally:
    connection.close()


def verify_password(user_id, password):
  connection = get_db()

  try:
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
  finally:
    connection.close()

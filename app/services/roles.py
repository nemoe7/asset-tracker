from app.db import get_db
from app.services.audit import create_audit_log


def _validate_name(name):
  if not isinstance(name, str) or not name.strip():
    raise ValueError("Role name cannot be empty")


def create_role(name, description=None):
  _validate_name(name)

  connection = get_db()

  try:
    existing = connection.execute(
      """
      SELECT id
      FROM roles
      WHERE name = ?
      """,
      (name,),
    ).fetchone()

    if existing is not None:
      raise ValueError("Role already exists")

    cursor = connection.execute(
      """
      INSERT INTO roles (
        name,
        description
      )
      VALUES (?, ?)
      """,
      (name, description),
    )

    role_id = cursor.lastrowid

    create_audit_log(
      action="created",
      entity_type="role",
      entity_id=role_id,
      connection=connection,
    )

    connection.commit()

    return role_id
  except:
    connection.rollback()
    raise
  finally:
    connection.close()


def get_role(role_id):
  connection = get_db()

  try:
    return connection.execute(
      """
      SELECT
        id,
        name,
        description
      FROM roles
      WHERE id = ?
      """,
      (role_id,),
    ).fetchone()
  finally:
    connection.close()


def get_roles():
  connection = get_db()

  try:
    return connection.execute(
      """
      SELECT
        id,
        name,
        description
      FROM roles
      ORDER BY name
      """
    ).fetchall()
  finally:
    connection.close()


def update_role(role_id, name=None, description=None):
  if name is None and description is None:
    raise ValueError("No fields to update")

  if name is not None:
    _validate_name(name)

  connection = get_db()

  try:
    existing = connection.execute(
      """
      SELECT *
      FROM roles
      WHERE id = ?
      """,
      (role_id,),
    ).fetchone()

    if existing is None:
      return False

    updates = []
    values = []
    details = {}

    if name is not None and existing["name"] != name:
      duplicate = connection.execute(
        """
        SELECT id
        FROM roles
        WHERE name = ?
          AND id != ?
        """,
        (name, role_id),
      ).fetchone()

      if duplicate is not None:
        raise ValueError("Role already exists")

      updates.append("name = ?")
      values.append(name)

      details["name"] = {
        "old": existing["name"],
        "new": name,
      }

    if description is not None and existing["description"] != description:
      updates.append("description = ?")
      values.append(description)

      details["description"] = {
        "old": existing["description"],
        "new": description,
      }

    if not updates:
      return True

    values.append(role_id)

    connection.execute(
      f"""
      UPDATE roles
      SET {", ".join(updates)}
      WHERE id = ?
      """,
      values,
    )

    create_audit_log(
      action="updated",
      entity_type="role",
      entity_id=role_id,
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


def delete_role(role_id):
  connection = get_db()

  try:
    result = connection.execute(
      """
      DELETE FROM roles
      WHERE id = ?
      """,
      (role_id,),
    )

    if result.rowcount == 0:
      connection.commit()
      return False

    create_audit_log(
      action="deleted",
      entity_type="role",
      entity_id=role_id,
      connection=connection,
    )

    connection.commit()

    return True
  except:
    connection.rollback()
    raise
  finally:
    connection.close()

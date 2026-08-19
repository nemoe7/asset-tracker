from app.db import get_db
from app.services.audit import create_audit_log


def _validate_name(name):
  if not isinstance(name, str) or not name.strip():
    raise ValueError("Permission name cannot be empty")


def create_permission(name, description=None):
  _validate_name(name)

  connection = get_db()

  try:
    existing = connection.execute(
      """
      SELECT id
      FROM permissions
      WHERE name = ?
      """,
      (name,),
    ).fetchone()

    if existing is not None:
      return existing["id"]

    cursor = connection.execute(
      """
      INSERT INTO permissions (
        name,
        description
      )
      VALUES (?, ?)
      """,
      (name, description),
    )

    permission_id = cursor.lastrowid

    create_audit_log(
      action="created",
      entity_type="permission",
      entity_id=permission_id,
      connection=connection,
    )

    connection.commit()

    return permission_id
  except:
    connection.rollback()
    raise
  finally:
    connection.close()


def get_permission(permission_id):
  connection = get_db()

  try:
    return connection.execute(
      """
      SELECT
        id,
        name,
        description
      FROM permissions
      WHERE id = ?
      """,
      (permission_id,),
    ).fetchone()
  finally:
    connection.close()


def get_permissions():
  connection = get_db()

  try:
    return connection.execute(
      """
      SELECT
        id,
        name,
        description
      FROM permissions
      ORDER BY name
      """
    ).fetchall()
  finally:
    connection.close()


def update_permission(
  permission_id,
  name=None,
  description=None,
):
  if name is None and description is None:
    raise ValueError("No fields to update")

  if name is not None:
    _validate_name(name)

  connection = get_db()

  try:
    existing = connection.execute(
      """
      SELECT *
      FROM permissions
      WHERE id = ?
      """,
      (permission_id,),
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
        FROM permissions
        WHERE name = ?
          AND id != ?
        """,
        (name, permission_id),
      ).fetchone()

      if duplicate is not None:
        raise ValueError("Permission already exists")

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

    values.append(permission_id)

    connection.execute(
      f"""
      UPDATE permissions
      SET {", ".join(updates)}
      WHERE id = ?
      """,
      values,
    )

    create_audit_log(
      action="updated",
      entity_type="permission",
      entity_id=permission_id,
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


def delete_permission(permission_id):
  connection = get_db()

  try:
    result = connection.execute(
      """
      DELETE FROM permissions
      WHERE id = ?
      """,
      (permission_id,),
    )

    if result.rowcount == 0:
      connection.commit()
      return False

    create_audit_log(
      action="deleted",
      entity_type="permission",
      entity_id=permission_id,
      connection=connection,
    )

    connection.commit()

    return True
  except:
    connection.rollback()
    raise
  finally:
    connection.close()

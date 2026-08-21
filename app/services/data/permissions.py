from ..exceptions.data.common import InvalidInputError
from ..exceptions.data.permissions import *
from .audit import create_audit_log
from .db import get_db

_UNSET = object()


def _validate_name(name):
  if not isinstance(name, str) or not name.strip():
    raise InvalidPermissionNameError()


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
      raise PermissionAlreadyExistsError()

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


def get_permission_by_name(name):
  _validate_name(name)
  connection = get_db()

  try:
    return connection.execute(
      """
      SELECT
        id,
        name,
        description
      FROM permissions
      WHERE name = ?
      """,
      (name,),
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
  name=_UNSET,
  description=_UNSET,
):
  if name is _UNSET and description is _UNSET:
    raise InvalidInputError("No fields to update")

  if name is not _UNSET:
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
      raise PermissionNotFoundError()

    updates = []
    values = []
    details = {}

    if name is not _UNSET and existing["name"] != name:
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
        raise PermissionAlreadyExistsError()

      updates.append("name = ?")
      values.append(name)

      details["name"] = {
        "old": existing["name"],
        "new": name,
      }

    if description is not _UNSET and existing["description"] != description:
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
    existing = connection.execute(
      """
      SELECT id
      FROM permissions
      WHERE id = ?
      """,
      (permission_id,),
    ).fetchone()

    if existing is None:
      raise PermissionNotFoundError()

    connection.execute(
      """
      DELETE FROM permissions
      WHERE id = ?
      """,
      (permission_id,),
    )

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

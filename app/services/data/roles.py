from ..exceptions.data.common import InvalidInputError
from ..exceptions.data.roles import *
from .audit import create_audit_log
from .db import db_connection, db_transaction


def _validate_name(name):
  if not isinstance(name, str) or not name.strip():
    raise InvalidRoleNameError()


def create_role(name, description=None):
  _validate_name(name)

  with db_transaction() as connection:
    existing = connection.execute(
      """
      SELECT id
      FROM roles
      WHERE name = ?
      """,
      (name,),
    ).fetchone()

    if existing is not None:
      raise RoleAlreadyExistsError()

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

    )

    return role_id


def get_role(role_id):
  with db_connection() as connection:
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


def get_roles():
  with db_connection() as connection:
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


def update_role(
  role_id,
  name=None,
  description=None,
):
  if name is None and description is None:
    raise InvalidInputError("No fields to update")

  if name is not None:
    _validate_name(name)

  with db_transaction() as connection:
    existing = connection.execute(
      """
      SELECT *
      FROM roles
      WHERE id = ?
      """,
      (role_id,),
    ).fetchone()

    if existing is None:
      raise RoleNotFoundError()

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
        raise RoleAlreadyExistsError()

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

    )

    return True


def delete_role(role_id):
  with db_transaction() as connection:
    result = connection.execute(
      """
      DELETE FROM roles
      WHERE id = ?
      """,
      (role_id,),
    )

    if result.rowcount == 0:
      raise RoleNotFoundError()

    create_audit_log(
      action="deleted",
      entity_type="role",
      entity_id=role_id,

    )

    return True

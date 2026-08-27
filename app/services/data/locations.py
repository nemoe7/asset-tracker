from ..exceptions.data.common import InvalidInputError
from ..exceptions.data.locations import *
from .audit import create_audit_log
from .db import db_connection, db_transaction

_UNSET = object()


def _validate_location_name(name):
  if not isinstance(name, str) or not name.strip():
    raise InvalidLocationNameError()


def create_location(name, description=None):
  _validate_location_name(name)

  with db_transaction() as connection:
    existing = connection.execute(
      """
      SELECT id
      FROM locations
      WHERE name = ?
      """,
      (name,),
    ).fetchone()

    if existing is not None:
      raise LocationAlreadyExistsError()

    cursor = connection.execute(
      """
      INSERT INTO locations (
        name,
        description,
        created_at,
        updated_at
      )
      VALUES (?, ?, datetime('now'), datetime('now'))
      """,
      (
        name,
        description,
      ),
    )

    location_id = cursor.lastrowid

    create_audit_log(
      action="created",
      entity_type="location",
      entity_id=location_id,
    )

    return location_id


def get_location(location_id):
  with db_connection() as connection:
    return connection.execute(
      """
      SELECT *
      FROM locations
      WHERE id = ?
      """,
      (location_id,),
    ).fetchone()


def get_location_by_name(name):
  with db_connection() as connection:
    return connection.execute(
      """
      SELECT *
      FROM locations
      WHERE name = ?
      """,
      (name,),
    ).fetchone()


def get_locations():
  with db_connection() as connection:
    return connection.execute(
      """
      SELECT *
      FROM locations
      ORDER BY id
      """
    ).fetchall()


def update_location(
  location_id,
  name=_UNSET,
  description=_UNSET,
):
  if name is _UNSET and description is _UNSET:
    raise InvalidInputError("No fields to update")

  with db_transaction() as connection:
    existing = connection.execute(
      """
      SELECT *
      FROM locations
      WHERE id = ?
      """,
      (location_id,),
    ).fetchone()

    if existing is None:
      raise LocationNotFoundError()

    updates = []
    values = []
    details = {}

    if name is not _UNSET:
      _validate_location_name(name)

      if name != existing["name"]:
        duplicate = connection.execute(
          """
          SELECT id
          FROM locations
          WHERE name = ?
            AND id != ?
          """,
          (
            name,
            location_id,
          ),
        ).fetchone()

        if duplicate is not None:
          raise LocationAlreadyExistsError()

        updates.append("name = ?")
        values.append(name)

        details["name"] = {
          "old": existing["name"],
          "new": name,
        }

    if description is not _UNSET and description != existing["description"]:
      updates.append("description = ?")
      values.append(description)

      details["description"] = {
        "old": existing["description"],
        "new": description,
      }

    if not updates:
      return True

    updates.append("updated_at = datetime('now')")
    values.append(location_id)

    connection.execute(
      f"""
      UPDATE locations
      SET {", ".join(updates)}
      WHERE id = ?
      """,
      values,
    )

    create_audit_log(
      action="updated",
      entity_type="location",
      entity_id=location_id,
      details=details,
    )

    return True


def delete_location(location_id, confirm=False):
  if not confirm:
    raise LocationDeletionConfirmationRequired(
      "Deleting a location requires confirmation"
    )

  with db_transaction() as connection:
    existing = connection.execute(
      """
      SELECT id
      FROM locations
      WHERE id = ?
      """,
      (location_id,),
    ).fetchone()

    if existing is None:
      raise LocationNotFoundError()

    connection.execute(
      """
      DELETE FROM locations
      WHERE id = ?
      """,
      (location_id,),
    )

    create_audit_log(
      action="deleted",
      entity_type="location",
      entity_id=location_id,
    )

    return True

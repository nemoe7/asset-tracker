from app.db import get_db
from app.services.audit import create_audit_log


class LocationDeletionConfirmationRequired(Exception):
  pass


def create_location(name, description=None):
  connection = get_db()

  try:
    result = connection.execute(
      """
      INSERT INTO locations (
        name,
        description,
        created_at,
        updated_at
      )
      VALUES (?, ?, datetime('now'), datetime('now'))
      """,
      (name, description),
    )

    location_id = result.lastrowid

    create_audit_log(
      action="created",
      entity_type="location",
      entity_id=location_id,
      connection=connection,
    )

    connection.commit()

    return location_id
  except:
    connection.rollback()
    raise
  finally:
    connection.close()


def get_location(location_id):
  connection = get_db()

  try:
    return connection.execute(
      """
      SELECT *
      FROM locations
      WHERE id = ?
      """,
      (location_id,),
    ).fetchone()
  finally:
    connection.close()


def get_locations():
  connection = get_db()

  try:
    return connection.execute(
      """
      SELECT *
      FROM locations
      ORDER BY name
      """
    ).fetchall()
  finally:
    connection.close()


def update_location(location_id, name, description=None):
  connection = get_db()

  try:
    result = connection.execute(
      """
      UPDATE locations
      SET name = ?,
          description = ?,
          updated_at = datetime('now')
      WHERE id = ?
      """,
      (name, description, location_id),
    )

    if result.rowcount == 0:
      connection.rollback()
      return False

    create_audit_log(
      action="updated",
      entity_type="location",
      entity_id=location_id,
      connection=connection,
    )

    connection.commit()

    return True
  except:
    connection.rollback()
    raise
  finally:
    connection.close()


def delete_location(location_id, confirmed=False):
  connection = get_db()

  try:
    location = connection.execute(
      """
      SELECT id
      FROM locations
      WHERE id = ?
      """,
      (location_id,),
    ).fetchone()

    if location is None:
      return False

    items = connection.execute(
      """
      SELECT id
      FROM inventory_items
      WHERE location_id = ?
      """,
      (location_id,),
    ).fetchall()

    if items and not confirmed:
      raise LocationDeletionConfirmationRequired(
        f"Location {location_id} contains {len(items)} inventory items"
      )

    for item in items:
      connection.execute(
        """
        UPDATE inventory_items
        SET location_id = NULL,
            updated_at = datetime('now')
        WHERE id = ?
        """,
        (item["id"],),
      )

      create_audit_log(
        action="location_changed",
        entity_type="inventory_item",
        entity_id=item["id"],
        details={
          "old_location_id": location_id,
          "new_location_id": None,
        },
        connection=connection,
      )

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
      connection=connection,
    )

    connection.commit()

    return True
  except:
    connection.rollback()
    raise
  finally:
    connection.close()

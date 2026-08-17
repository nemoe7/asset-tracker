import uuid

from app.db import get_db
from app.services.audit import create_audit_log

_UNSET = object()


def _validate_item_name(name):
  if not isinstance(name, str) or not name.strip():
    raise ValueError("Item name cannot be empty")


def _validate_location(connection, location_id):
  if location_id is None:
    return

  location = connection.execute(
    """
    SELECT id
    FROM locations
    WHERE id = ?
    """,
    (location_id,),
  ).fetchone()

  if location is None:
    raise ValueError("Location does not exist")


def _get_custom_fields(connection, item_id):
  rows = connection.execute(
    """
    SELECT
      inventory_item_fields.field_id,
      inventory_item_fields.value,
      custom_fields.field_type
    FROM inventory_item_fields
    JOIN custom_fields
      ON custom_fields.id = inventory_item_fields.field_id
    WHERE inventory_item_fields.item_id = ?
    """,
    (item_id,),
  ).fetchall()

  fields = {}

  for row in rows:
    value = row["value"]
    field_type = row["field_type"]

    if field_type == "integer":
      value = int(value)
    elif field_type == "decimal":
      value = float(value)
    elif field_type == "boolean":
      value = value == "1"

    fields[row["field_id"]] = value

  return fields


def _item_with_custom_fields(connection, item):
  if item is None:
    return None

  item = dict(item)
  item["custom_fields"] = _get_custom_fields(
    connection,
    item["id"],
  )

  return item


def create_item(name, location_id=None):
  item_id = str(uuid.uuid4())

  connection = get_db()

  try:
    _validate_item_name(name)
    _validate_location(connection, location_id)

    connection.execute(
      """
      INSERT INTO inventory_items (
        id,
        name,
        location_id,
        created_at,
        updated_at
      )
      VALUES (?, ?, ?, datetime('now'), datetime('now'))
      """,
      (
        item_id,
        name,
        location_id,
      ),
    )

    create_audit_log(
      action="created",
      entity_type="inventory_item",
      entity_id=item_id,
      connection=connection,
    )

    connection.commit()

    return item_id
  except:
    connection.rollback()
    raise
  finally:
    connection.close()


def get_item(item_id):
  connection = get_db()

  try:
    item = connection.execute(
      """
      SELECT *
      FROM inventory_items
      WHERE id = ?
        AND archived_at IS NULL
      """,
      (item_id,),
    ).fetchone()

    return _item_with_custom_fields(
      connection,
      item,
    )
  finally:
    connection.close()


def get_items():
  connection = get_db()

  try:
    items = connection.execute(
      """
      SELECT *
      FROM inventory_items
      WHERE archived_at IS NULL
      ORDER BY name
      """
    ).fetchall()

    return [_item_with_custom_fields(connection, item) for item in items]
  finally:
    connection.close()


def update_item(
  item_id,
  name=_UNSET,
  location_id=_UNSET,
):
  connection = get_db()

  try:
    existing = connection.execute(
      """
      SELECT *
      FROM inventory_items
      WHERE id = ?
        AND archived_at IS NULL
      """,
      (item_id,),
    ).fetchone()

    if existing is None:
      return False

    updates = []
    values = []
    details = {}

    if name is not _UNSET:
      _validate_item_name(name)

      if existing["name"] != name:
        updates.append("name = ?")
        values.append(name)

        details["name"] = {
          "old": existing["name"],
          "new": name,
        }

    if location_id is not _UNSET:
      _validate_location(
        connection,
        location_id,
      )

      if existing["location_id"] != location_id:
        updates.append("location_id = ?")
        values.append(location_id)

        details["location_id"] = {
          "old": existing["location_id"],
          "new": location_id,
        }

    if not updates:
      connection.commit()
      return True

    updates.append("updated_at = datetime('now')")
    values.append(item_id)

    result = connection.execute(
      f"""
      UPDATE inventory_items
      SET {", ".join(updates)}
      WHERE id = ?
        AND archived_at IS NULL
      """,
      values,
    )

    create_audit_log(
      action="updated",
      entity_type="inventory_item",
      entity_id=item_id,
      details=details,
      connection=connection,
    )

    connection.commit()

    return result.rowcount > 0
  except:
    connection.rollback()
    raise
  finally:
    connection.close()


def archive_item(item_id):
  connection = get_db()

  try:
    result = connection.execute(
      """
      UPDATE inventory_items
      SET archived_at = datetime('now'),
          updated_at = datetime('now')
      WHERE id = ?
        AND archived_at IS NULL
      """,
      (item_id,),
    )

    if result.rowcount == 0:
      connection.commit()
      return False

    create_audit_log(
      action="archived",
      entity_type="inventory_item",
      entity_id=item_id,
      connection=connection,
    )

    connection.commit()

    return True
  except:
    connection.rollback()
    raise
  finally:
    connection.close()


def restore_item(item_id):
  connection = get_db()

  try:
    result = connection.execute(
      """
      UPDATE inventory_items
      SET archived_at = NULL,
          updated_at = datetime('now')
      WHERE id = ?
        AND archived_at IS NOT NULL
      """,
      (item_id,),
    )

    if result.rowcount == 0:
      connection.commit()
      return False

    create_audit_log(
      action="restored",
      entity_type="inventory_item",
      entity_id=item_id,
      connection=connection,
    )

    connection.commit()

    return True
  except:
    connection.rollback()
    raise
  finally:
    connection.close()

from datetime import date

from app.db import get_db
from app.services.audit import create_audit_log


def _validate_value(field_type, value):
  if field_type == "text":
    if not isinstance(value, str):
      raise ValueError("Value must be text")

    return value

  if field_type == "integer":
    if isinstance(value, bool):
      raise ValueError("Value must be an integer")

    try:
      return int(value)
    except (TypeError, ValueError):
      raise ValueError("Value must be an integer")

  if field_type == "decimal":
    if isinstance(value, bool):
      raise ValueError("Value must be a decimal")

    try:
      return float(value)
    except (TypeError, ValueError):
      raise ValueError("Value must be a decimal")

  if field_type == "boolean":
    if not isinstance(value, bool):
      raise ValueError("Value must be a boolean")

    return value

  if field_type == "date":
    if not isinstance(value, str):
      raise ValueError("Value must be a date")

    try:
      date.fromisoformat(value)
    except ValueError:
      raise ValueError("Value must be a valid date")

    return value

  raise ValueError("Invalid custom field type")


def _serialize_value(field_type, value):
  value = _validate_value(field_type, value)

  if field_type == "boolean":
    return "1" if value else "0"

  if field_type == "decimal":
    return str(value)

  return str(value)


def _deserialize_value(field_type, value):
  if value is None:
    return None

  if field_type == "text":
    return value

  if field_type == "integer":
    return int(value)

  if field_type == "decimal":
    return float(value)

  if field_type == "boolean":
    return value == "1"

  if field_type == "date":
    return value

  raise ValueError("Invalid custom field type")


def _get_field(connection, field_id):
  return connection.execute(
    """
    SELECT *
    FROM custom_fields
    WHERE id = ?
    """,
    (field_id,),
  ).fetchone()


def _get_item(connection, item_id):
  return connection.execute(
    """
    SELECT *
    FROM inventory_items
    WHERE id = ?
    """,
    (item_id,),
  ).fetchone()


def set_custom_field_value(item_id, field_id, value):
  connection = get_db()

  try:
    item = _get_item(connection, item_id)

    if item is None:
      raise ValueError("Inventory item does not exist")

    field = _get_field(connection, field_id)

    if field is None:
      raise ValueError("Custom field does not exist")

    serialized_value = _serialize_value(
      field["field_type"],
      value,
    )

    existing = connection.execute(
      """
      SELECT value
      FROM inventory_item_fields
      WHERE item_id = ?
        AND field_id = ?
      """,
      (item_id, field_id),
    ).fetchone()

    if existing is None:
      connection.execute(
        """
        INSERT INTO inventory_item_fields (
          item_id,
          field_id,
          value
        )
        VALUES (?, ?, ?)
        """,
        (
          item_id,
          field_id,
          serialized_value,
        ),
      )

      create_audit_log(
        action="created",
        entity_type="inventory_item_field",
        entity_id=f"{item_id}:{field_id}",
        connection=connection,
      )
    else:
      old_value = _deserialize_value(
        field["field_type"],
        existing["value"],
      )

      if old_value == value:
        connection.commit()
        return

      connection.execute(
        """
        UPDATE inventory_item_fields
        SET value = ?
        WHERE item_id = ?
          AND field_id = ?
        """,
        (
          serialized_value,
          item_id,
          field_id,
        ),
      )

      create_audit_log(
        action="updated",
        entity_type="inventory_item_field",
        entity_id=f"{item_id}:{field_id}",
        details={
          "value": {
            "old": old_value,
            "new": value,
          },
        },
        connection=connection,
      )

    connection.commit()
  except:
    connection.rollback()
    raise
  finally:
    connection.close()


def get_custom_field_value(item_id, field_id):
  connection = get_db()

  try:
    field = _get_field(connection, field_id)

    if field is None:
      return None

    result = connection.execute(
      """
      SELECT value
      FROM inventory_item_fields
      WHERE item_id = ?
        AND field_id = ?
      """,
      (item_id, field_id),
    ).fetchone()

    if result is None:
      return None

    return _deserialize_value(
      field["field_type"],
      result["value"],
    )
  finally:
    connection.close()


def clear_custom_field_value(item_id, field_id):
  connection = get_db()

  try:
    field = _get_field(connection, field_id)

    if field is None:
      return False

    existing = connection.execute(
      """
      SELECT value
      FROM inventory_item_fields
      WHERE item_id = ?
        AND field_id = ?
      """,
      (item_id, field_id),
    ).fetchone()

    if existing is None:
      return False

    old_value = _deserialize_value(
      field["field_type"],
      existing["value"],
    )

    connection.execute(
      """
      DELETE FROM inventory_item_fields
      WHERE item_id = ?
        AND field_id = ?
      """,
      (item_id, field_id),
    )

    create_audit_log(
      action="cleared",
      entity_type="inventory_item_field",
      entity_id=f"{item_id}:{field_id}",
      details={
        "value": {
          "old": old_value,
          "new": None,
        },
      },
      connection=connection,
    )

    connection.commit()

    return True
  except:
    connection.rollback()
    raise
  finally:
    connection.close()

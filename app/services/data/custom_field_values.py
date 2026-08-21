import json
from datetime import date

from ..exceptions.data.custom_field_values import *
from ..exceptions.data.custom_fields import (
  CustomFieldArchivedError,
  CustomFieldNotFoundError,
)
from ..exceptions.data.inventory import ItemNotFoundError
from .db import get_db


def _validate_value(field, value, connection):
  field_type = field["field_type"]

  if value is None:
    if field["required"]:
      raise RequiredCustomFieldError()
    return

  if field_type == "text":
    if not isinstance(value, str):
      raise InvalidCustomFieldValueError("Value must be a string")

  elif field_type == "integer":
    if isinstance(value, bool) or not isinstance(value, int):
      raise InvalidCustomFieldValueError("Value must be an integer")

  elif field_type == "decimal":
    if isinstance(value, bool) or not isinstance(value, (int, float)):
      raise InvalidCustomFieldValueError("Value must be a decimal")

  elif field_type == "boolean":
    if not isinstance(value, bool):
      raise InvalidCustomFieldValueError("Value must be a boolean")

  elif field_type == "date":
    if not isinstance(value, str):
      raise InvalidCustomFieldValueError("Value must be a date in YYYY-MM-DD format")

    try:
      date.fromisoformat(value)
    except ValueError:
      raise InvalidCustomFieldValueError("Value must be a date in YYYY-MM-DD format")

  elif field_type == "enum":
    if not isinstance(value, str):
      raise InvalidCustomFieldEnumValueError("Value must be a string")

    enum_values = json.loads(field["enum_values"])

    if value not in enum_values:
      raise InvalidCustomFieldEnumValueError(
        f"Value '{value}' is not one of: {', '.join(enum_values)}"
      )

  elif field_type == "user":
    if isinstance(value, bool) or not isinstance(value, int):
      raise InvalidCustomFieldValueError("Value must be a user ID")

    user = connection.execute(
      """
      SELECT 1
      FROM users
      WHERE id = ?
        AND archived_at IS NULL
      """,
      (value,),
    ).fetchone()

    if user is None:
      raise InvalidCustomFieldValueError(f"User with ID {value} does not exist")


def _serialize_value(field_type, value):
  if value is None:
    return None

  if field_type == "boolean":
    return "1" if value else "0"

  return str(value)


def set_custom_field_value(item_id, field_id, value):
  connection = get_db()

  try:
    item = connection.execute(
      """
      SELECT 1
      FROM inventory_items
      WHERE id = ?
      """,
      (item_id,),
    ).fetchone()

    if item is None:
      raise ItemNotFoundError()

    field = connection.execute(
      """
      SELECT
        id,
        field_type,
        required,
        enum_values,
        archived_at
      FROM custom_fields
      WHERE id = ?
      """,
      (field_id,),
    ).fetchone()

    if field is None:
      raise CustomFieldNotFoundError()

    if field["archived_at"] is not None:
      raise CustomFieldArchivedError()

    _validate_value(
      field,
      value,
      connection,
    )

    if value is None:
      connection.execute(
        """
        DELETE FROM inventory_item_fields
        WHERE item_id = ?
          AND field_id = ?
        """,
        (item_id, field_id),
      )

      connection.commit()

      return True

    serialized_value = _serialize_value(
      field["field_type"],
      value,
    )

    connection.execute(
      """
      INSERT INTO inventory_item_fields (
        item_id,
        field_id,
        value
      )
      VALUES (?, ?, ?)
      ON CONFLICT(item_id, field_id)
      DO UPDATE SET value = excluded.value
      """,
      (
        item_id,
        field_id,
        serialized_value,
      ),
    )

    connection.commit()

    return True
  except Exception:
    connection.rollback()
    raise
  finally:
    connection.close()


def get_custom_field_value(item_id, field_id):
  connection = get_db()

  try:
    return connection.execute(
      """
      SELECT
        item_id,
        field_id,
        value
      FROM inventory_item_fields
      WHERE item_id = ?
        AND field_id = ?
      """,
      (item_id, field_id),
    ).fetchone()
  finally:
    connection.close()


def get_custom_field_values(item_id):
  connection = get_db()

  try:
    return connection.execute(
      """
      SELECT
        item_id,
        field_id,
        value
      FROM inventory_item_fields
      WHERE item_id = ?
      ORDER BY field_id
      """,
      (item_id,),
    ).fetchall()
  finally:
    connection.close()


def delete_custom_field_value(item_id, field_id):
  connection = get_db()

  try:
    field = connection.execute(
      """
      SELECT
        id,
        required,
        archived_at
      FROM custom_fields
      WHERE id = ?
      """,
      (field_id,),
    ).fetchone()

    if field is None:
      raise CustomFieldNotFoundError()

    value = connection.execute(
      """
      SELECT 1
      FROM inventory_item_fields
      WHERE item_id = ?
        AND field_id = ?
      """,
      (item_id, field_id),
    ).fetchone()

    if value is None:
      raise CustomFieldValueNotFoundError()

    if field["required"]:
      raise RequiredCustomFieldError()

    connection.execute(
      """
      DELETE FROM inventory_item_fields
      WHERE item_id = ?
        AND field_id = ?
      """,
      (item_id, field_id),
    )

    connection.commit()

    return True
  except Exception:
    connection.rollback()
    raise
  finally:
    connection.close()

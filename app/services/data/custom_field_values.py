import json
from datetime import date

from ..exceptions.data.custom_field_values import *
from ..exceptions.data.custom_fields import (
  CustomFieldIsArchivedError,
  CustomFieldNotFoundError,
)
from ..exceptions.data.inventory import ItemNotFoundError
from .audit import create_audit_log
from .db import db_connection, db_transaction
from .users import get_user


def _validate_value(field, value):
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

    user = get_user(value)

    if user is None:
      raise InvalidCustomFieldValueError(f"User with ID {value} does not exist")


def _serialize_value(field_type, value):
  if value is None:
    return None

  if field_type == "boolean":
    return "1" if value else "0"

  return str(value)


def set_custom_field_value(item_id, field_id, value):
  with db_transaction() as connection:
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
      raise CustomFieldIsArchivedError()

    _validate_value(
      field,
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

    if value is None:
      if existing is None:
        return True

      old_value = existing["value"]

      connection.execute(
        """
        DELETE FROM inventory_item_fields
        WHERE item_id = ?
          AND field_id = ?
        """,
        (item_id, field_id),
      )

      create_audit_log(
        action="deleted",
        entity_type="custom_field_value",
        entity_id=f"{item_id}:{field_id}",
        details={
          "value": {
            "old": old_value,
            "new": None,
          },
        },
      )

      return True

    serialized_value = _serialize_value(
      field["field_type"],
      value,
    )

    if existing is not None:
      old_value = existing["value"]

      if old_value == serialized_value:
        return True

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
        entity_type="custom_field_value",
        entity_id=f"{item_id}:{field_id}",
        details={
          "value": {
            "old": old_value,
            "new": serialized_value,
          },
        },
      )

      return True

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
      entity_type="custom_field_value",
      entity_id=f"{item_id}:{field_id}",
      details={
        "value": {
          "old": None,
          "new": serialized_value,
        },
      },
    )

    return True


def get_custom_field_value(item_id, field_id):
  with db_connection() as connection:
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


def get_custom_field_values(item_id):
  with db_connection() as connection:
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


def delete_custom_field_value(item_id, field_id):
  with db_transaction() as connection:
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
      SELECT value
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

    old_value = value["value"]

    connection.execute(
      """
      DELETE FROM inventory_item_fields
      WHERE item_id = ?
        AND field_id = ?
      """,
      (item_id, field_id),
    )

    create_audit_log(
      action="deleted",
      entity_type="custom_field_value",
      entity_id=f"{item_id}:{field_id}",
      details={
        "value": {
          "old": old_value,
          "new": None,
        },
      },
    )

    return True

import json

from ..exceptions.data.common import InvalidInputError
from ..exceptions.data.custom_fields import *
from .audit import create_audit_log
from .db import db_connection, db_transaction

_VALID_FIELD_TYPES = {
  "text",
  "integer",
  "decimal",
  "boolean",
  "date",
  "enum",
  "user",
}

_UNSET = object()


def _validate_name(name):
  if not isinstance(name, str) or not name.strip():
    raise InvalidCustomFieldNameError()


def _validate_field_type(field_type):
  if field_type not in _VALID_FIELD_TYPES:
    raise InvalidCustomFieldTypeError()


def _validate_required(required):
  if not isinstance(required, bool):
    raise InvalidCustomFieldRequiredError()


def _validate_enum_values(field_type, enum_values):
  if field_type == "enum":
    if not isinstance(enum_values, list) or not enum_values:
      raise InvalidCustomFieldEnumValuesError("Enum values must be a non-empty list")

    if any(not isinstance(value, str) or not value for value in enum_values):
      raise InvalidCustomFieldEnumValuesError(
        "Enum values must contain only non-empty strings"
      )

    if len(enum_values) != len(set(enum_values)):
      raise InvalidCustomFieldEnumValuesError("Enum values must be unique")
  elif enum_values is not None:
    raise InvalidCustomFieldEnumValuesError(
      "Enum values are only valid for enum fields"
    )


def _deserialize_enum_values(field):
  if field["enum_values"] is None:
    return None

  return json.loads(field["enum_values"])


def create_custom_field(
  name, field_type, description=None, required=False, enum_values=None
):
  _validate_name(name)
  _validate_field_type(field_type)
  _validate_required(required)
  _validate_enum_values(field_type, enum_values)

  with db_transaction() as connection:
    existing = connection.execute(
      """
      SELECT id
      FROM custom_fields
      WHERE name = ?
      """,
      (name,),
    ).fetchone()

    if existing is not None:
      raise CustomFieldAlreadyExistsError()

    serialized_enum_values = (
      json.dumps(enum_values) if enum_values is not None else None
    )

    cursor = connection.execute(
      """
      INSERT INTO custom_fields (
        name,
        field_type,
        description,
        required,
        enum_values
      )
      VALUES (?, ?, ?, ?, ?)
      """,
      (
        name,
        field_type,
        description,
        int(required),
        serialized_enum_values,
      ),
    )

    field_id = cursor.lastrowid

    create_audit_log(
      action="created",
      entity_type="custom_field",
      entity_id=field_id,
    )

    return field_id


def get_custom_field(field_id):
  with db_connection() as connection:
    field = connection.execute(
      """
      SELECT
        id,
        name,
        field_type,
        description,
        required,
        enum_values,
        archived_at
      FROM custom_fields
      WHERE id = ?
      """,
      (field_id,),
    ).fetchone()

    if field is None:
      return None

    field = dict(field)
    field["enum_values"] = _deserialize_enum_values(field)

    return field


def get_custom_fields(include_archived=False):
  with db_connection() as connection:
    query = """
      SELECT
        id,
        name,
        field_type,
        description,
        required,
        enum_values,
        archived_at
      FROM custom_fields
    """

    if not include_archived:
      query += " WHERE archived_at IS NULL"

    query += " ORDER BY name"

    fields = connection.execute(query).fetchall()

    result = []

    for field in fields:
      field = dict(field)
      field["enum_values"] = _deserialize_enum_values(field)
      result.append(field)

    return result


def update_custom_field(
  field_id,
  name=_UNSET,
  field_type=_UNSET,
  description=_UNSET,
  required=_UNSET,
  enum_values=_UNSET,
):
  if all(
    value is _UNSET
    for value in (
      name,
      field_type,
      description,
      required,
      enum_values,
    )
  ):
    raise InvalidInputError("No fields to update")

  if name is not _UNSET:
    _validate_name(name)

  if field_type is not _UNSET:
    _validate_field_type(field_type)

  if required is not _UNSET:
    _validate_required(required)

  with db_transaction() as connection:
    existing = connection.execute(
      """
      SELECT
        id,
        name,
        field_type,
        description,
        required,
        enum_values,
        archived_at
      FROM custom_fields
      WHERE id = ?
      """,
      (field_id,),
    ).fetchone()

    if existing is None:
      raise CustomFieldNotFoundError()

    if existing["archived_at"] is not None:
      raise CustomFieldIsArchivedError()

    existing_enum_values = (
      json.loads(existing["enum_values"])
      if existing["enum_values"] is not None
      else None
    )

    new_field_type = field_type if field_type is not _UNSET else existing["field_type"]

    new_enum_values = enum_values if enum_values is not _UNSET else existing_enum_values

    _validate_enum_values(
      new_field_type,
      new_enum_values,
    )

    updates = []
    values = []
    details = {}

    if name is not _UNSET and existing["name"] != name:
      duplicate = connection.execute(
        """
        SELECT id
        FROM custom_fields
        WHERE name = ?
          AND id != ?
        """,
        (name, field_id),
      ).fetchone()

      if duplicate is not None:
        raise CustomFieldAlreadyExistsError()

      updates.append("name = ?")
      values.append(name)

      details["name"] = {
        "old": existing["name"],
        "new": name,
      }

    if field_type is not _UNSET and existing["field_type"] != field_type:
      value = connection.execute(
        """
        SELECT 1
        FROM inventory_item_fields
        WHERE field_id = ?
        LIMIT 1
        """,
        (field_id,),
      ).fetchone()

      if value is not None:
        raise CustomFieldInUseError()

      if existing["archived_at"] is not None:
        raise CustomFieldIsArchivedError()

      updates.append("field_type = ?")
      values.append(field_type)

      details["field_type"] = {
        "old": existing["field_type"],
        "new": field_type,
      }

    if description is not _UNSET and existing["description"] != description:
      updates.append("description = ?")
      values.append(description)

      details["description"] = {
        "old": existing["description"],
        "new": description,
      }

    if required is not _UNSET and bool(existing["required"]) != required:
      updates.append("required = ?")
      values.append(int(required))

      details["required"] = {
        "old": bool(existing["required"]),
        "new": required,
      }

    if enum_values is not _UNSET and existing_enum_values != enum_values:
      serialized_enum_values = (
        json.dumps(enum_values) if enum_values is not None else None
      )

      updates.append("enum_values = ?")
      values.append(serialized_enum_values)

      details["enum_values"] = {
        "old": existing_enum_values,
        "new": enum_values,
      }

    if not updates:
      return True

    values.append(field_id)

    connection.execute(
      f"""
      UPDATE custom_fields
      SET {", ".join(updates)}
      WHERE id = ?
      """,
      values,
    )

    create_audit_log(
      action="updated",
      entity_type="custom_field",
      entity_id=field_id,
      details=details,
    )

    return True


def archive_custom_field(field_id):
  with db_transaction() as connection:
    existing = connection.execute(
      """
      SELECT id, archived_at
      FROM custom_fields
      WHERE id = ?
      """,
      (field_id,),
    ).fetchone()

    if existing is None:
      raise CustomFieldNotFoundError()

    if existing["archived_at"] is not None:
      raise CustomFieldIsArchivedError()

    connection.execute(
      """
      UPDATE custom_fields
      SET archived_at = CURRENT_TIMESTAMP
      WHERE id = ?
      """,
      (field_id,),
    )

    create_audit_log(
      action="archived",
      entity_type="custom_field",
      entity_id=field_id,
    )

    return True


def restore_custom_field(field_id):
  with db_transaction() as connection:
    existing = connection.execute(
      """
      SELECT
        id,
        name,
        archived_at
      FROM custom_fields
      WHERE id = ?
      """,
      (field_id,),
    ).fetchone()

    if existing is None:
      raise CustomFieldNotFoundError()

    if existing["archived_at"] is None:
      raise CustomFieldIsNotArchivedError()

    duplicate = connection.execute(
      """
      SELECT id
      FROM custom_fields
      WHERE name = ?
        AND id != ?
        AND archived_at IS NULL
      """,
      (existing["name"], field_id),
    ).fetchone()

    if duplicate is not None:
      raise CustomFieldAlreadyExistsError()

    connection.execute(
      """
      UPDATE custom_fields
      SET archived_at = NULL
      WHERE id = ?
      """,
      (field_id,),
    )

    create_audit_log(
      action="unarchived",
      entity_type="custom_field",
      entity_id=field_id,
    )

    return True

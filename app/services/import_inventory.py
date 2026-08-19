import csv
import io
import uuid
from datetime import date

from app.db import get_db
from app.services.audit import create_audit_log
from app.services.authorization import has_permission
from app.services.custom_field_values import set_custom_field_value

_BASE_FIELDS = {
  "id",
  "name",
  "location",
}


def _get_locations(connection):
  rows = connection.execute(
    """
    SELECT id, name
    FROM locations
    ORDER BY id
    """
  ).fetchall()

  return {row["name"]: row["id"] for row in rows}


def _get_custom_fields_by_name(connection):
  rows = connection.execute(
    """
    SELECT id, name, field_type
    FROM custom_fields
    ORDER BY id
    """
  ).fetchall()

  return {row["name"]: row for row in rows}


def _get_existing_item_ids(connection):
  rows = connection.execute(
    """
    SELECT id
    FROM inventory_items
    """
  ).fetchall()

  return {row["id"] for row in rows}


def _parse_csv(content):
  if not isinstance(content, str):
    raise ValueError("Import content must be a string")

  try:
    reader = csv.DictReader(
      io.StringIO(content),
    )

    if reader.fieldnames is None:
      raise ValueError("CSV header is required")

    if not reader.fieldnames:
      raise ValueError("CSV header is required")

    if len(reader.fieldnames) != len(set(reader.fieldnames)):
      raise ValueError("Duplicate CSV fields are not allowed")

    rows = list(reader)

  except csv.Error as error:
    raise ValueError("Invalid CSV") from error

  return reader.fieldnames, rows


def _validate_headers(
  headers,
  custom_fields_by_name,
):
  if "name" not in headers:
    raise ValueError("Missing required field: name")

  known_fields = set(_BASE_FIELDS)
  known_fields.update(custom_fields_by_name)

  invalid_fields = [field for field in headers if field not in known_fields]

  if invalid_fields:
    raise ValueError(f"Invalid import field: {invalid_fields[0]}")


def _validate_custom_field_value(
  field,
  value,
):
  field_type = field["field_type"]

  if field_type == "text":
    return

  if field_type == "integer":
    numeric_value = value[1:] if value.startswith("-") else value

    if not numeric_value.isdigit():
      raise ValueError(f"Invalid integer value for field: {field['name']}")

    return

  if field_type == "decimal":
    try:
      float(value)
    except (TypeError, ValueError) as error:
      raise ValueError(f"Invalid decimal value for field: {field['name']}") from error

    return

  if field_type == "boolean":
    if value not in {
      "0",
      "1",
      "true",
      "false",
      "True",
      "False",
    }:
      raise ValueError(f"Invalid boolean value for field: {field['name']}")

    return

  if field_type == "date":
    try:
      date.fromisoformat(value)
    except ValueError as error:
      raise ValueError(f"Invalid date value for field: {field['name']}") from error

    return

  if field_type in {
    "enum",
    "user",
  }:
    return

  raise ValueError(f"Invalid custom field type: {field_type}")


def _validate_rows(
  user_id,
  rows,
  headers,
  existing_ids,
  locations,
  custom_fields_by_name,
):
  seen_ids = set()
  prepared_rows = []

  for row in rows:
    item_id = row.get(
      "id",
      "",
    ).strip()

    if not item_id:
      item_id = str(uuid.uuid4())

    if item_id in seen_ids:
      raise ValueError(f"Duplicate item id: {item_id}")

    if item_id in existing_ids:
      raise ValueError(f"Inventory item already exists: {item_id}")

    seen_ids.add(item_id)

    name = row.get("name")

    if not isinstance(name, str) or not name.strip():
      raise ValueError("Item name cannot be empty")

    location_name = row.get(
      "location",
      "",
    )

    location_id = None

    if location_name:
      if location_name not in locations:
        raise ValueError(f"Location does not exist: {location_name}")

      location_id = locations[location_name]

    custom_field_values = []

    for field_name in headers:
      field = custom_fields_by_name.get(field_name)

      if field is None:
        continue

      value = row.get(
        field_name,
        "",
      )

      if value == "":
        continue

      if not has_permission(
        user_id,
        f"field.{field['id']}.update",
      ):
        continue

      _validate_custom_field_value(
        field,
        value,
      )

      custom_field_values.append(
        (
          field["id"],
          value,
        )
      )

    prepared_rows.append(
      {
        "id": item_id,
        "name": name,
        "location_id": location_id,
        "custom_field_values": custom_field_values,
      }
    )

  return prepared_rows


def import_inventory(
  user_id,
  content,
):
  if not has_permission(
    user_id,
    "inventory.import",
  ):
    raise PermissionError("Inventory import permission is required")

  connection = get_db()

  try:
    headers, rows = _parse_csv(
      content,
    )

    locations = _get_locations(
      connection,
    )

    custom_fields_by_name = _get_custom_fields_by_name(
      connection,
    )

    _validate_headers(
      headers,
      custom_fields_by_name,
    )

    existing_ids = _get_existing_item_ids(
      connection,
    )

    prepared_rows = _validate_rows(
      user_id,
      rows,
      headers,
      existing_ids,
      locations,
      custom_fields_by_name,
    )

    imported_items = []

    for prepared_row in prepared_rows:
      connection.execute(
        """
        INSERT INTO inventory_items (
          id,
          name,
          location_id,
          created_at,
          updated_at
        )
        VALUES (
          ?,
          ?,
          ?,
          datetime('now'),
          datetime('now')
        )
        """,
        (
          prepared_row["id"],
          prepared_row["name"],
          prepared_row["location_id"],
        ),
      )

      create_audit_log(
        action="created",
        entity_type="inventory_item",
        entity_id=prepared_row["id"],
        connection=connection,
      )

      for field_id, value in prepared_row["custom_field_values"]:
        set_custom_field_value(
          prepared_row["id"],
          field_id,
          value,
          connection=connection,
        )

      imported_items.append(
        {
          "id": prepared_row["id"],
          "name": prepared_row["name"],
          "location_id": prepared_row["location_id"],
        }
      )

    create_audit_log(
      action="created",
      entity_type="inventory_import",
      entity_id="inventory",
      connection=connection,
    )

    connection.commit()

    return imported_items

  except Exception:
    connection.rollback()
    raise

  finally:
    connection.close()

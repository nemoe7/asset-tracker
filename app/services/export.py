import csv
import io

from app.db import get_db
from app.services.audit import create_audit_log
from app.services.authorization import has_permission
from app.services.inventory import get_items


def _get_custom_fields():
  connection = get_db()

  try:
    return connection.execute(
      """
      SELECT id, name
      FROM custom_fields
      ORDER BY id
      """
    ).fetchall()
  finally:
    connection.close()


def _get_locations(location_ids):
  if not location_ids:
    return {}

  connection = get_db()

  try:
    placeholders = ", ".join("?" for _ in location_ids)

    rows = connection.execute(
      f"""
      SELECT id, name
      FROM locations
      WHERE id IN ({placeholders})
      """,
      list(location_ids),
    ).fetchall()

    return {row["id"]: row["name"] for row in rows}
  finally:
    connection.close()


def _get_exportable_custom_fields(
  user_id,
  custom_fields,
):
  return [
    field
    for field in custom_fields
    if has_permission(
      user_id,
      f"field.{field['id']}.read",
    )
  ]


def _get_custom_field_value(item, field_id):
  return item["custom_fields"].get(field_id)


def _validate_requested_fields(
  fields,
  base_fields,
  all_custom_fields,
  exportable_custom_fields,
):
  if not fields:
    raise ValueError("Export field selection cannot be empty")

  if len(fields) != len(set(fields)):
    raise ValueError("Duplicate export fields are not allowed")

  all_available_fields = set(base_fields)

  for field in all_custom_fields:
    all_available_fields.add(field["name"])

  invalid_fields = [field for field in fields if field not in all_available_fields]

  if invalid_fields:
    raise ValueError(f"Invalid export field: {invalid_fields[0]}")

  exportable_fields = set(base_fields)

  for field in exportable_custom_fields:
    exportable_fields.add(field["name"])

  return [field for field in fields if field in exportable_fields]


def export_inventory(
  user_id,
  fields=None,
  search=None,
  location_id=None,
):
  if not has_permission(
    user_id,
    "inventory.export",
  ):
    raise PermissionError("Inventory export permission is required")

  items = get_items(
    search=search,
    location_id=location_id,
  )

  items = sorted(
    items,
    key=lambda item: item["id"],
  )

  all_custom_fields = _get_custom_fields()

  exportable_custom_fields = _get_exportable_custom_fields(
    user_id,
    all_custom_fields,
  )

  base_fields = [
    "id",
    "name",
    "location",
  ]

  if fields is None:
    selected_fields = [
      *base_fields,
    ]
  else:
    selected_fields = _validate_requested_fields(
      fields,
      base_fields,
      all_custom_fields,
      exportable_custom_fields,
    )

  populated_custom_fields = [
    field
    for field in exportable_custom_fields
    if any(
      _get_custom_field_value(
        item,
        field["id"],
      )
      is not None
      for item in items
    )
  ]

  populated_custom_field_by_name = {
    field["name"]: field for field in populated_custom_fields
  }

  exportable_custom_field_by_name = {
    field["name"]: field for field in exportable_custom_fields
  }

  if fields is None:
    selected_fields.extend(populated_custom_field_by_name)

    custom_field_by_name = populated_custom_field_by_name
  else:
    custom_field_by_name = {
      field_name: exportable_custom_field_by_name[field_name]
      for field_name in selected_fields
      if field_name in exportable_custom_field_by_name
    }

  location_ids = {
    item["location_id"] for item in items if item["location_id"] is not None
  }

  locations = _get_locations(
    location_ids,
  )

  output = io.StringIO()

  writer = csv.DictWriter(
    output,
    fieldnames=selected_fields,
  )

  writer.writeheader()

  for item in items:
    row = {}

    if "id" in selected_fields:
      row["id"] = item["id"]

    if "name" in selected_fields:
      row["name"] = item["name"]

    if "location" in selected_fields:
      row["location"] = locations.get(
        item["location_id"],
        "",
      )

    for field_name, field in custom_field_by_name.items():
      value = _get_custom_field_value(
        item,
        field["id"],
      )

      row[field_name] = "" if value is None else str(value)

    writer.writerow(row)

  connection = get_db()

  try:
    create_audit_log(
      action="created",
      entity_type="inventory_export",
      entity_id="inventory",
      connection=connection,
    )

    connection.commit()
  except:
    connection.rollback()
    raise
  finally:
    connection.close()

  return output.getvalue()

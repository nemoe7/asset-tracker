import csv
import io

from .data.audit import create_audit_log
from .data.custom_fields import get_custom_fields
from .data.inventory import get_items
from .exceptions.data.common import InvalidInputError

_BUILTIN_COLUMNS = [
  ("id", lambda item: item["id"]),
  ("name", lambda item: item["name"]),
  ("description", lambda item: item["description"]),
  ("location", lambda item: item["location_name"]),
  ("created_at", lambda item: item["created_at"]),
  ("updated_at", lambda item: item["updated_at"]),
]


def _custom_column(field):
  def get_value(item):
    return item["custom_fields"].get(field["name"])

  return (field["name"], get_value)


def _selected_columns(field_keys):
  custom_columns = [
    _custom_column(field) for field in get_custom_fields()
  ]

  if field_keys is None:
    return _BUILTIN_COLUMNS + custom_columns

  keys = [key.strip() for key in field_keys if key.strip()]

  if not keys:
    raise InvalidInputError("No fields selected")

  if len(keys) != len(set(keys)):
    raise InvalidInputError("Duplicate fields selected")

  available = {key: get_value for key, get_value in _BUILTIN_COLUMNS + custom_columns}

  unknown = [key for key in keys if key not in available]

  if unknown:
    raise InvalidInputError(f"Unknown fields: {', '.join(unknown)}")

  return [(key, available[key]) for key in keys]


_FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def _csv_safe(value):
  if value.startswith(_FORMULA_PREFIXES):
    return f"'{value}"

  return value


def _cell(value):
  if value is None:
    return ""

  return _csv_safe(str(value))


def build_export(
  search=None,
  location_id=None,
  include_archived=False,
  sort_by="name",
  sort_order="asc",
  custom_field_filters=None,
  field_keys=None,
):
  columns = _selected_columns(field_keys)

  items = get_items(
    search=search,
    location_id=location_id,
    include_archived=include_archived,
    sort_by=sort_by,
    sort_order=sort_order,
    custom_field_filters=custom_field_filters,
  )

  output = io.StringIO()
  writer = csv.writer(output)

  writer.writerow([key for key, _ in columns])

  for item in items:
    writer.writerow([_cell(get_value(item)) for _, get_value in columns])

  create_audit_log(
    action="exported",
    entity_type="inventory",
    entity_id="export",
    details={
      "item_count": len(items),
      "fields": [key for key, _ in columns],
    },
  )

  return output.getvalue()

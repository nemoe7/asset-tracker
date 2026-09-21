import csv
import io
import re

from .data.audit import create_audit_log
from .data.custom_fields import get_custom_fields
from .data.inventory import get_items
from .data.users import get_users
from .exceptions.data.common import InvalidInputError

_BUILTIN_COLUMNS = [
  ("id", lambda item: item["id"]),
  ("name", lambda item: item["name"]),
  ("description", lambda item: item["description"]),
  ("location", lambda item: item["location_name"]),
  ("created_at", lambda item: item["created_at"]),
  ("updated_at", lambda item: item["updated_at"]),
  ("archival_reason", lambda item: item["archival_reason"]),
  ("archival_notes", lambda item: item["archival_notes"]),
]


def _custom_column(field, users_by_id=None):
  def get_value(item):
    value = item["custom_fields"].get(field["name"])

    if field["field_type"] == "user" and value is not None and users_by_id is not None:
      user = users_by_id.get(str(value))

      if user is not None:
        return user["name"] or user["username"]

    return value

  return (field["name"], get_value)


def _selected_columns(field_keys, visible_field_ids=None, users_by_id=None):
  custom_columns = [
    _custom_column(field, users_by_id)
    for field in get_custom_fields()
    if visible_field_ids is None or field["id"] in visible_field_ids
  ]

  if field_keys is None:
    return _BUILTIN_COLUMNS + custom_columns

  keys = [key.strip() for key in field_keys if key.strip()]

  if not keys:
    raise InvalidInputError("No fields selected")

  # Builtin-wins on case-insensitive collision: a custom field literally
  # named "Name" can coexist with the builtin "name" under BINARY unique.
  get_value_by_lower = {key.lower(): get_value for key, get_value in custom_columns}
  get_value_by_lower.update(
    {key.lower(): get_value for key, get_value in _BUILTIN_COLUMNS}
  )
  key_by_lower = {key.lower(): key for key, _ in custom_columns}
  key_by_lower.update({key.lower(): key for key, _ in _BUILTIN_COLUMNS})

  unknown = [key for key in keys if key.lower() not in key_by_lower]

  if unknown:
    raise InvalidInputError(f"Unknown fields: {', '.join(unknown)}")

  # Resolve to canonical key so duplicate detection is case-insensitive.
  canonical = [key_by_lower[key.lower()] for key in keys]

  if len(canonical) != len(set(canonical)):
    raise InvalidInputError("Duplicate fields selected")

  return [(key, get_value_by_lower[key.lower()]) for key in canonical]


_FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")

# Plain integers/decimals (including negative) are exempt from the
# formula-prefix defense so "-5" is not mangled into "'-5".
_PLAIN_NUMERIC = re.compile(r"-?\d+(?:\.\d+)?")


def _csv_safe(value):
  if value.startswith(_FORMULA_PREFIXES) and not _PLAIN_NUMERIC.fullmatch(value):
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
  visible_field_ids=None,
):
  # User-type columns resolve IDs to display names; archived users included
  # so existing references still export meaningfully. Missing users export raw.
  users_by_id = {str(user["id"]): user for user in get_users(include_archived=True)}

  columns = _selected_columns(field_keys, visible_field_ids, users_by_id)

  items = get_items(
    search=search,
    location_id=location_id,
    include_archived=include_archived,
    sort_by=sort_by,
    sort_order=sort_order,
    custom_field_filters=custom_field_filters,
    visible_field_ids=visible_field_ids,
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

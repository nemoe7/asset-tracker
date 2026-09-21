from datetime import date

from ..exceptions.data.common import InvalidInputError

# Sentinel filter value matching items with no stored value for the field.
EMPTY_FILTER_VALUE = "__empty__"

_FIELD_OPERATORS = {
  "integer": [
    ("=", "="),
    ("!=", "!="),
    ("<", "<"),
    ("<=", "<="),
    (">", ">"),
    (">=", ">="),
  ],
  "decimal": [
    ("=", "="),
    ("!=", "!="),
    ("<", "<"),
    ("<=", "<="),
    (">", ">"),
    (">=", ">="),
  ],
  "date": [
    ("=", "On"),
    ("!=", "Not on"),
    ("<", "Before"),
    ("<=", "Until"),
    (">", "After"),
    (">=", "Since"),
  ],
  "expiry_date": [
    ("is", "Is"),
    ("before", "Before"),
    ("expires_in", "Expires in"),
  ],
  "enum": [
    ("=", "Is"),
    ("!=", "Is not"),
  ],
  "user": [
    ("=", "Is"),
    ("!=", "Is not"),
    ("~", "Matches"),
  ],
  "boolean": [],
  "text": [
    ("contains", "Contains"),
    ("excludes", "Excludes"),
  ],
}

_TEXT_OPS = {"contains", "excludes", "contains_cs", "excludes_cs"}


def get_operators(field_type):
  operators = _FIELD_OPERATORS.get(field_type)

  if operators is None:
    raise InvalidInputError("Unknown custom field type")

  return [tuple(operator) for operator in operators]


def _validate_operator(field, op):
  # "—" filters items with no stored value; valid for every field type.
  if op == EMPTY_FILTER_VALUE:
    return op

  field_type = field["field_type"]

  if field_type == "boolean":
    if op not in ("", "="):
      raise InvalidInputError("Invalid operator for boolean field")

    return "="

  if field_type == "text":
    if op not in _TEXT_OPS:
      raise InvalidInputError("Invalid operator for text field")

    return op

  valid_ops = {op for op, _label in _FIELD_OPERATORS[field_type]}

  if op not in valid_ops:
    raise InvalidInputError("Invalid operator for field type")

  return op


def _resolve_user_value(value):
  from .users import get_user_by_username, get_users

  user = get_user_by_username(value)

  if user is not None:
    return str(user["id"])

  # "≈" substring match: all active users whose username or name contains
  # the input; empty result is an unknown-user error.
  matches = [
    user
    for user in get_users()
    if value.lower() in user["username"].lower()
    or (user["name"] and value.lower() in user["name"].lower())
  ]

  if not matches:
    raise InvalidInputError(f"User '{value}' does not exist")

  return ",".join(str(user["id"]) for user in matches)


def _validate_value(field, raw_value, op=None):
  field_type = field["field_type"]
  value = str(raw_value)

  if value == EMPTY_FILTER_VALUE:
    return value

  if field_type in ("integer", "decimal"):
    try:
      return int(value) if field_type == "integer" else float(value)
    except ValueError:
      raise InvalidInputError(f"Invalid value for {field_type} field")

  if field_type == "date":
    try:
      date.fromisoformat(value)
    except ValueError:
      raise InvalidInputError("Invalid date value")

    return value

  if field_type == "expiry_date":
    if op == "is":
      if value not in ("expired", "not expired"):
        raise InvalidInputError("Invalid value for expiry date 'is' filter")
      return value
    elif op == "expires_in":
      try:
        val = int(value)
        if val < 0:
          raise ValueError()
        return val
      except ValueError:
        raise InvalidInputError("Invalid integer value for 'expires_in'")
    elif op == "before":
      try:
        date.fromisoformat(value)
      except ValueError:
        raise InvalidInputError("Invalid date value")
      return value

  if field_type == "boolean":
    if value not in ("true", "false"):
      raise InvalidInputError("Invalid boolean value")

    return value

  if field_type == "enum":
    if value not in field["enum_values"]:
      raise InvalidInputError("Value not allowed for enum field")

    return value

  if field_type == "user":
    return _resolve_user_value(value)

  return value


def parse_filters(f_fields, f_ops, f_values, fields):
  if not (len(f_fields) == len(f_ops) == len(f_values)):
    raise InvalidInputError("Malformed filter parameters")

  fields_by_id = {field["id"]: field for field in fields}

  filters = []

  for field_id, op, raw_value in zip(f_fields, f_ops, f_values):
    key = int(field_id) if str(field_id).isdigit() else field_id
    field = fields_by_id.get(key)

    if field is None:
      raise InvalidInputError("Unknown custom field in filter")

    validated_op = _validate_operator(field, op)

    validated_value = (
      EMPTY_FILTER_VALUE
      if validated_op == EMPTY_FILTER_VALUE
      else _validate_value(field, raw_value, validated_op)
    )

    filters.append((field["id"], validated_op, validated_value))

  return filters

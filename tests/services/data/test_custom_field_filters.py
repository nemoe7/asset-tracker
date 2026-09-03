import pytest

from app.services.data.custom_field_filters import (
  get_operators,
  parse_filters,
)
from app.services.data.custom_fields import (
  create_custom_field,
  get_custom_field,
)
from app.services.exceptions.data.common import InvalidInputError


def _create_field(name, field_type, **kwargs):
  field_id = create_custom_field(name, field_type, **kwargs)

  return get_custom_field(field_id)


@pytest.fixture
def integer_field(gen_test_data_admin):
  return _create_field("Quantity", "integer")


@pytest.fixture
def decimal_field(gen_test_data_admin):
  return _create_field("Price", "decimal")


@pytest.fixture
def date_field(gen_test_data_admin):
  return _create_field("Purchased", "date")


@pytest.fixture
def enum_field(gen_test_data_admin):
  return _create_field(
    "Category",
    "enum",
    enum_values=["Electronics", "Furniture"],
  )


@pytest.fixture
def boolean_field(gen_test_data_admin):
  return _create_field("Active", "boolean")


@pytest.fixture
def text_field(gen_test_data_admin):
  return _create_field("Serial", "text")


@pytest.fixture
def fields(
  integer_field,
  decimal_field,
  date_field,
  enum_field,
  boolean_field,
  text_field,
):
  return {
    "integer": integer_field,
    "decimal": decimal_field,
    "date": date_field,
    "enum": enum_field,
    "boolean": boolean_field,
    "text": text_field,
  }


# --- parse_filters: valid parsing -------------------------------------------


def test_parse_filters_parses_valid_integer_filter(fields, integer_field):
  filters = parse_filters(
    [str(integer_field["id"])],
    ["="],
    ["5"],
    list(fields.values()),
  )

  assert filters == [(integer_field["id"], "=", 5)]


def test_parse_filters_returns_list_for_multiple_filters(
  fields,
  integer_field,
  text_field,
):
  filters = parse_filters(
    [str(integer_field["id"]), str(text_field["id"])],
    ["<", "contains"],
    ["10", "abc"],
    list(fields.values()),
  )

  assert filters == [
    (integer_field["id"], "<", 10),
    (text_field["id"], "contains", "abc"),
  ]


def test_parse_filters_converts_decimal_value(fields, decimal_field):
  filters = parse_filters(
    [str(decimal_field["id"])],
    [">="],
    ["1.5"],
    list(fields.values()),
  )

  assert filters == [(decimal_field["id"], ">=", 1.5)]


def test_parse_filters_keeps_date_and_enum_values_as_strings(
  fields,
  date_field,
  enum_field,
):
  filters = parse_filters(
    [str(date_field["id"]), str(enum_field["id"])],
    [">", "="],
    ["2024-01-31", "Electronics"],
    list(fields.values()),
  )

  assert filters == [
    (date_field["id"], ">", "2024-01-31"),
    (enum_field["id"], "=", "Electronics"),
  ]


def test_parse_filters_accepts_text_case_tokens(fields, text_field):
  filters = parse_filters(
    [str(text_field["id"]), str(text_field["id"])],
    ["excludes", "contains_cs"],
    ["foo", "Bar"],
    list(fields.values()),
  )

  assert filters == [
    (text_field["id"], "excludes", "foo"),
    (text_field["id"], "contains_cs", "Bar"),
  ]


# --- parse_filters: invalid input -------------------------------------------


def test_parse_filters_rejects_unknown_field_id(fields):
  with pytest.raises(InvalidInputError):
    parse_filters(["9999"], ["="], ["5"], list(fields.values()))


def test_parse_filters_rejects_invalid_operator(fields, integer_field):
  with pytest.raises(InvalidInputError):
    parse_filters(
      [str(integer_field["id"])],
      ["contains"],
      ["5"],
      list(fields.values()),
    )


def test_parse_filters_rejects_mismatched_triplet_lengths(
  fields,
  integer_field,
):
  with pytest.raises(InvalidInputError):
    parse_filters(
      [str(integer_field["id"]), str(integer_field["id"])],
      ["="],
      ["5"],
      list(fields.values()),
    )


@pytest.mark.parametrize("value", ["abc", "1.5", ""])
def test_parse_filters_rejects_non_integer_value(
  fields,
  integer_field,
  value,
):
  with pytest.raises(InvalidInputError):
    parse_filters(
      [str(integer_field["id"])],
      ["="],
      [value],
      list(fields.values()),
    )


def test_parse_filters_rejects_non_decimal_value(fields, decimal_field):
  with pytest.raises(InvalidInputError):
    parse_filters(
      [str(decimal_field["id"])],
      ["="],
      ["abc"],
      list(fields.values()),
    )


def test_parse_filters_rejects_invalid_date_value(fields, date_field):
  with pytest.raises(InvalidInputError):
    parse_filters(
      [str(date_field["id"])],
      ["="],
      ["not-a-date"],
      list(fields.values()),
    )


def test_parse_filters_rejects_enum_value_not_in_enum_values(
  fields,
  enum_field,
):
  with pytest.raises(InvalidInputError):
    parse_filters(
      [str(enum_field["id"])],
      ["="],
      ["Toys"],
      list(fields.values()),
    )


@pytest.mark.parametrize("value", ["yes", "1", ""])
def test_parse_filters_rejects_invalid_boolean_value(
  fields,
  boolean_field,
  value,
):
  with pytest.raises(InvalidInputError):
    parse_filters(
      [str(boolean_field["id"])],
      ["="],
      [value],
      list(fields.values()),
    )


def test_parse_filters_rejects_operator_on_boolean_field(
  fields,
  boolean_field,
):
  with pytest.raises(InvalidInputError):
    parse_filters(
      [str(boolean_field["id"])],
      ["!="],
      ["true"],
      list(fields.values()),
    )


def test_parse_filters_rejects_user_type_field(gen_test_data_admin):
  user_field = create_custom_field("Assignee", "user")

  with pytest.raises(InvalidInputError):
    parse_filters(
      [str(user_field)],
      ["="],
      ["1"],
      [{"id": user_field, "field_type": "user"}],
    )


# --- get_operators -----------------------------------------------------------


def test_get_operators_numeric_uses_symbols():
  assert get_operators("integer") == [
    ("=", "="),
    ("!=", "!="),
    ("<", "<"),
    ("<=", "<="),
    (">", ">"),
    (">=", ">="),
  ]
  assert get_operators("decimal") == get_operators("integer")


def test_get_operators_date_uses_worded_labels():
  assert get_operators("date") == [
    ("=", "On"),
    ("!=", "Not on"),
    ("<", "Before"),
    ("<=", "No later than"),
    (">", "After"),
    (">=", "No earlier than"),
  ]


def test_get_operators_enum_uses_is_labels():
  assert get_operators("enum") == [("=", "Is"), ("!=", "Is not")]


def test_get_operators_boolean_has_no_operators():
  assert get_operators("boolean") == []


def test_get_operators_text_uses_contains_excludes():
  assert get_operators("text") == [
    ("contains", "Contains"),
    ("excludes", "Excludes"),
  ]


def test_get_operators_rejects_unknown_type():
  with pytest.raises(InvalidInputError):
    get_operators("user")

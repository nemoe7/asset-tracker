import pytest

from app.services.data.custom_field_filters import parse_filters
from app.services.data.custom_field_values import set_custom_field_value
from app.services.data.custom_fields import (
  create_custom_field,
  get_custom_field,
)
from app.services.data.inventory import create_item, get_items, get_items_paginated


def _create_field(name, field_type, **kwargs):
  field_id = create_custom_field(name, field_type, **kwargs)

  return get_custom_field(field_id)


@pytest.fixture
def integer_field(gen_test_data_admin):
  return _create_field("Quantity", "integer")


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


def _make_item(name, field, value):
  item_id = create_item(name)

  set_custom_field_value(
    item_id,
    field["id"],
    value,
  )

  return item_id


def _filter(fields, f_fields, f_ops, f_values):
  return parse_filters(f_fields, f_ops, f_values, fields)


def _ids(items):
  return {item["id"] for item in items}


def test_get_items_integer_equals_and_less_than(integer_field):
  low = _make_item("Low", integer_field, 5)
  _make_item("High", integer_field, 10)
  create_item("None")

  filters = _filter(
    [integer_field],
    [str(integer_field["id"])],
    ["="],
    ["5"],
  )
  items = get_items(custom_field_filters=filters)
  assert _ids(items) == {low}

  filters = _filter(
    [integer_field],
    [str(integer_field["id"])],
    ["<"],
    ["10"],
  )
  items = get_items(custom_field_filters=filters)
  assert _ids(items) == {low}


def test_get_items_integer_not_equals_matches_missing_value(integer_field):
  _make_item("Low", integer_field, 5)
  other = _make_item("Other", integer_field, 7)
  none_id = create_item("None")

  filters = _filter(
    [integer_field],
    [str(integer_field["id"])],
    ["!="],
    ["5"],
  )
  items = get_items(custom_field_filters=filters)
  assert _ids(items) == {other, none_id}


def test_get_items_date_comparison(date_field):
  old = _make_item("Old", date_field, "2023-01-15")
  new = _make_item("New", date_field, "2024-06-01")

  filters = _filter(
    [date_field],
    [str(date_field["id"])],
    ["<"],
    ["2024-01-01"],
  )
  items = get_items(custom_field_filters=filters)
  assert _ids(items) == {old}

  filters = _filter(
    [date_field],
    [str(date_field["id"])],
    [">="],
    ["2024-01-01"],
  )
  items = get_items(custom_field_filters=filters)
  assert _ids(items) == {new}


def test_get_items_enum_equals_and_not_equals(enum_field):
  electronics = _make_item("Lamp", enum_field, "Electronics")
  furniture = _make_item("Chair", enum_field, "Furniture")
  none_id = create_item("Bare")

  filters = _filter(
    [enum_field],
    [str(enum_field["id"])],
    ["="],
    ["Electronics"],
  )
  items = get_items(custom_field_filters=filters)
  assert _ids(items) == {electronics}

  filters = _filter(
    [enum_field],
    [str(enum_field["id"])],
    ["!="],
    ["Electronics"],
  )
  items = get_items(custom_field_filters=filters)
  assert _ids(items) == {furniture, none_id}


def test_get_items_boolean_equals(boolean_field):
  active = _make_item("Active", boolean_field, True)
  inactive = _make_item("Inactive", boolean_field, False)

  filters = _filter(
    [boolean_field],
    [str(boolean_field["id"])],
    [""],
    ["true"],
  )
  items = get_items(custom_field_filters=filters)
  assert _ids(items) == {active}

  filters = _filter(
    [boolean_field],
    [str(boolean_field["id"])],
    [""],
    ["false"],
  )
  items = get_items(custom_field_filters=filters)
  assert _ids(items) == {inactive}


def test_get_items_text_contains_and_excludes_case_insensitive(text_field):
  needle = _make_item("Has Needle", text_field, "has NEEDLE inside")
  other = _make_item("Other", text_field, "nothing here")
  empty = create_item("Empty")

  filters = _filter(
    [text_field],
    [str(text_field["id"])],
    ["contains"],
    ["needle"],
  )
  items = get_items(custom_field_filters=filters)
  assert _ids(items) == {needle}

  filters = _filter(
    [text_field],
    [str(text_field["id"])],
    ["excludes"],
    ["needle"],
  )
  items = get_items(custom_field_filters=filters)
  assert _ids(items) == {other, empty}


def test_get_items_text_case_sensitive_variants(text_field):
  upper = _make_item("Upper", text_field, "Has NEEDLE inside")
  lower = _make_item("Lower", text_field, "has needle inside")

  filters = _filter(
    [text_field],
    [str(text_field["id"])],
    ["contains_cs"],
    ["NEEDLE"],
  )
  items = get_items(custom_field_filters=filters)
  assert _ids(items) == {upper}

  filters = _filter(
    [text_field],
    [str(text_field["id"])],
    ["excludes_cs"],
    ["NEEDLE"],
  )
  items = get_items(custom_field_filters=filters)
  assert _ids(items) == {lower}


def test_get_items_multiple_fields_and(integer_field, text_field):
  match_id = create_item("Match")

  set_custom_field_value(match_id, integer_field["id"], 5)
  set_custom_field_value(match_id, text_field["id"], "starts abc here")

  wrong_text_id = create_item("Wrong text")

  set_custom_field_value(wrong_text_id, integer_field["id"], 5)
  set_custom_field_value(wrong_text_id, text_field["id"], "no match")

  wrong_number_id = create_item("Wrong number")

  set_custom_field_value(wrong_number_id, text_field["id"], "starts abc here")

  filters = _filter(
    [integer_field, text_field],
    [str(integer_field["id"]), str(text_field["id"])],
    ["=", "contains"],
    ["5", "abc"],
  )
  items = get_items(custom_field_filters=filters)
  assert _ids(items) == {match_id}


def test_get_items_same_field_equality_rows_or(integer_field):
  five = _make_item("Five", integer_field, 5)
  ten = _make_item("Ten", integer_field, 10)
  _make_item("Fifteen", integer_field, 15)

  filters = _filter(
    [integer_field, integer_field],
    [str(integer_field["id"]), str(integer_field["id"])],
    ["=", "="],
    ["5", "10"],
  )
  items = get_items(custom_field_filters=filters)
  assert _ids(items) == {five, ten}


def test_get_items_same_field_ordering_rows_and_range(integer_field):
  five = _make_item("Five", integer_field, 5)
  ten = _make_item("Ten", integer_field, 10)
  twenty = _make_item("Twenty", integer_field, 20)

  filters = _filter(
    [integer_field, integer_field],
    [str(integer_field["id"]), str(integer_field["id"])],
    [">=", "<="],
    ["5", "10"],
  )
  items = get_items(custom_field_filters=filters)
  assert _ids(items) == {five, ten}


def test_get_items_same_field_negatives_and(text_field):
  neither = _make_item("Neither", text_field, "clean")
  _make_item("HasX", text_field, "contains X here")
  _make_item("HasY", text_field, "contains Y here")

  filters = _filter(
    [text_field, text_field],
    [str(text_field["id"]), str(text_field["id"])],
    ["excludes", "excludes"],
    ["X", "Y"],
  )
  items = get_items(custom_field_filters=filters)
  assert _ids(items) == {neither}


def test_get_items_paginated_applies_filters_and_totals(integer_field):
  _make_item("Five", integer_field, 5)
  _make_item("Ten", integer_field, 10)
  create_item("None")

  filters = _filter(
    [integer_field],
    [str(integer_field["id"])],
    ["!="],
    ["5"],
  )
  result = get_items_paginated(
    custom_field_filters=filters,
    page=1,
    per_page=25,
  )

  assert result["total"] == 2
  assert result["total_pages"] == 1
  assert _ids(result["items"]) == {
    item["id"] for item in get_items(custom_field_filters=filters)
  }

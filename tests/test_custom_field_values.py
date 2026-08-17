import json
from decimal import Decimal

import pytest

from app.services.audit import get_audit_logs
from app.services.custom_field_values import (
  clear_custom_field_value,
  get_custom_field_value,
  set_custom_field_value,
)
from app.services.custom_fields import create_custom_field
from app.services.inventory import create_item


def test_set_custom_field_value(test_db, authenticated_test_user):
  item_id = create_item(
    name="Laptop",
  )

  field_id = create_custom_field(
    name="Serial Number",
    field_type="text",
  )

  set_custom_field_value(
    item_id,
    field_id,
    "ABC123",
  )

  assert (
    get_custom_field_value(
      item_id,
      field_id,
    )
    == "ABC123"
  )


def test_get_missing_custom_field_value_returns_none(test_db, authenticated_test_user):
  item_id = create_item(
    name="Laptop",
  )

  field_id = create_custom_field(
    name="Serial Number",
    field_type="text",
  )

  assert (
    get_custom_field_value(
      item_id,
      field_id,
    )
    is None
  )


def test_update_custom_field_value(test_db, authenticated_test_user):
  item_id = create_item(
    name="Laptop",
  )

  field_id = create_custom_field(
    name="Serial Number",
    field_type="text",
  )

  set_custom_field_value(item_id, field_id, "ABC123")
  set_custom_field_value(item_id, field_id, "XYZ789")

  assert (
    get_custom_field_value(
      item_id,
      field_id,
    )
    == "XYZ789"
  )


def test_clear_custom_field_value(test_db, authenticated_test_user):
  item_id = create_item(
    name="Laptop",
  )

  field_id = create_custom_field(
    name="Serial Number",
    field_type="text",
  )

  set_custom_field_value(item_id, field_id, "ABC123")
  clear_custom_field_value(item_id, field_id)

  assert (
    get_custom_field_value(
      item_id,
      field_id,
    )
    is None
  )


def test_clear_missing_custom_field_value_returns_false(
  test_db, authenticated_test_user
):
  item_id = create_item(
    name="Laptop",
  )

  field_id = create_custom_field(
    name="Serial Number",
    field_type="text",
  )

  assert (
    clear_custom_field_value(
      item_id,
      field_id,
    )
    is False
  )


def test_item_can_have_multiple_custom_field_values(test_db, authenticated_test_user):
  item_id = create_item(
    name="Laptop",
  )

  serial_field = create_custom_field(
    name="Serial Number",
    field_type="text",
  )

  year_field = create_custom_field(
    name="Purchase Year",
    field_type="integer",
  )

  set_custom_field_value(
    item_id,
    serial_field,
    "ABC123",
  )

  set_custom_field_value(
    item_id,
    year_field,
    2026,
  )

  assert (
    get_custom_field_value(
      item_id,
      serial_field,
    )
    == "ABC123"
  )

  assert (
    get_custom_field_value(
      item_id,
      year_field,
    )
    == 2026
  )


def test_multiple_items_can_use_same_custom_field(test_db, authenticated_test_user):
  first_item_id = create_item(
    name="Laptop",
  )

  second_item_id = create_item(
    name="Desktop",
  )

  field_id = create_custom_field(
    name="Serial Number",
    field_type="text",
  )

  set_custom_field_value(
    first_item_id,
    field_id,
    "ABC123",
  )

  set_custom_field_value(
    second_item_id,
    field_id,
    "XYZ789",
  )

  assert (
    get_custom_field_value(
      first_item_id,
      field_id,
    )
    == "ABC123"
  )

  assert (
    get_custom_field_value(
      second_item_id,
      field_id,
    )
    == "XYZ789"
  )


@pytest.mark.parametrize(
  "field_type,value,expected",
  [
    ("text", "ABC123", "ABC123"),
    ("integer", 123, 123),
    ("decimal", Decimal("12.50"), Decimal("12.50")),
    ("boolean", True, True),
    ("date", "2026-08-16", "2026-08-16"),
  ],
)
def test_custom_field_value_types(
  test_db,
  authenticated_test_user,
  field_type,
  value,
  expected,
):
  item_id = create_item(
    name="Laptop",
  )

  field_id = create_custom_field(
    name=f"Test {field_type}",
    field_type=field_type,
  )

  set_custom_field_value(
    item_id,
    field_id,
    value,
  )

  assert (
    get_custom_field_value(
      item_id,
      field_id,
    )
    == expected
  )


@pytest.mark.parametrize(
  "value",
  [
    Decimal("0.01"),
    Decimal("12.50"),
    Decimal("1000.00"),
    Decimal("123456789.123456"),
  ],
)
def test_decimal_values_preserve_precision(
  test_db,
  authenticated_test_user,
  value,
):
  item_id = create_item(
    name="Laptop",
  )

  field_id = create_custom_field(
    name="Purchase Price",
    field_type="decimal",
  )

  set_custom_field_value(
    item_id,
    field_id,
    value,
  )

  assert (
    get_custom_field_value(
      item_id,
      field_id,
    )
    == value
  )


def test_invalid_integer_value_is_rejected(test_db, authenticated_test_user):
  item_id = create_item(
    name="Laptop",
  )

  field_id = create_custom_field(
    name="Purchase Year",
    field_type="integer",
  )

  with pytest.raises(ValueError):
    set_custom_field_value(
      item_id,
      field_id,
      "not an integer",
    )


def test_invalid_decimal_value_is_rejected(test_db, authenticated_test_user):
  item_id = create_item(
    name="Laptop",
  )

  field_id = create_custom_field(
    name="Purchase Price",
    field_type="decimal",
  )

  with pytest.raises(ValueError):
    set_custom_field_value(
      item_id,
      field_id,
      "not a decimal",
    )


def test_invalid_boolean_value_is_rejected(test_db, authenticated_test_user):
  item_id = create_item(
    name="Laptop",
  )

  field_id = create_custom_field(
    name="Loaner",
    field_type="boolean",
  )

  with pytest.raises(ValueError):
    set_custom_field_value(
      item_id,
      field_id,
      "maybe",
    )


def test_invalid_date_value_is_rejected(test_db, authenticated_test_user):
  item_id = create_item(
    name="Laptop",
  )

  field_id = create_custom_field(
    name="Purchase Date",
    field_type="date",
  )

  with pytest.raises(ValueError):
    set_custom_field_value(
      item_id,
      field_id,
      "not a date",
    )


def test_set_custom_field_value_creates_audit(test_db, authenticated_test_user):
  item_id = create_item(
    name="Laptop",
  )

  field_id = create_custom_field(
    name="Serial Number",
    field_type="text",
  )

  set_custom_field_value(
    item_id,
    field_id,
    "ABC123",
  )

  logs = get_audit_logs(
    entity_type="inventory_item_field",
    entity_id=f"{item_id}:{field_id}",
  )

  assert len(logs) == 1
  assert logs[0]["action"] == "created"


def test_update_custom_field_value_creates_audit(test_db, authenticated_test_user):
  item_id = create_item(
    name="Laptop",
  )

  field_id = create_custom_field(
    name="Serial Number",
    field_type="text",
  )

  set_custom_field_value(item_id, field_id, "ABC123")
  set_custom_field_value(item_id, field_id, "XYZ789")

  logs = get_audit_logs(
    entity_type="inventory_item_field",
    entity_id=f"{item_id}:{field_id}",
  )

  assert len(logs) == 2
  assert logs[1]["action"] == "updated"

  details = json.loads(logs[1]["details"])

  assert details == {
    "value": {
      "old": "ABC123",
      "new": "XYZ789",
    },
  }


def test_clear_custom_field_value_creates_audit(test_db, authenticated_test_user):
  item_id = create_item(
    name="Laptop",
  )

  field_id = create_custom_field(
    name="Serial Number",
    field_type="text",
  )

  set_custom_field_value(
    item_id,
    field_id,
    "ABC123",
  )

  clear_custom_field_value(
    item_id,
    field_id,
  )

  logs = get_audit_logs(
    entity_type="inventory_item_field",
    entity_id=f"{item_id}:{field_id}",
  )

  assert len(logs) == 2
  assert logs[1]["action"] == "cleared"

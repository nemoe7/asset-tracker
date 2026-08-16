import json
from pathlib import Path

import pytest

import config
from app.db import init_db
from app.services.audit import get_audit_logs
from app.services.custom_field_values import (
  clear_custom_field_value,
  get_custom_field_value,
  set_custom_field_value,
)
from app.services.custom_fields import (
  CustomFieldInUseError,
  create_custom_field,
  delete_custom_field,
  get_custom_field,
  get_custom_fields,
  update_custom_field,
)
from app.services.inventory import create_item


@pytest.fixture
def test_db(tmp_path, monkeypatch):
  db_path = tmp_path / "test.db"
  monkeypatch.setattr(config, "DB_PATH", Path(db_path))

  init_db()

  return db_path


def test_create_custom_field(test_db):
  field_id = create_custom_field(
    name="Serial Number",
    field_type="text",
    description="Asset serial number",
  )

  assert field_id is not None

  field = get_custom_field(field_id)

  assert field["id"] == field_id
  assert field["name"] == "Serial Number"
  assert field["field_type"] == "text"
  assert field["description"] == "Asset serial number"


def test_create_custom_field_without_description(test_db):
  field_id = create_custom_field(
    name="Serial Number",
    field_type="text",
  )

  field = get_custom_field(field_id)

  assert field["description"] is None


def test_create_custom_field_with_invalid_type(test_db):
  with pytest.raises(ValueError):
    create_custom_field(
      name="Serial Number",
      field_type="invalid",
    )


def test_create_custom_field_with_empty_name(test_db):
  with pytest.raises(ValueError):
    create_custom_field(
      name="",
      field_type="text",
    )


def test_get_custom_field(test_db):
  field_id = create_custom_field(
    name="Serial Number",
    field_type="text",
  )

  result = get_custom_field(field_id)

  assert result["id"] == field_id
  assert result["name"] == "Serial Number"


def test_get_nonexistent_custom_field(test_db):
  assert get_custom_field(999) is None


def test_get_custom_fields(test_db):
  create_custom_field(
    name="Serial Number",
    field_type="text",
  )

  create_custom_field(
    name="Purchase Year",
    field_type="integer",
  )

  fields = get_custom_fields()

  assert len(fields) == 2
  assert fields[0]["name"] == "Purchase Year"
  assert fields[1]["name"] == "Serial Number"


def test_update_custom_field(test_db):
  field_id = create_custom_field(
    name="Serial Number",
    field_type="text",
    description="Asset serial number",
  )

  updated = update_custom_field(
    field_id,
    name="Asset Serial",
    field_type="text",
    description="Unique asset identifier",
  )

  assert updated is True

  field = get_custom_field(field_id)

  assert field["name"] == "Asset Serial"
  assert field["field_type"] == "text"
  assert field["description"] == "Unique asset identifier"


def test_update_custom_field_type(test_db):
  field_id = create_custom_field(
    name="Purchase Value",
    field_type="integer",
  )

  updated = update_custom_field(
    field_id,
    field_type="decimal",
  )

  assert updated is True

  field = get_custom_field(field_id)

  assert field["field_type"] == "decimal"


def test_update_custom_field_description_to_none(test_db):
  field_id = create_custom_field(
    name="Serial Number",
    field_type="text",
    description="Asset serial number",
  )

  updated = update_custom_field(
    field_id,
    description=None,
  )

  assert updated is True

  field = get_custom_field(field_id)

  assert field["description"] is None


def test_update_custom_field_without_changes_does_not_create_audit(
  test_db,
):
  field_id = create_custom_field(
    name="Serial Number",
    field_type="text",
    description="Asset serial number",
  )

  updated = update_custom_field(
    field_id,
    name="Serial Number",
    field_type="text",
    description="Asset serial number",
  )

  assert updated is True

  logs = get_audit_logs(
    entity_type="custom_field",
    entity_id=field_id,
  )

  assert len(logs) == 1
  assert logs[0]["action"] == "created"


def test_update_nonexistent_custom_field(test_db):
  result = update_custom_field(
    999,
    name="Serial Number",
  )

  assert result is False


def test_update_custom_field_with_invalid_type(test_db):
  field_id = create_custom_field(
    name="Serial Number",
    field_type="text",
  )

  with pytest.raises(ValueError):
    update_custom_field(
      field_id,
      field_type="invalid",
    )


def test_update_custom_field_audit_records_name_change(test_db):
  field_id = create_custom_field(
    name="Serial Number",
    field_type="text",
  )

  update_custom_field(
    field_id,
    name="Asset Serial",
  )

  logs = get_audit_logs(
    entity_type="custom_field",
    entity_id=field_id,
  )

  assert len(logs) == 2
  assert logs[1]["action"] == "updated"

  details = json.loads(logs[1]["details"])

  assert details == {
    "name": {
      "old": "Serial Number",
      "new": "Asset Serial",
    },
  }


def test_update_custom_field_audit_records_type_change(test_db):
  field_id = create_custom_field(
    name="Purchase Value",
    field_type="integer",
  )

  update_custom_field(
    field_id,
    field_type="decimal",
  )

  logs = get_audit_logs(
    entity_type="custom_field",
    entity_id=field_id,
  )

  assert len(logs) == 2
  assert logs[1]["action"] == "updated"

  details = json.loads(logs[1]["details"])

  assert details == {
    "field_type": {
      "old": "integer",
      "new": "decimal",
    },
  }


def test_update_custom_field_audit_records_description_change(test_db):
  field_id = create_custom_field(
    name="Serial Number",
    field_type="text",
    description="Old description",
  )

  update_custom_field(
    field_id,
    description="New description",
  )

  logs = get_audit_logs(
    entity_type="custom_field",
    entity_id=field_id,
  )

  assert len(logs) == 2
  assert logs[1]["action"] == "updated"

  details = json.loads(logs[1]["details"])

  assert details == {
    "description": {
      "old": "Old description",
      "new": "New description",
    },
  }


def test_delete_custom_field(test_db):
  field_id = create_custom_field(
    name="Serial Number",
    field_type="text",
  )

  deleted = delete_custom_field(field_id)

  assert deleted is True
  assert get_custom_field(field_id) is None


def test_delete_nonexistent_custom_field(test_db):
  assert delete_custom_field(999) is False


def test_cannot_delete_custom_field_with_values(test_db):
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

  with pytest.raises(CustomFieldInUseError):
    delete_custom_field(field_id)

  assert get_custom_field(field_id) is not None

  assert (
    get_custom_field_value(
      item_id,
      field_id,
    )
    == "ABC123"
  )


def test_failed_custom_field_deletion_does_not_create_audit(
  test_db,
):
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

  with pytest.raises(CustomFieldInUseError):
    delete_custom_field(field_id)

  logs = get_audit_logs(
    entity_type="custom_field",
    entity_id=field_id,
  )

  assert len(logs) == 1
  assert logs[0]["action"] == "created"


def test_delete_custom_field_creates_audit(test_db):
  field_id = create_custom_field(
    name="Serial Number",
    field_type="text",
  )

  assert delete_custom_field(field_id) is True

  logs = get_audit_logs(
    entity_type="custom_field",
    entity_id=field_id,
  )

  assert len(logs) == 2
  assert logs[0]["action"] == "created"
  assert logs[1]["action"] == "deleted"


def test_set_custom_field_value(test_db):
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


def test_get_missing_custom_field_value_returns_none(test_db):
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


def test_update_custom_field_value(test_db):
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

  set_custom_field_value(
    item_id,
    field_id,
    "XYZ789",
  )

  assert (
    get_custom_field_value(
      item_id,
      field_id,
    )
    == "XYZ789"
  )


def test_clear_custom_field_value(test_db):
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

  assert (
    get_custom_field_value(
      item_id,
      field_id,
    )
    is None
  )


def test_clear_missing_custom_field_value_returns_false(test_db):
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


def test_item_can_have_multiple_custom_field_values(test_db):
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


def test_multiple_items_can_use_same_custom_field(test_db):
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
    ("decimal", 12.5, 12.5),
    ("boolean", True, True),
    ("date", "2026-08-16", "2026-08-16"),
  ],
)
def test_custom_field_value_types(
  test_db,
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


def test_invalid_integer_value_is_rejected(test_db):
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


def test_invalid_decimal_value_is_rejected(test_db):
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


def test_invalid_boolean_value_is_rejected(test_db):
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


def test_invalid_date_value_is_rejected(test_db):
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


def test_set_custom_field_value_creates_audit(test_db):
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


def test_update_custom_field_value_creates_audit(test_db):
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

  set_custom_field_value(
    item_id,
    field_id,
    "XYZ789",
  )

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


def test_clear_custom_field_value_creates_audit(test_db):
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

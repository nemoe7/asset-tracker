import json
from pathlib import Path

import pytest

import config
from app.db import init_db
from app.services.audit import get_audit_logs
from app.services.custom_fields import (
  create_custom_field,
  get_custom_field,
  get_custom_fields,
  update_custom_field,
)


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
    description="Device serial number",
  )

  assert field_id is not None

  field = get_custom_field(field_id)

  assert field["id"] == field_id
  assert field["name"] == "Serial Number"
  assert field["field_type"] == "text"
  assert field["description"] == "Device serial number"


def test_create_custom_field_defaults_description_to_none(test_db):
  field_id = create_custom_field(
    name="Serial Number",
    field_type="text",
  )

  field = get_custom_field(field_id)

  assert field["description"] is None


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


@pytest.mark.parametrize(
  "field_type",
  [
    "text",
    "integer",
    "decimal",
    "boolean",
    "date",
  ],
)
def test_supported_custom_field_types(test_db, field_type):
  field_id = create_custom_field(
    name=f"Test {field_type}",
    field_type=field_type,
  )

  field = get_custom_field(field_id)

  assert field["field_type"] == field_type


def test_create_custom_field_creates_audit(test_db):
  field_id = create_custom_field(
    name="Serial Number",
    field_type="text",
  )

  logs = get_audit_logs(
    entity_type="custom_field",
    entity_id=field_id,
  )

  assert len(logs) == 1
  assert logs[0]["action"] == "created"


def test_invalid_custom_field_type_is_rejected(test_db):
  with pytest.raises(ValueError):
    create_custom_field(
      name="Something",
      field_type="banana",
    )


def test_empty_custom_field_name_is_rejected(test_db):
  with pytest.raises(ValueError):
    create_custom_field(
      name="",
      field_type="text",
    )


def test_update_custom_field(test_db):
  field_id = create_custom_field(
    name="Serial Number",
    field_type="text",
    description="Device serial number",
  )

  updated = update_custom_field(
    field_id,
    name="Asset Serial Number",
    field_type="text",
    description="Unique serial number assigned to the device",
  )

  assert updated is True

  field = get_custom_field(field_id)

  assert field["name"] == "Asset Serial Number"
  assert field["field_type"] == "text"
  assert field["description"] == ("Unique serial number assigned to the device")

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
      "new": "Asset Serial Number",
    },
    "description": {
      "old": "Device serial number",
      "new": "Unique serial number assigned to the device",
    },
  }


def test_update_custom_field_type(test_db):
  field_id = create_custom_field(
    name="Purchase Value",
    field_type="integer",
  )

  updated = update_custom_field(
    field_id,
    name="Purchase Value",
    field_type="decimal",
  )

  assert updated is True

  field = get_custom_field(field_id)

  assert field["field_type"] == "decimal"

  logs = get_audit_logs(
    entity_type="custom_field",
    entity_id=field_id,
  )

  details = json.loads(logs[1]["details"])

  assert details == {
    "field_type": {
      "old": "integer",
      "new": "decimal",
    },
  }


def test_update_custom_field_description_to_none(test_db):
  field_id = create_custom_field(
    name="Serial Number",
    field_type="text",
    description="Device serial number",
  )

  updated = update_custom_field(
    field_id,
    name="Serial Number",
    description=None,
  )

  assert updated is True

  field = get_custom_field(field_id)

  assert field["description"] is None

  logs = get_audit_logs(
    entity_type="custom_field",
    entity_id=field_id,
  )

  details = json.loads(logs[1]["details"])

  assert details == {
    "description": {
      "old": "Device serial number",
      "new": None,
    },
  }


def test_update_custom_field_without_changes_does_not_create_audit(test_db):
  field_id = create_custom_field(
    name="Serial Number",
    field_type="text",
    description="Device serial number",
  )

  updated = update_custom_field(
    field_id,
    name="Serial Number",
    field_type="text",
    description="Device serial number",
  )

  assert updated is True

  logs = get_audit_logs(
    entity_type="custom_field",
    entity_id=field_id,
  )

  assert len(logs) == 1
  assert logs[0]["action"] == "created"


def test_update_nonexistent_custom_field(test_db):
  updated = update_custom_field(
    999,
    name="Serial Number",
    field_type="text",
  )

  assert updated is False


def test_update_custom_field_rejects_invalid_type(test_db):
  field_id = create_custom_field(
    name="Serial Number",
    field_type="text",
  )

  with pytest.raises(ValueError):
    update_custom_field(
      field_id,
      name="Serial Number",
      field_type="banana",
    )

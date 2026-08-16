from pathlib import Path

import pytest

import config
from app.db import get_db, init_db
from app.services.audit import get_audit_logs
from app.services.inventory import (
  create_item,
  delete_item,
  get_item,
  get_items,
  update_item,
)


@pytest.fixture
def test_db(tmp_path, monkeypatch):
  db_path = tmp_path / "test.db"
  monkeypatch.setattr(config, "DB_PATH", Path(db_path))

  init_db()

  conn = get_db()

  conn.execute("""
    INSERT INTO locations (
      id,
      name,
      description,
      created_at,
      updated_at
    )
    VALUES
      (1, 'Office', NULL, datetime('now'), datetime('now')),
      (2, 'IT Room', NULL, datetime('now'), datetime('now'))
  """)

  conn.commit()
  conn.close()

  return db_path


def test_create_item(test_db):
  item_id = create_item(
    name="Laptop",
    location_id=1,
  )

  assert item_id is not None

  item = get_item(item_id)

  assert item["id"] == item_id
  assert item["name"] == "Laptop"
  assert item["location_id"] == 1

  logs = get_audit_logs(
    entity_type="inventory_item",
    entity_id=item_id,
  )

  assert len(logs) == 1
  assert logs[0]["action"] == "created"


def test_get_item(test_db):
  item_id = create_item(
    name="Laptop",
    location_id=1,
  )

  result = get_item(item_id)

  assert result["id"] == item_id
  assert result["name"] == "Laptop"
  assert result["location_id"] == 1


def test_update_item(test_db):
  item_id = create_item(
    name="Laptop",
    location_id=1,
  )

  updated = update_item(
    item_id,
    name="Desktop",
    location_id=2,
  )

  assert updated is True

  item = get_item(item_id)

  assert item["id"] == item_id
  assert item["name"] == "Desktop"
  assert item["location_id"] == 2

  logs = get_audit_logs(
    entity_type="inventory_item",
    entity_id=item_id,
  )

  assert len(logs) == 2
  assert logs[0]["action"] == "created"
  assert logs[1]["action"] == "updated"


def test_delete_item(test_db):
  item_id = create_item(
    name="Laptop",
    location_id=1,
  )

  deleted = delete_item(item_id)

  assert deleted is True
  assert get_item(item_id) is None

  logs = get_audit_logs(
    entity_type="inventory_item",
    entity_id=item_id,
  )

  assert len(logs) == 2
  assert logs[0]["action"] == "created"
  assert logs[1]["action"] == "deleted"


def test_create_item_without_location(test_db):
  item_id = create_item(
    name="Laptop",
  )

  item = get_item(item_id)

  assert item["id"] == item_id
  assert item["name"] == "Laptop"
  assert item["location_id"] is None


def test_get_nonexistent_item(test_db):
  result = get_item("does-not-exist")

  assert result is None


def test_get_items(test_db):
  create_item(
    name="Laptop",
    location_id=1,
  )

  create_item(
    name="Desktop",
    location_id=2,
  )

  items = get_items()

  assert len(items) == 2
  assert items[0]["name"] == "Desktop"
  assert items[1]["name"] == "Laptop"


def test_update_nonexistent_item(test_db):
  result = update_item(
    "does-not-exist",
    name="Laptop",
    location_id=1,
  )

  assert result is False

  logs = get_audit_logs(
    entity_type="inventory_item",
    entity_id="does-not-exist",
  )

  assert logs == []


def test_delete_nonexistent_item(test_db):
  result = delete_item("does-not-exist")

  assert result is False

  logs = get_audit_logs(
    entity_type="inventory_item",
    entity_id="does-not-exist",
  )

  assert logs == []


def test_update_item_without_location(test_db):
  item_id = create_item(
    name="Laptop",
    location_id=1,
  )

  updated = update_item(
    item_id,
    name="Laptop",
  )

  assert updated is True

  item = get_item(item_id)

  assert item["name"] == "Laptop"
  assert item["location_id"] is None


def test_audit_uses_item_id_as_text(test_db):
  item_id = create_item(
    name="Laptop",
    location_id=1,
  )

  logs = get_audit_logs(
    entity_type="inventory_item",
    entity_id=item_id,
  )

  assert len(logs) == 1
  assert logs[0]["entity_id"] == str(item_id)

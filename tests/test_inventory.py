import json
from pathlib import Path

import pytest

import config
from app.db import get_db, init_db
from app.services.audit import get_audit_logs
from app.services.inventory import (
  archive_item,
  create_item,
  get_item,
  get_items,
  restore_item,
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


def test_update_item_audit_records_name_change(test_db):
  item_id = create_item(
    name="Laptop",
    location_id=1,
  )

  updated = update_item(
    item_id,
    name="Desktop",
    location_id=1,
  )

  assert updated is True

  logs = get_audit_logs(
    entity_type="inventory_item",
    entity_id=item_id,
  )

  assert len(logs) == 2
  assert logs[1]["action"] == "updated"

  details = json.loads(logs[1]["details"])

  assert details == {
    "name": {
      "old": "Laptop",
      "new": "Desktop",
    },
  }


def test_update_item_audit_records_location_change(test_db):
  item_id = create_item(
    name="Laptop",
    location_id=1,
  )

  updated = update_item(
    item_id,
    name="Laptop",
    location_id=2,
  )

  assert updated is True

  logs = get_audit_logs(
    entity_type="inventory_item",
    entity_id=item_id,
  )

  assert len(logs) == 2
  assert logs[1]["action"] == "updated"

  details = json.loads(logs[1]["details"])

  assert details == {
    "location_id": {
      "old": 1,
      "new": 2,
    },
  }


def test_update_item_audit_records_multiple_changes(test_db):
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

  logs = get_audit_logs(
    entity_type="inventory_item",
    entity_id=item_id,
  )

  assert len(logs) == 2
  assert logs[1]["action"] == "updated"

  details = json.loads(logs[1]["details"])

  assert details == {
    "name": {
      "old": "Laptop",
      "new": "Desktop",
    },
    "location_id": {
      "old": 1,
      "new": 2,
    },
  }


def test_update_item_audit_records_location_removed(test_db):
  item_id = create_item(
    name="Laptop",
    location_id=1,
  )

  updated = update_item(
    item_id,
    name="Laptop",
    location_id=None,
  )

  assert updated is True

  logs = get_audit_logs(
    entity_type="inventory_item",
    entity_id=item_id,
  )

  assert len(logs) == 2

  details = json.loads(logs[1]["details"])

  assert details == {
    "location_id": {
      "old": 1,
      "new": None,
    },
  }


def test_update_item_without_changes_does_not_create_audit(test_db):
  item_id = create_item(
    name="Laptop",
    location_id=1,
  )

  updated = update_item(
    item_id,
    name="Laptop",
    location_id=1,
  )

  assert updated is True

  logs = get_audit_logs(
    entity_type="inventory_item",
    entity_id=item_id,
  )

  assert len(logs) == 1
  assert logs[0]["action"] == "created"


def test_archive_item_hides_from_active_items(test_db):
  item_id = create_item(
    name="Laptop",
    location_id=1,
  )

  archived = archive_item(item_id)

  assert archived is True
  assert get_item(item_id) is None

  logs = get_audit_logs(
    entity_type="inventory_item",
    entity_id=item_id,
  )

  assert len(logs) == 2
  assert logs[0]["action"] == "created"
  assert logs[1]["action"] == "archived"


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


def test_archive_nonexistent_item(test_db):
  result = archive_item("does-not-exist")

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


def test_archived_item_is_not_in_get_items(test_db):
  item_id = create_item(
    name="Laptop",
    location_id=1,
  )

  create_item(
    name="Desktop",
    location_id=1,
  )

  archive_item(item_id)

  items = get_items()

  assert len(items) == 1
  assert items[0]["name"] == "Desktop"


def test_archived_item_remains_in_database(test_db):
  item_id = create_item(
    name="Laptop",
    location_id=1,
  )

  archive_item(item_id)

  connection = get_db()

  try:
    item = connection.execute(
      """
      SELECT *
      FROM inventory_items
      WHERE id = ?
      """,
      (item_id,),
    ).fetchone()
  finally:
    connection.close()

  assert item is not None
  assert item["archived_at"] is not None


def test_cannot_archive_already_archived_item(test_db):
  item_id = create_item(
    name="Laptop",
    location_id=1,
  )

  assert archive_item(item_id) is True
  assert archive_item(item_id) is False


def test_inventory_items_support_archival(test_db):
  connection = get_db()

  try:
    columns = connection.execute(
      """
      PRAGMA table_info(inventory_items)
      """
    ).fetchall()
  finally:
    connection.close()

  column_names = {column["name"] for column in columns}

  assert "archived_at" in column_names


def test_restore_item_makes_item_active_again(test_db):
  item_id = create_item(
    name="Laptop",
    location_id=1,
  )

  assert archive_item(item_id) is True
  assert get_item(item_id) is None

  restored = restore_item(item_id)

  assert restored is True

  item = get_item(item_id)

  assert item is not None
  assert item["id"] == item_id
  assert item["name"] == "Laptop"
  assert item["location_id"] == 1
  assert item["archived_at"] is None

  logs = get_audit_logs(
    entity_type="inventory_item",
    entity_id=item_id,
  )

  assert len(logs) == 3
  assert logs[0]["action"] == "created"
  assert logs[1]["action"] == "archived"
  assert logs[2]["action"] == "restored"


def test_cannot_restore_active_item(test_db):
  item_id = create_item(
    name="Laptop",
    location_id=1,
  )

  assert restore_item(item_id) is False

  logs = get_audit_logs(
    entity_type="inventory_item",
    entity_id=item_id,
  )

  assert len(logs) == 1
  assert logs[0]["action"] == "created"


def test_restore_nonexistent_item_returns_false(test_db):
  assert restore_item("does-not-exist") is False


def test_restored_item_appears_in_get_items(test_db):
  item_id = create_item(
    name="Laptop",
    location_id=1,
  )

  archive_item(item_id)

  assert get_items() == []

  assert restore_item(item_id) is True

  items = get_items()

  assert len(items) == 1
  assert items[0]["id"] == item_id

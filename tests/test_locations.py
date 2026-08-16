import json

import pytest

from app.db import get_db, init_db
from app.services.audit import get_audit_logs
from app.services.inventory import archive_item, create_item, get_item
from app.services.locations import (
  LocationDeletionConfirmationRequired,
  create_location,
  delete_location,
  get_location,
  get_locations,
  update_location,
)


@pytest.fixture
def test_db(tmp_path, monkeypatch):
  import config

  db_path = tmp_path / "test.db"
  monkeypatch.setattr(config, "DB_PATH", db_path)

  init_db()

  return db_path


def test_create_location(test_db):
  location_id = create_location(
    name="Office",
    description="Main office",
  )

  assert location_id is not None

  location = get_location(location_id)

  assert location["id"] == location_id
  assert location["name"] == "Office"
  assert location["description"] == "Main office"

  logs = get_audit_logs(
    entity_type="location",
    entity_id=location_id,
  )

  assert len(logs) == 1
  assert logs[0]["action"] == "created"


def test_get_location(test_db):
  location_id = create_location("Office")

  result = get_location(location_id)

  assert result["id"] == location_id
  assert result["name"] == "Office"
  assert result["description"] is None


def test_get_nonexistent_location(test_db):
  assert get_location(999) is None


def test_get_locations(test_db):
  create_location("Office")
  create_location("IT Room")

  locations = get_locations()

  assert len(locations) == 2
  assert locations[0]["name"] == "IT Room"
  assert locations[1]["name"] == "Office"


def test_update_location(test_db):
  location_id = create_location(
    "Office",
    "Main office",
  )

  updated = update_location(
    location_id,
    "Head Office",
    "Main headquarters",
  )

  assert updated is True

  location = get_location(location_id)

  assert location["name"] == "Head Office"
  assert location["description"] == "Main headquarters"

  logs = get_audit_logs(
    entity_type="location",
    entity_id=location_id,
  )

  assert len(logs) == 2
  assert logs[0]["action"] == "created"
  assert logs[1]["action"] == "updated"

  details = json.loads(logs[1]["details"])

  assert details == {
    "name": {
      "old": "Office",
      "new": "Head Office",
    },
    "description": {
      "old": "Main office",
      "new": "Main headquarters",
    },
  }


def test_update_location_name_only(test_db):
  location_id = create_location(
    "Office",
    "Main office",
  )

  updated = update_location(
    location_id,
    "Head Office",
    "Main office",
  )

  assert updated is True

  logs = get_audit_logs(
    entity_type="location",
    entity_id=location_id,
  )

  assert len(logs) == 2

  details = json.loads(logs[1]["details"])

  assert details == {
    "name": {
      "old": "Office",
      "new": "Head Office",
    },
  }


def test_update_location_description_only(test_db):
  location_id = create_location(
    "Office",
    "Main office",
  )

  updated = update_location(
    location_id,
    "Office",
    "Headquarters",
  )

  assert updated is True

  logs = get_audit_logs(
    entity_type="location",
    entity_id=location_id,
  )

  assert len(logs) == 2

  details = json.loads(logs[1]["details"])

  assert details == {
    "description": {
      "old": "Main office",
      "new": "Headquarters",
    },
  }


def test_update_location_description_removed(test_db):
  location_id = create_location(
    "Office",
    "Main office",
  )

  updated = update_location(
    location_id,
    "Office",
    None,
  )

  assert updated is True

  location = get_location(location_id)

  assert location["description"] is None

  logs = get_audit_logs(
    entity_type="location",
    entity_id=location_id,
  )

  assert len(logs) == 2

  details = json.loads(logs[1]["details"])

  assert details == {
    "description": {
      "old": "Main office",
      "new": None,
    },
  }


def test_update_location_without_changes_does_not_create_audit(test_db):
  location_id = create_location(
    "Office",
    "Main office",
  )

  updated = update_location(
    location_id,
    "Office",
    "Main office",
  )

  assert updated is True

  logs = get_audit_logs(
    entity_type="location",
    entity_id=location_id,
  )

  assert len(logs) == 1
  assert logs[0]["action"] == "created"


def test_update_nonexistent_location(test_db):
  result = update_location(
    999,
    "Office",
  )

  assert result is False

  logs = get_audit_logs(
    entity_type="location",
    entity_id=999,
  )

  assert logs == []


def test_delete_location(test_db):
  location_id = create_location("Office")

  deleted = delete_location(location_id)

  assert deleted is True
  assert get_location(location_id) is None

  logs = get_audit_logs(
    entity_type="location",
    entity_id=location_id,
  )

  assert len(logs) == 2
  assert logs[0]["action"] == "created"
  assert logs[1]["action"] == "deleted"


def test_delete_nonexistent_location(test_db):
  assert delete_location(999) is False

  logs = get_audit_logs(
    entity_type="location",
    entity_id=999,
  )

  assert logs == []


def test_delete_location_with_items_requires_confirmation(test_db):
  location_id = create_location("Office")

  item_id = create_item(
    name="Laptop",
    location_id=location_id,
  )

  with pytest.raises(LocationDeletionConfirmationRequired):
    delete_location(location_id)

  location = get_location(location_id)
  assert location is not None

  item = get_item(item_id)
  assert item["location_id"] == location_id


def test_delete_location_with_items_after_confirmation(test_db):
  location_id = create_location("Office")

  item_id = create_item(
    name="Laptop",
    location_id=location_id,
  )

  deleted = delete_location(
    location_id,
    confirmed=True,
  )

  assert deleted is True
  assert get_location(location_id) is None

  item = get_item(item_id)
  assert item["location_id"] is None


def test_delete_location_with_multiple_items_after_confirmation(test_db):
  location_id = create_location("Office")

  item1_id = create_item(
    name="Laptop",
    location_id=location_id,
  )

  item2_id = create_item(
    name="Desktop",
    location_id=location_id,
  )

  deleted = delete_location(
    location_id,
    confirmed=True,
  )

  assert deleted is True
  assert get_location(location_id) is None

  assert get_item(item1_id)["location_id"] is None
  assert get_item(item2_id)["location_id"] is None


def test_delete_location_with_items_creates_item_audits(test_db):
  location_id = create_location("Office")

  item_id = create_item(
    name="Laptop",
    location_id=location_id,
  )

  delete_location(
    location_id,
    confirmed=True,
  )

  logs = get_audit_logs(
    entity_type="inventory_item",
    entity_id=item_id,
  )

  assert len(logs) == 2
  assert logs[0]["action"] == "created"
  assert logs[1]["action"] == "location_changed"

  details = json.loads(logs[1]["details"])

  assert details == {
    "old_location_id": location_id,
    "new_location_id": None,
  }


def test_delete_location_with_items_creates_location_audit(test_db):
  location_id = create_location("Office")

  create_item(
    name="Laptop",
    location_id=location_id,
  )

  delete_location(
    location_id,
    confirmed=True,
  )

  logs = get_audit_logs(
    entity_type="location",
    entity_id=location_id,
  )

  assert len(logs) == 2
  assert logs[0]["action"] == "created"
  assert logs[1]["action"] == "deleted"


def test_delete_location_rolls_back_when_audit_fails(test_db, monkeypatch):
  location_id = create_location("Office")

  item_id = create_item(
    name="Laptop",
    location_id=location_id,
  )

  from app.services import locations

  original_create_audit_log = locations.create_audit_log

  def failing_audit(*args, **kwargs):
    if kwargs.get("action") == "deleted":
      raise RuntimeError("simulated audit failure")

    return original_create_audit_log(*args, **kwargs)

  monkeypatch.setattr(
    locations,
    "create_audit_log",
    failing_audit,
  )

  with pytest.raises(RuntimeError):
    locations.delete_location(
      location_id,
      confirmed=True,
    )

  assert get_location(location_id) is not None
  assert get_item(item_id)["location_id"] == location_id

  logs = get_audit_logs(
    entity_type="inventory_item",
    entity_id=item_id,
  )

  assert len(logs) == 1
  assert logs[0]["action"] == "created"


def test_delete_location_rolls_back_all_items_when_audit_fails(
  test_db,
  monkeypatch,
):
  location_id = create_location("Office")

  item1_id = create_item(
    name="Laptop",
    location_id=location_id,
  )

  item2_id = create_item(
    name="Desktop",
    location_id=location_id,
  )

  from app.services import locations

  original_create_audit_log = locations.create_audit_log
  location_change_count = 0

  def failing_audit(*args, **kwargs):
    nonlocal location_change_count

    if kwargs.get("action") == "location_changed":
      location_change_count += 1

      if location_change_count == 2:
        raise RuntimeError("simulated audit failure")

    return original_create_audit_log(*args, **kwargs)

  monkeypatch.setattr(
    locations,
    "create_audit_log",
    failing_audit,
  )

  with pytest.raises(RuntimeError):
    locations.delete_location(
      location_id,
      confirmed=True,
    )

  assert get_location(location_id) is not None

  assert get_item(item1_id)["location_id"] == location_id
  assert get_item(item2_id)["location_id"] == location_id

  item1_logs = get_audit_logs(
    entity_type="inventory_item",
    entity_id=item1_id,
  )

  item2_logs = get_audit_logs(
    entity_type="inventory_item",
    entity_id=item2_id,
  )

  assert len(item1_logs) == 1
  assert len(item2_logs) == 1

  assert item1_logs[0]["action"] == "created"
  assert item2_logs[0]["action"] == "created"


def test_delete_location_unassigns_archived_items(test_db):
  location_id = create_location("Office")

  item_id = create_item(
    name="Laptop",
    location_id=location_id,
  )

  assert archive_item(item_id) is True

  deleted = delete_location(
    location_id,
    confirmed=True,
  )

  assert deleted is True
  assert get_location(location_id) is None

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
  assert item["location_id"] is None

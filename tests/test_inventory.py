from app.services.audit import get_audit_logs
from app.services.inventory import (
  archive_item,
  create_item,
  get_item,
  get_items,
  restore_item,
  update_item,
)
from app.services.locations import create_location


def test_create_item(test_db, authenticated_test_user):
  item_id = create_item(
    name="Laptop",
  )

  item = get_item(item_id)

  assert item["id"] == item_id
  assert item["name"] == "Laptop"
  assert item["location_id"] is None
  assert item["archived_at"] is None


def test_create_item_with_location(test_db, authenticated_test_user):
  location_id = create_location(
    name="Storage Room",
  )

  item_id = create_item(
    name="Laptop",
    location_id=location_id,
  )

  item = get_item(item_id)

  assert item["name"] == "Laptop"
  assert item["location_id"] == location_id


def test_create_item_creates_audit_log(test_db, authenticated_test_user):
  item_id = create_item(
    name="Laptop",
  )

  logs = get_audit_logs(
    entity_type="inventory_item",
    entity_id=item_id,
  )

  assert len(logs) == 1
  assert logs[0]["user_id"] == 1
  assert logs[0]["action"] == "created"


def test_get_item(test_db, authenticated_test_user):
  item_id = create_item(
    name="Laptop",
  )

  item = get_item(item_id)

  assert item is not None
  assert item["id"] == item_id
  assert item["name"] == "Laptop"


def test_get_nonexistent_item(test_db):
  assert get_item("nonexistent") is None


def test_get_items(test_db, authenticated_test_user):
  first_id = create_item(
    name="Laptop",
  )

  second_id = create_item(
    name="Monitor",
  )

  items = get_items()

  ids = [item["id"] for item in items]

  assert first_id in ids
  assert second_id in ids


def test_update_item_name(test_db, authenticated_test_user):
  item_id = create_item(
    name="Laptop",
  )

  assert (
    update_item(
      item_id,
      name="Desktop",
    )
    is True
  )

  item = get_item(item_id)

  assert item["name"] == "Desktop"


def test_update_item_location(test_db, authenticated_test_user):
  item_id = create_item(
    name="Laptop",
  )

  location_id = create_location(
    name="Storage Room",
  )

  assert (
    update_item(
      item_id,
      location_id=location_id,
    )
    is True
  )

  item = get_item(item_id)

  assert item["location_id"] == location_id


def test_update_item_remove_location(test_db, authenticated_test_user):
  location_id = create_location(
    name="Storage Room",
  )

  item_id = create_item(
    name="Laptop",
    location_id=location_id,
  )

  assert (
    update_item(
      item_id,
      location_id=None,
    )
    is True
  )

  item = get_item(item_id)

  assert item["location_id"] is None


def test_update_item_name_only_preserves_location(test_db, authenticated_test_user):
  location_id = create_location(
    name="Storage Room",
  )

  item_id = create_item(
    name="Laptop",
    location_id=location_id,
  )

  assert (
    update_item(
      item_id,
      name="Desktop",
    )
    is True
  )

  item = get_item(item_id)

  assert item["name"] == "Desktop"
  assert item["location_id"] == location_id


def test_update_item_location_only_preserves_name(test_db, authenticated_test_user):
  first_location_id = create_location(
    name="Storage Room",
  )

  second_location_id = create_location(
    name="Office",
  )

  item_id = create_item(
    name="Laptop",
    location_id=first_location_id,
  )

  assert (
    update_item(
      item_id,
      location_id=second_location_id,
    )
    is True
  )

  item = get_item(item_id)

  assert item["name"] == "Laptop"
  assert item["location_id"] == second_location_id


def test_update_item_without_changes_creates_no_audit_log(
  test_db, authenticated_test_user
):
  item_id = create_item(
    name="Laptop",
  )

  assert update_item(item_id) is True

  logs = get_audit_logs(
    entity_type="inventory_item",
    entity_id=item_id,
  )

  assert len(logs) == 1
  assert logs[0]["action"] == "created"


def test_update_item_creates_audit_log(test_db, authenticated_test_user):
  first_location_id = create_location(
    name="Storage Room",
  )

  second_location_id = create_location(
    name="Office",
  )

  item_id = create_item(
    name="Laptop",
    location_id=first_location_id,
  )

  assert (
    update_item(
      item_id,
      name="Desktop",
      location_id=second_location_id,
    )
    is True
  )

  logs = get_audit_logs(
    entity_type="inventory_item",
    entity_id=item_id,
  )

  assert len(logs) == 2
  assert logs[0]["action"] == "created"
  assert logs[1]["action"] == "updated"
  assert logs[1]["user_id"] == 1


def test_update_item_with_same_values_creates_no_audit_log(
  test_db, authenticated_test_user
):
  location_id = create_location(
    name="Storage Room",
  )

  item_id = create_item(
    name="Laptop",
    location_id=location_id,
  )

  assert (
    update_item(
      item_id,
      name="Laptop",
      location_id=location_id,
    )
    is True
  )

  logs = get_audit_logs(
    entity_type="inventory_item",
    entity_id=item_id,
  )

  assert len(logs) == 1
  assert logs[0]["action"] == "created"


def test_update_nonexistent_item(test_db):
  assert (
    update_item(
      "nonexistent",
      name="Laptop",
    )
    is False
  )


def test_archive_item(test_db, authenticated_test_user):
  item_id = create_item(
    name="Laptop",
  )

  assert archive_item(item_id) is True

  assert get_item(item_id) is None


def test_archive_item_creates_audit_log(test_db, authenticated_test_user):
  item_id = create_item(
    name="Laptop",
  )

  assert archive_item(item_id) is True

  logs = get_audit_logs(
    entity_type="inventory_item",
    entity_id=item_id,
  )

  assert len(logs) == 2
  assert logs[0]["action"] == "created"
  assert logs[1]["action"] == "archived"
  assert logs[1]["user_id"] == 1


def test_archive_item_excludes_item_from_get_items(test_db, authenticated_test_user):
  item_id = create_item(
    name="Laptop",
  )

  assert archive_item(item_id) is True

  items = get_items()

  assert all(item["id"] != item_id for item in items)


def test_cannot_archive_already_archived_item(test_db, authenticated_test_user):
  item_id = create_item(
    name="Laptop",
  )

  assert archive_item(item_id) is True
  assert archive_item(item_id) is False


def test_archive_nonexistent_item(test_db):
  assert archive_item("nonexistent") is False


def test_restore_item(test_db, authenticated_test_user):
  item_id = create_item(
    name="Laptop",
  )

  assert archive_item(item_id) is True
  assert restore_item(item_id) is True

  item = get_item(item_id)

  assert item["archived_at"] is None


def test_restore_item_creates_audit_log(test_db, authenticated_test_user):
  item_id = create_item(
    name="Laptop",
  )

  assert archive_item(item_id) is True
  assert restore_item(item_id) is True

  logs = get_audit_logs(
    entity_type="inventory_item",
    entity_id=item_id,
  )

  assert len(logs) == 3
  assert logs[0]["action"] == "created"
  assert logs[1]["action"] == "archived"
  assert logs[2]["action"] == "restored"
  assert logs[2]["user_id"] == 1


def test_restore_active_item(test_db, authenticated_test_user):
  item_id = create_item(
    name="Laptop",
  )

  assert restore_item(item_id) is False


def test_restore_nonexistent_item(test_db):
  assert restore_item("nonexistent") is False


def test_update_archived_item_fails(test_db, authenticated_test_user):
  item_id = create_item(
    name="Laptop",
  )

  assert archive_item(item_id) is True

  assert (
    update_item(
      item_id,
      name="Desktop",
    )
    is False
  )

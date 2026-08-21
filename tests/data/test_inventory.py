import pytest

from app.services.data.audit import get_audit_logs
from app.services.data.inventory import (
  archive_item,
  create_item,
  get_item,
  get_items,
  restore_item,
  update_item,
)
from app.services.data.locations import create_location
from app.services.exceptions.data.common import InvalidInputError
from app.services.exceptions.data.inventory import *
from app.services.exceptions.data.locations import LocationNotFoundError


def test_create_item(gen_test_admin):
  item_id = create_item("Laptop")

  assert item_id is not None

  item = get_item(item_id)

  assert item["id"] == item_id
  assert item["name"] == "Laptop"
  assert item["location_id"] is None
  assert item["archived_at"] is None
  assert item["custom_fields"] == {}


def test_create_item_with_location(gen_test_admin):
  location_id = create_location("Storage")
  item_id = create_item(
    "Laptop",
    location_id=location_id,
  )

  item = get_item(item_id)

  assert item["location_id"] == location_id
  assert item["location_name"] == "Storage"


def test_create_item_with_empty_name_fails(gen_test_admin):
  with pytest.raises(InvalidItemNameError):
    create_item("")


def test_create_item_with_whitespace_name_fails(gen_test_admin):
  with pytest.raises(InvalidItemNameError):
    create_item("   ")


def test_create_item_with_non_string_name_fails(gen_test_admin):
  with pytest.raises(InvalidItemNameError):
    create_item(None)


def test_create_item_with_nonexistent_location_fails(gen_test_admin):
  with pytest.raises(LocationNotFoundError):
    create_item(
      "Laptop",
      location_id=999,
    )


def test_get_item(gen_test_admin):
  item_id = create_item("Laptop")

  item = get_item(item_id)

  assert item["id"] == item_id
  assert item["name"] == "Laptop"


def test_get_nonexistent_item(gen_test_admin):
  assert get_item("does-not-exist") is None


def test_get_items(gen_test_admin):
  create_item("Laptop")
  create_item("Monitor")

  items = get_items()

  assert len(items) == 2
  assert items[0]["name"] == "Laptop"
  assert items[1]["name"] == "Monitor"


def test_get_items_search(gen_test_admin):
  create_item("Gaming Laptop")
  create_item("Office Monitor")

  items = get_items(search="Laptop")

  assert len(items) == 1
  assert items[0]["name"] == "Gaming Laptop"


def test_get_items_search_is_partial(gen_test_admin):
  create_item("Gaming Laptop")

  items = get_items(search="Lap")

  assert len(items) == 1
  assert items[0]["name"] == "Gaming Laptop"


def test_get_items_by_location(gen_test_admin):
  storage_id = create_location("Storage")
  office_id = create_location("Office")

  create_item(
    "Laptop",
    location_id=storage_id,
  )
  create_item(
    "Monitor",
    location_id=office_id,
  )

  items = get_items(location_id=storage_id)

  assert len(items) == 1
  assert items[0]["name"] == "Laptop"


def test_get_items_with_nonexistent_location_fails(gen_test_admin):
  with pytest.raises(LocationNotFoundError):
    get_items(location_id=999)


def test_update_item_name(gen_test_admin):
  item_id = create_item("Laptop")

  assert (
    update_item(
      item_id,
      name="Desktop",
    )
    is True
  )

  item = get_item(item_id)

  assert item["name"] == "Desktop"


def test_update_item_location(gen_test_admin):
  old_location = create_location("Storage")
  new_location = create_location("Office")

  item_id = create_item(
    "Laptop",
    location_id=old_location,
  )

  assert (
    update_item(
      item_id,
      location_id=new_location,
    )
    is True
  )

  item = get_item(item_id)

  assert item["location_id"] == new_location
  assert item["location_name"] == "Office"


def test_update_item_location_to_none(gen_test_admin):
  location_id = create_location("Storage")

  item_id = create_item(
    "Laptop",
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
  assert item["location_name"] is None


def test_update_item_with_no_fields_fails(gen_test_admin):
  item_id = create_item("Laptop")

  with pytest.raises(
    InvalidInputError,
    match="No fields to update",
  ):
    update_item(item_id)


def test_update_nonexistent_item(gen_test_admin):
  with pytest.raises(ItemNotFoundError):
    update_item(
      "does-not-exist",
      name="Laptop",
    )


def test_update_archived_item_fails(gen_test_admin):
  item_id = create_item("Laptop")

  archive_item(item_id)

  with pytest.raises(ItemIsArchivedError):
    update_item(
      item_id,
      name="Desktop",
    )


def test_update_item_with_empty_name_fails(gen_test_admin):
  item_id = create_item("Laptop")

  with pytest.raises(InvalidItemNameError):
    update_item(
      item_id,
      name="",
    )


def test_update_item_with_nonexistent_location_fails(gen_test_admin):
  item_id = create_item("Laptop")

  with pytest.raises(LocationNotFoundError):
    update_item(
      item_id,
      location_id=999,
    )


def test_update_item_with_same_name_creates_no_audit_log(gen_test_admin):
  item_id = create_item("Laptop")

  assert (
    update_item(
      item_id,
      name="Laptop",
    )
    is True
  )

  logs = get_audit_logs(
    entity_type="inventory_item",
    entity_id=item_id,
  )

  assert len(logs) == 1
  assert logs[0]["action"] == "created"


def test_update_item_with_same_location_creates_no_audit_log(
  gen_test_admin,
):
  location_id = create_location("Storage")

  item_id = create_item(
    "Laptop",
    location_id=location_id,
  )

  assert (
    update_item(
      item_id,
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


def test_update_item_creates_audit_log(gen_test_admin):
  item_id = create_item("Laptop")

  assert (
    update_item(
      item_id,
      name="Desktop",
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

  details = logs[1]["details"]

  assert details == {
    "name": {
      "old": "Laptop",
      "new": "Desktop",
    },
  }


def test_update_item_creates_audit_log_for_location_change(
  gen_test_admin,
):
  old_location = create_location("Storage")
  new_location = create_location("Office")

  item_id = create_item(
    "Laptop",
    location_id=old_location,
  )

  assert (
    update_item(
      item_id,
      location_id=new_location,
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

  details = logs[1]["details"]

  assert details == {
    "location_id": {
      "old": old_location,
      "new": new_location,
    },
  }


def test_archive_item(gen_test_admin):
  item_id = create_item("Laptop")

  assert archive_item(item_id) is True

  item = get_item(item_id)

  assert item is None


def test_archive_item_creates_audit_log(gen_test_admin):
  item_id = create_item("Laptop")

  assert archive_item(item_id) is True

  logs = get_audit_logs(
    entity_type="inventory_item",
    entity_id=item_id,
  )

  assert len(logs) == 2
  assert logs[0]["action"] == "created"
  assert logs[1]["action"] == "archived"


def test_archive_already_archived_item_fails(gen_test_admin):
  item_id = create_item("Laptop")

  assert archive_item(item_id) is True

  with pytest.raises(ItemIsArchivedError):
    archive_item(item_id)


def test_archive_nonexistent_item(gen_test_admin):
  with pytest.raises(ItemNotFoundError):
    archive_item("does-not-exist")


def test_archived_item_excluded_from_get_items(gen_test_admin):
  item_id = create_item("Laptop")

  archive_item(item_id)

  assert get_items() == []


def test_archived_item_included_when_requested(gen_test_admin):
  item_id = create_item("Laptop")

  archive_item(item_id)

  items = get_items(include_archived=True)

  assert len(items) == 1
  assert items[0]["id"] == item_id
  assert items[0]["name"] == "Laptop"
  assert items[0]["archived_at"] is not None


def test_restore_item(gen_test_admin):
  item_id = create_item("Laptop")

  archive_item(item_id)

  assert restore_item(item_id) is True

  item = get_item(item_id)

  assert item is not None
  assert item["name"] == "Laptop"
  assert item["archived_at"] is None


def test_restore_item_creates_audit_log(gen_test_admin):
  item_id = create_item("Laptop")

  archive_item(item_id)
  assert restore_item(item_id) is True

  logs = get_audit_logs(
    entity_type="inventory_item",
    entity_id=item_id,
  )

  assert len(logs) == 3
  assert logs[0]["action"] == "created"
  assert logs[1]["action"] == "archived"
  assert logs[2]["action"] == "restored"


def test_restore_active_item_fails(gen_test_admin):
  item_id = create_item("Laptop")

  with pytest.raises(ItemIsNotArchivedError):
    restore_item(item_id)


def test_restore_nonexistent_item(gen_test_admin):
  with pytest.raises(ItemNotFoundError):
    restore_item("does-not-exist")


def test_archived_item_can_be_restored_and_found_again(gen_test_admin):
  item_id = create_item("Laptop")

  archive_item(item_id)

  assert get_item(item_id) is None

  restore_item(item_id)

  item = get_item(item_id)

  assert item is not None
  assert item["id"] == item_id
  assert item["name"] == "Laptop"
  assert item["archived_at"] is None


def test_update_item_creates_one_audit_log_for_multiple_changes(
  gen_test_admin,
):
  old_location = create_location("Storage")
  new_location = create_location("Office")

  item_id = create_item(
    "Laptop",
    location_id=old_location,
  )

  assert (
    update_item(
      item_id,
      name="Desktop",
      location_id=new_location,
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

  assert logs[1]["details"] == {
    "name": {
      "old": "Laptop",
      "new": "Desktop",
    },
    "location_id": {
      "old": old_location,
      "new": new_location,
    },
  }

import pytest

from app.services.checks import check_item
from app.services.data.audit import get_audit_logs
from app.services.data.inventory import (
  archive_item,
  create_item,
  get_item,
)
from app.services.data.locations import create_location
from app.services.exceptions.data.inventory import (
  ItemIsArchivedError,
  ItemNotFoundError,
)
from app.services.exceptions.data.locations import LocationNotFoundError


def test_check_item(gen_test_data_admin):
  item_id = create_item("Laptop")

  assert check_item(item_id) is True

  logs = get_audit_logs(
    entity_type="inventory_item",
    entity_id=item_id,
  )

  assert len(logs) == 2
  assert logs[-1]["user_id"] == gen_test_data_admin
  assert logs[-1]["action"] == "checked"
  assert logs[-1]["entity_type"] == "inventory_item"
  assert logs[-1]["entity_id"] == item_id


def test_check_item_with_location(gen_test_data_admin):
  item_id = create_item("Laptop")
  location_name = "Room 204"
  location_id = create_location(location_name)

  assert (
    check_item(
      item_id,
      location_id=location_id,
    )
    is True
  )

  item = get_item(item_id)

  assert item["location_id"] == location_id

  logs = get_audit_logs(
    entity_type="inventory_item",
    entity_id=item_id,
  )

  assert logs[-1]["details"] == {
    "location": location_name,
  }


def test_check_item_with_none_clears_location(gen_test_data_admin):
  location_id = create_location("Room 204")
  item_id = create_item(
    "Laptop",
    location_id=location_id,
  )

  assert (
    check_item(
      item_id,
      location_id=None,
    )
    is True
  )

  item = get_item(item_id)

  assert item["location_id"] is None


def test_check_item_without_location_keeps_location(gen_test_data_admin):
  location_id = create_location("Room 204")
  item_id = create_item(
    "Laptop",
    location_id=location_id,
  )

  assert check_item(item_id) is True

  item = get_item(item_id)

  assert item["location_id"] == location_id


def test_check_item_invalid_location(gen_test_data_admin):
  item_id = create_item("Laptop")

  with pytest.raises(LocationNotFoundError):
    check_item(
      item_id,
      location_id=999,
    )


def test_check_item_not_found(gen_test_data_admin):
  with pytest.raises(ItemNotFoundError):
    check_item("does-not-exist")


def test_check_archived_item(gen_test_data_admin):
  item_id = create_item("Laptop")

  archive_item(item_id)

  with pytest.raises(ItemIsArchivedError):
    check_item(item_id)

import pytest

from app.services.audit import get_audit_logs
from app.services.inventory import create_item, get_item
from app.services.locations import (
  LocationDeletionConfirmationRequired,
  create_location,
  delete_location,
  get_location,
  get_locations,
  update_location,
)


def test_create_location(test_db):
  location_id = create_location(
    name="Storage Room",
  )

  location = get_location(location_id)

  assert location["id"] == location_id
  assert location["name"] == "Storage Room"
  assert location["description"] is None


def test_create_location_with_description(test_db):
  location_id = create_location(
    name="Storage Room",
    description="Main storage area",
  )

  location = get_location(location_id)

  assert location["name"] == "Storage Room"
  assert location["description"] == "Main storage area"


def test_create_location_creates_audit_log(test_db):
  location_id = create_location(
    name="Storage Room",
  )

  logs = get_audit_logs(
    entity_type="location",
    entity_id=location_id,
  )

  assert len(logs) == 1
  assert logs[0]["user_id"] == 1
  assert logs[0]["action"] == "created"


def test_create_location_with_duplicate_name_fails(test_db):
  create_location(
    name="Storage Room",
  )

  with pytest.raises(ValueError):
    create_location(
      name="Storage Room",
    )


def test_create_location_with_empty_name_fails(test_db):
  with pytest.raises(ValueError):
    create_location(
      name="",
    )


def test_create_location_with_whitespace_name_fails(test_db):
  with pytest.raises(ValueError):
    create_location(
      name="   ",
    )


def test_get_location(test_db):
  location_id = create_location(
    name="Storage Room",
  )

  location = get_location(location_id)

  assert location is not None
  assert location["id"] == location_id


def test_get_nonexistent_location(test_db):
  assert get_location(999) is None


def test_get_locations(test_db):
  first_id = create_location(
    name="Storage Room",
  )

  second_id = create_location(
    name="Office",
  )

  locations = get_locations()

  ids = [location["id"] for location in locations]

  assert first_id in ids
  assert second_id in ids


def test_update_location_name(test_db):
  location_id = create_location(
    name="Storage Room",
  )

  assert (
    update_location(
      location_id,
      name="Main Storage",
    )
    is True
  )

  location = get_location(location_id)

  assert location["name"] == "Main Storage"


def test_update_location_description(test_db):
  location_id = create_location(
    name="Storage Room",
  )

  assert (
    update_location(
      location_id,
      description="Main storage area",
    )
    is True
  )

  location = get_location(location_id)

  assert location["description"] == "Main storage area"


def test_update_location_name_and_description(test_db):
  location_id = create_location(
    name="Storage Room",
    description="Old description",
  )

  assert (
    update_location(
      location_id,
      name="Main Storage",
      description="New description",
    )
    is True
  )

  location = get_location(location_id)

  assert location["name"] == "Main Storage"
  assert location["description"] == "New description"


def test_update_location_description_to_none(test_db):
  location_id = create_location(
    name="Storage Room",
    description="Main storage area",
  )

  assert (
    update_location(
      location_id,
      description=None,
    )
    is True
  )

  location = get_location(location_id)

  assert location["description"] is None


def test_update_location_without_changes_creates_no_audit_log(test_db):
  location_id = create_location(
    name="Storage Room",
  )

  assert update_location(location_id) is True

  logs = get_audit_logs(
    entity_type="location",
    entity_id=location_id,
  )

  assert len(logs) == 1
  assert logs[0]["action"] == "created"


def test_update_location_with_same_values_creates_no_audit_log(test_db):
  location_id = create_location(
    name="Storage Room",
    description="Main storage area",
  )

  assert (
    update_location(
      location_id,
      name="Storage Room",
      description="Main storage area",
    )
    is True
  )

  logs = get_audit_logs(
    entity_type="location",
    entity_id=location_id,
  )

  assert len(logs) == 1
  assert logs[0]["action"] == "created"


def test_update_location_creates_audit_log(test_db):
  location_id = create_location(
    name="Storage Room",
  )

  assert (
    update_location(
      location_id,
      name="Main Storage",
      description="Main storage area",
    )
    is True
  )

  logs = get_audit_logs(
    entity_type="location",
    entity_id=location_id,
  )

  assert len(logs) == 2
  assert logs[0]["action"] == "created"
  assert logs[1]["action"] == "updated"
  assert logs[1]["user_id"] == 1


def test_update_location_to_existing_name_fails(test_db):
  create_location(
    name="Storage Room",
  )

  location_id = create_location(
    name="Office",
  )

  with pytest.raises(ValueError):
    update_location(
      location_id,
      name="Storage Room",
    )


def test_update_nonexistent_location(test_db):
  assert (
    update_location(
      999,
      name="Storage Room",
    )
    is False
  )


def test_delete_location_requires_confirmation(test_db):
  location_id = create_location(
    name="Storage Room",
  )

  with pytest.raises(LocationDeletionConfirmationRequired):
    delete_location(location_id)

  assert get_location(location_id) is not None

  logs = get_audit_logs(
    entity_type="location",
    entity_id=location_id,
  )

  assert len(logs) == 1
  assert logs[0]["action"] == "created"


def test_delete_location(test_db):
  location_id = create_location(
    name="Storage Room",
  )

  assert (
    delete_location(
      location_id,
      confirm=True,
    )
    is True
  )

  assert get_location(location_id) is None


def test_delete_location_creates_audit_log(test_db):
  location_id = create_location(
    name="Storage Room",
  )

  assert (
    delete_location(
      location_id,
      confirm=True,
    )
    is True
  )

  logs = get_audit_logs(
    entity_type="location",
    entity_id=location_id,
  )

  assert len(logs) == 2
  assert logs[0]["action"] == "created"
  assert logs[1]["action"] == "deleted"
  assert logs[1]["user_id"] == 1


def test_delete_nonexistent_location(test_db):
  assert (
    delete_location(
      999,
      confirm=True,
    )
    is False
  )


def test_delete_location_sets_inventory_location_to_null(test_db):
  location_id = create_location(
    name="Storage Room",
  )

  item_id = create_item(
    name="Laptop",
    location_id=location_id,
  )

  assert (
    delete_location(
      location_id,
      confirm=True,
    )
    is True
  )

  item = get_item(item_id)

  assert item["location_id"] is None


def test_deleted_location_does_not_appear_in_get_locations(test_db):
  location_id = create_location(
    name="Storage Room",
  )

  assert (
    delete_location(
      location_id,
      confirm=True,
    )
    is True
  )

  locations = get_locations()

  assert all(location["id"] != location_id for location in locations)

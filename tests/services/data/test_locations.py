import pytest

from app.services.data.audit import get_audit_logs
from app.services.data.locations import (
  create_location,
  delete_location,
  get_location,
  get_location_by_name,
  get_locations,
  update_location,
)
from app.services.exceptions.data.common import InvalidInputError
from app.services.exceptions.data.locations import *


def test_create_location(gen_test_data_admin):
  location_id = create_location("Warehouse")

  assert location_id is not None

  location = get_location(location_id)

  assert location["id"] == location_id
  assert location["name"] == "Warehouse"
  assert location["description"] is None


def test_create_location_with_description(gen_test_data_admin):
  location_id = create_location(
    "Warehouse",
    description="Main storage area",
  )

  location = get_location(location_id)

  assert location["name"] == "Warehouse"
  assert location["description"] == "Main storage area"


def test_create_location_with_empty_name_fails(gen_test_data_admin):
  with pytest.raises(InvalidLocationNameError):
    create_location("")


def test_create_location_with_whitespace_name_fails(gen_test_data_admin):
  with pytest.raises(InvalidLocationNameError):
    create_location("   ")


def test_create_duplicate_location_fails(gen_test_data_admin):
  create_location("Warehouse")

  with pytest.raises(LocationAlreadyExistsError):
    create_location("Warehouse")


def test_get_location(gen_test_data_admin):
  location_id = create_location("Warehouse")

  location = get_location(location_id)

  assert location["id"] == location_id
  assert location["name"] == "Warehouse"


def test_get_nonexistent_location(gen_test_data_admin):
  assert get_location(999) is None


def test_get_locations(gen_test_data_admin):
  first_id = create_location("Warehouse")
  second_id = create_location("Office")

  locations = get_locations()

  assert len(locations) == 2
  assert locations[0]["id"] == first_id
  assert locations[1]["id"] == second_id


def test_update_location_name(gen_test_data_admin):
  location_id = create_location("Warehouse")

  assert (
    update_location(
      location_id,
      name="Main Warehouse",
    )
    is True
  )

  location = get_location(location_id)

  assert location["name"] == "Main Warehouse"


def test_update_location_description(gen_test_data_admin):
  location_id = create_location("Warehouse")

  assert (
    update_location(
      location_id,
      description="Storage area",
    )
    is True
  )

  location = get_location(location_id)

  assert location["description"] == "Storage area"


def test_update_location_name_and_description(gen_test_data_admin):
  location_id = create_location("Warehouse")

  assert (
    update_location(
      location_id,
      name="Main Warehouse",
      description="Main storage area",
    )
    is True
  )

  location = get_location(location_id)

  assert location["name"] == "Main Warehouse"
  assert location["description"] == "Main storage area"


def test_update_location_with_same_name_creates_no_audit_log(
  gen_test_data_admin,
):
  location_id = create_location("Warehouse")

  assert (
    update_location(
      location_id,
      name="Warehouse",
    )
    is True
  )

  logs = get_audit_logs(
    entity_type="location",
    entity_id=location_id,
  )

  assert len(logs) == 1
  assert logs[0]["action"] == "created"


def test_update_location_with_same_description_creates_no_audit_log(
  gen_test_data_admin,
):
  location_id = create_location(
    "Warehouse",
    description="Storage",
  )

  assert (
    update_location(
      location_id,
      description="Storage",
    )
    is True
  )

  logs = get_audit_logs(
    entity_type="location",
    entity_id=location_id,
  )

  assert len(logs) == 1
  assert logs[0]["action"] == "created"


def test_update_location_creates_audit_log(gen_test_data_admin):
  location_id = create_location("Warehouse")

  assert (
    update_location(
      location_id,
      name="Main Warehouse",
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


def test_update_location_to_existing_name_fails(gen_test_data_admin):
  create_location("Warehouse")
  location_id = create_location("Office")

  with pytest.raises(LocationAlreadyExistsError):
    update_location(
      location_id,
      name="Warehouse",
    )


def test_update_location_with_empty_name_fails(gen_test_data_admin):
  location_id = create_location("Warehouse")

  with pytest.raises(InvalidLocationNameError):
    update_location(
      location_id,
      name="",
    )


def test_update_nonexistent_location_fails(gen_test_data_admin):
  with pytest.raises(LocationNotFoundError):
    update_location(
      999,
      name="Warehouse",
    )


def test_update_location_with_no_fields_fails(gen_test_data_admin):
  location_id = create_location("Warehouse")

  with pytest.raises(InvalidInputError, match="No fields to update"):
    update_location(location_id)


def test_delete_location_requires_confirmation(gen_test_data_admin):
  location_id = create_location("Warehouse")

  with pytest.raises(
    LocationDeletionConfirmationRequired,
    match="Deleting a location requires confirmation",
  ):
    delete_location(location_id)


def test_delete_location(gen_test_data_admin):
  location_id = create_location("Warehouse")

  assert (
    delete_location(
      location_id,
      confirm=True,
    )
    is True
  )

  assert get_location(location_id) is None


def test_delete_nonexistent_location_fails(gen_test_data_admin):
  with pytest.raises(LocationNotFoundError):
    delete_location(
      999,
      confirm=True,
    )


def test_delete_location_creates_audit_log(gen_test_data_admin):
  location_id = create_location("Warehouse")

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


def test_update_location_creates_one_audit_log_for_multiple_changes(
  gen_test_data_admin,
):
  location_id = create_location(
    "Warehouse",
    description="Old description",
  )

  assert (
    update_location(
      location_id,
      name="Main Warehouse",
      description="New description",
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

  assert logs[1]["details"] == {
    "name": {
      "old": "Warehouse",
      "new": "Main Warehouse",
    },
    "description": {
      "old": "Old description",
      "new": "New description",
    },
  }


def test_get_location_by_name(gen_test_data_admin):
  location_id = create_location("Warehouse")

  location = get_location_by_name("Warehouse")

  assert location["id"] == location_id
  assert location["name"] == "Warehouse"


def test_get_nonexistent_location_by_name(gen_test_data_admin):
  assert get_location_by_name("does-not-exist") is None

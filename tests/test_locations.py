import pytest

from app.db import init_db
from app.services.inventory import create_item
from app.services.locations import (
  LocationInUseError,
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


def test_update_nonexistent_location(test_db):
  result = update_location(
    999,
    "Office",
  )

  assert result is False


def test_delete_location(test_db):
  location_id = create_location("Office")

  deleted = delete_location(location_id)

  assert deleted is True
  assert get_location(location_id) is None


def test_delete_nonexistent_location(test_db):
  assert delete_location(999) is False


def test_cannot_delete_location_with_inventory_item(test_db):
  location_id = create_location("Office")

  create_item(
    name="Laptop",
    location_id=location_id,
  )

  with pytest.raises(LocationInUseError):
    delete_location(location_id)

  assert get_location(location_id) is not None

import pytest

from app.services.checks import check_item
from app.services.data.audit import get_audit_logs
from app.services.data.inventory import (
  archive_item,
  create_item,
)
from app.services.exceptions.data.inventory import (
  ItemIsArchivedError,
  ItemNotFoundError,
)


def test_check_item(gen_test_data_admin):
  item_id = create_item("Laptop")

  item = check_item(item_id)

  assert item["id"] == item_id
  assert item["name"] == "Laptop"

  logs = get_audit_logs(
    entity_type="inventory_item",
    entity_id=item_id,
  )

  assert len(logs) == 2
  assert logs[-1]["user_id"] == gen_test_data_admin
  assert logs[-1]["action"] == "checked"
  assert logs[-1]["entity_type"] == "inventory_item"
  assert logs[-1]["entity_id"] == item_id


def test_check_item_not_found(gen_test_data_admin):
  with pytest.raises(ItemNotFoundError):
    check_item("does-not-exist")


def test_check_archived_item(gen_test_data_admin):
  item_id = create_item("Laptop")

  archive_item(item_id)

  with pytest.raises(ItemIsArchivedError):
    check_item(item_id)

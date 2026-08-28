import uuid

import pytest

from app.services.data.audit import get_audit_logs
from app.services.data.custom_field_values import set_custom_field_value
from app.services.data.custom_fields import create_custom_field
from app.services.data.inventory import (
  archive_item,
  create_item,
  get_item,
  get_items,
  get_items_paginated,
  restore_item,
  update_item,
)
from app.services.data.locations import create_location
from app.services.exceptions.data.common import InvalidInputError
from app.services.exceptions.data.inventory import *
from app.services.exceptions.data.locations import LocationNotFoundError


def test_create_item(gen_test_data_admin):
  item_id = create_item("Laptop")

  assert item_id is not None

  item = get_item(item_id)

  assert item["id"] == item_id
  assert item["name"] == "Laptop"
  assert item["location_id"] is None
  assert item["archived_at"] is None
  assert item["custom_fields"] == {}


def test_create_item_with_location(gen_test_data_admin):
  location_id = create_location("Storage")
  item_id = create_item(
    "Laptop",
    location_id=location_id,
  )

  item = get_item(item_id)

  assert item["location_id"] == location_id
  assert item["location_name"] == "Storage"


def test_create_item_with_empty_name_fails(gen_test_data_admin):
  with pytest.raises(InvalidItemNameError):
    create_item("")


def test_create_item_with_whitespace_name_fails(gen_test_data_admin):
  with pytest.raises(InvalidItemNameError):
    create_item("   ")


def test_create_item_with_non_string_name_fails(gen_test_data_admin):
  with pytest.raises(InvalidItemNameError):
    create_item(None)


def test_create_item_with_nonexistent_location_fails(gen_test_data_admin):
  with pytest.raises(LocationNotFoundError):
    create_item(
      "Laptop",
      location_id=999,
    )


def test_get_item(gen_test_data_admin):
  item_id = create_item("Laptop")

  item = get_item(item_id)

  assert item["id"] == item_id
  assert item["name"] == "Laptop"


def test_get_nonexistent_item(gen_test_data_admin):
  assert get_item("does-not-exist") is None


def test_get_items(gen_test_data_admin):
  create_item("Laptop")
  create_item("Monitor")

  items = get_items()

  assert len(items) == 2
  assert items[0]["name"] == "Laptop"
  assert items[1]["name"] == "Monitor"


def test_get_items_search(gen_test_data_admin):
  create_item("Gaming Laptop")
  create_item("Office Monitor")

  items = get_items(search="Laptop")

  assert len(items) == 1
  assert items[0]["name"] == "Gaming Laptop"


def test_get_items_search_is_partial(gen_test_data_admin):
  create_item("Gaming Laptop")

  items = get_items(search="Lap")

  assert len(items) == 1
  assert items[0]["name"] == "Gaming Laptop"


def test_get_items_by_location(gen_test_data_admin):
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


def test_get_items_with_nonexistent_location_fails(gen_test_data_admin):
  with pytest.raises(LocationNotFoundError):
    get_items(location_id=999)


def test_update_item_name(gen_test_data_admin):
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


def test_update_item_location(gen_test_data_admin):
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


def test_update_item_location_to_none(gen_test_data_admin):
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


def test_update_item_with_no_fields_fails(gen_test_data_admin):
  item_id = create_item("Laptop")

  with pytest.raises(
    InvalidInputError,
    match="No fields to update",
  ):
    update_item(item_id)


def test_update_nonexistent_item(gen_test_data_admin):
  with pytest.raises(ItemNotFoundError):
    update_item(
      "does-not-exist",
      name="Laptop",
    )


def test_update_archived_item_fails(gen_test_data_admin):
  item_id = create_item("Laptop")

  archive_item(item_id)

  with pytest.raises(ItemIsArchivedError):
    update_item(
      item_id,
      name="Desktop",
    )


def test_update_item_with_empty_name_fails(gen_test_data_admin):
  item_id = create_item("Laptop")

  with pytest.raises(InvalidItemNameError):
    update_item(
      item_id,
      name="",
    )


def test_update_item_with_nonexistent_location_fails(gen_test_data_admin):
  item_id = create_item("Laptop")

  with pytest.raises(LocationNotFoundError):
    update_item(
      item_id,
      location_id=999,
    )


def test_update_item_with_same_name_creates_no_audit_log(gen_test_data_admin):
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
  gen_test_data_admin,
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


def test_update_item_creates_audit_log(gen_test_data_admin):
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
  gen_test_data_admin,
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


def test_archive_item(gen_test_data_admin):
  item_id = create_item("Laptop")

  assert archive_item(item_id) is True

  item = get_item(item_id)

  assert item is None


def test_archive_item_creates_audit_log(gen_test_data_admin):
  item_id = create_item("Laptop")

  assert archive_item(item_id) is True

  logs = get_audit_logs(
    entity_type="inventory_item",
    entity_id=item_id,
  )

  assert len(logs) == 2
  assert logs[0]["action"] == "created"
  assert logs[1]["action"] == "archived"


def test_archive_already_archived_item_fails(gen_test_data_admin):
  item_id = create_item("Laptop")

  assert archive_item(item_id) is True

  with pytest.raises(ItemIsArchivedError):
    archive_item(item_id)


def test_archive_nonexistent_item(gen_test_data_admin):
  with pytest.raises(ItemNotFoundError):
    archive_item("does-not-exist")


def test_archived_item_excluded_from_get_items(gen_test_data_admin):
  item_id = create_item("Laptop")

  archive_item(item_id)

  assert get_items() == []


def test_archived_item_included_when_requested(gen_test_data_admin):
  item_id = create_item("Laptop")

  archive_item(item_id)

  items = get_items(include_archived=True)

  assert len(items) == 1
  assert items[0]["id"] == item_id
  assert items[0]["name"] == "Laptop"
  assert items[0]["archived_at"] is not None


def test_restore_item(gen_test_data_admin):
  item_id = create_item("Laptop")

  archive_item(item_id)

  assert restore_item(item_id) is True

  item = get_item(item_id)

  assert item is not None
  assert item["name"] == "Laptop"
  assert item["archived_at"] is None


def test_restore_item_creates_audit_log(gen_test_data_admin):
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


def test_restore_active_item_fails(gen_test_data_admin):
  item_id = create_item("Laptop")

  with pytest.raises(ItemIsNotArchivedError):
    restore_item(item_id)


def test_restore_nonexistent_item(gen_test_data_admin):
  with pytest.raises(ItemNotFoundError):
    restore_item("does-not-exist")


def test_archived_item_can_be_restored_and_found_again(gen_test_data_admin):
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
  gen_test_data_admin,
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


def test_create_item_generates_uuid(gen_test_data_admin):
  item_id = create_item("Test Asset")

  assert uuid.UUID(item_id).version == 4


def test_create_item_generates_unique_ids(gen_test_data_admin):
  first_id = create_item("First Asset")
  second_id = create_item("Second Asset")

  assert first_id != second_id


def test_archived_asset_is_distinguishable(
  gen_test_data_admin,
):
  item_id = create_item("Laptop")

  active_item = get_item(item_id)
  assert active_item["archived_at"] is None

  archive_item(item_id)

  archived_item = get_item(
    item_id,
    include_archived=True,
  )

  assert archived_item["archived_at"] is not None


def test_get_items_search_and_location(gen_test_data_admin):
  storage_id = create_location("Storage")
  office_id = create_location("Office")

  create_item(
    "Gaming Laptop",
    location_id=storage_id,
  )
  create_item(
    "Office Laptop",
    location_id=office_id,
  )
  create_item(
    "Gaming Monitor",
    location_id=storage_id,
  )

  items = get_items(
    search="Laptop",
    location_id=storage_id,
  )

  assert len(items) == 1
  assert items[0]["name"] == "Gaming Laptop"


def test_get_items_sort_by_name_ascending(gen_test_data_admin):
  create_item("Monitor")
  create_item("Laptop")
  create_item("Keyboard")

  items = get_items(
    sort_by="name",
    sort_order="asc",
  )

  assert [item["name"] for item in items] == [
    "Keyboard",
    "Laptop",
    "Monitor",
  ]


def test_get_items_sort_by_name_descending(gen_test_data_admin):
  create_item("Monitor")
  create_item("Laptop")
  create_item("Keyboard")

  items = get_items(
    sort_by="name",
    sort_order="desc",
  )

  assert [item["name"] for item in items] == [
    "Monitor",
    "Laptop",
    "Keyboard",
  ]


def test_get_items_filter_by_custom_field(gen_test_data_admin):
  field_id = create_custom_field(
    "Department",
    "text",
  )

  it_item_id = create_item("Laptop")
  hr_item_id = create_item("Monitor")

  set_custom_field_value(
    it_item_id,
    field_id,
    "IT",
  )
  set_custom_field_value(
    hr_item_id,
    field_id,
    "HR",
  )

  items = get_items(
    custom_fields={
      field_id: "IT",
    },
  )

  assert [item["id"] for item in items] == [it_item_id]


def test_get_items_filter_by_multiple_custom_fields(gen_test_data_admin):
  department_id = create_custom_field(
    "Department",
    "text",
  )
  type_id = create_custom_field(
    "Type",
    "text",
  )

  matching_id = create_item("Laptop")
  department_only_id = create_item("Monitor")
  type_only_id = create_item("Keyboard")

  set_custom_field_value(matching_id, department_id, "IT")
  set_custom_field_value(matching_id, type_id, "Hardware")

  set_custom_field_value(department_only_id, department_id, "IT")
  set_custom_field_value(type_only_id, type_id, "Hardware")

  items = get_items(
    custom_fields={
      department_id: "IT",
      type_id: "Hardware",
    },
  )

  assert [item["id"] for item in items] == [matching_id]


def test_get_items_sort_by_custom_field(gen_test_data_admin):
  field_id = create_custom_field(
    "Department",
    "text",
  )

  it_id = create_item("Laptop")
  hr_id = create_item("Monitor")
  finance_id = create_item("Keyboard")

  set_custom_field_value(it_id, field_id, "IT")
  set_custom_field_value(hr_id, field_id, "HR")
  set_custom_field_value(finance_id, field_id, "Finance")

  items = get_items(
    sort_by=field_id,
    sort_order="asc",
  )

  assert [item["id"] for item in items] == [
    finance_id,
    hr_id,
    it_id,
  ]


def test_get_items_sort_by_integer_custom_field(gen_test_data_admin):
  field_id = create_custom_field(
    "Quantity",
    "integer",
  )

  item_2_id = create_item("Item 2")
  item_10_id = create_item("Item 10")
  item_100_id = create_item("Item 100")

  set_custom_field_value(item_2_id, field_id, 2)
  set_custom_field_value(item_10_id, field_id, 10)
  set_custom_field_value(item_100_id, field_id, 100)

  items = get_items(
    sort_by=field_id,
    sort_order="asc",
  )

  assert [item["id"] for item in items] == [
    item_2_id,
    item_10_id,
    item_100_id,
  ]


def test_get_items_sort_by_custom_field_descending(gen_test_data_admin):
  field_id = create_custom_field(
    "Department",
    "text",
  )

  it_id = create_item("Laptop")
  hr_id = create_item("Monitor")
  finance_id = create_item("Keyboard")

  set_custom_field_value(it_id, field_id, "IT")
  set_custom_field_value(hr_id, field_id, "HR")
  set_custom_field_value(finance_id, field_id, "Finance")

  items = get_items(
    sort_by=field_id,
    sort_order="desc",
  )

  assert [item["id"] for item in items] == [
    it_id,
    hr_id,
    finance_id,
  ]


def test_get_items_with_invalid_sort_field_fails(gen_test_data_admin):
  create_item("Laptop")

  with pytest.raises(InvalidInputError):
    get_items(
      sort_by="invalid",
      sort_order="asc",
    )


def test_get_items_with_invalid_sort_order_fails(gen_test_data_admin):
  create_item("Laptop")

  with pytest.raises(InvalidInputError):
    get_items(
      sort_by="name",
      sort_order="invalid",
    )


def test_get_items_filter_by_custom_field_excludes_missing_values(
  gen_test_data_admin,
):
  field_id = create_custom_field(
    "Department",
    "text",
  )

  matching_id = create_item("Laptop")
  create_item("Monitor")

  set_custom_field_value(
    matching_id,
    field_id,
    "IT",
  )

  items = get_items(
    custom_fields={
      field_id: "IT",
    },
  )

  assert [item["id"] for item in items] == [matching_id]


def test_get_items_sort_by_custom_field_with_missing_values(
  gen_test_data_admin,
):
  field_id = create_custom_field(
    "Department",
    "text",
  )

  it_id = create_item("Laptop")
  missing_id = create_item("Monitor")
  hr_id = create_item("Keyboard")

  set_custom_field_value(
    it_id,
    field_id,
    "IT",
  )
  set_custom_field_value(
    hr_id,
    field_id,
    "HR",
  )

  items = get_items(
    sort_by=field_id,
    sort_order="asc",
  )

  assert [item["id"] for item in items] == [
    missing_id,
    hr_id,
    it_id,
  ]


def test_archived_items_are_excluded_from_search_and_sort(
  gen_test_data_admin,
):
  active_id = create_item("Laptop")
  archived_id = create_item("Monitor")

  archive_item(archived_id)

  items = get_items(
    search="",
    sort_by="name",
    sort_order="asc",
  )

  assert [item["id"] for item in items] == [active_id]


def test_archived_items_are_excluded_from_custom_field_filter(
  gen_test_data_admin,
):
  field_id = create_custom_field(
    "Department",
    "text",
  )

  active_id = create_item("Laptop")
  archived_id = create_item("Monitor")

  set_custom_field_value(
    active_id,
    field_id,
    "IT",
  )
  set_custom_field_value(
    archived_id,
    field_id,
    "IT",
  )

  archive_item(archived_id)

  items = get_items(
    custom_fields={
      field_id: "IT",
    },
  )

  assert [item["id"] for item in items] == [active_id]


def test_archived_items_can_be_included_in_search_and_sort(
  gen_test_data_admin,
):
  active_id = create_item("Laptop")
  archived_id = create_item("Monitor")

  archive_item(archived_id)

  items = get_items(
    include_archived=True,
    sort_by="name",
    sort_order="asc",
  )

  assert [item["id"] for item in items] == [
    active_id,
    archived_id,
  ]


def test_get_items_sort_by_decimal_custom_field(gen_test_data_admin):
  field_id = create_custom_field(
    "Price",
    "decimal",
  )

  item_2_id = create_item("Item 2")
  item_10_id = create_item("Item 10")
  item_100_id = create_item("Item 100")

  set_custom_field_value(item_2_id, field_id, 2.5)
  set_custom_field_value(item_10_id, field_id, 10.25)
  set_custom_field_value(item_100_id, field_id, 100.75)

  items = get_items(
    sort_by=field_id,
    sort_order="asc",
  )

  assert [item["id"] for item in items] == [
    item_2_id,
    item_10_id,
    item_100_id,
  ]


def test_get_items_sort_by_boolean_custom_field(gen_test_data_admin):
  field_id = create_custom_field(
    "Active",
    "boolean",
  )

  false_id = create_item("False")
  true_id = create_item("True")

  set_custom_field_value(false_id, field_id, False)
  set_custom_field_value(true_id, field_id, True)

  items = get_items(
    sort_by=field_id,
    sort_order="asc",
  )

  assert [item["id"] for item in items] == [
    false_id,
    true_id,
  ]


def test_get_items_sort_by_custom_field_descending_with_missing_values(
  gen_test_data_admin,
):
  field_id = create_custom_field(
    "Department",
    "text",
  )

  missing_id = create_item("Missing")
  it_id = create_item("IT")
  hr_id = create_item("HR")

  set_custom_field_value(
    it_id,
    field_id,
    "IT",
  )
  set_custom_field_value(
    hr_id,
    field_id,
    "HR",
  )

  items = get_items(
    sort_by=field_id,
    sort_order="desc",
  )

  assert [item["id"] for item in items] == [
    missing_id,
    it_id,
    hr_id,
  ]


def test_get_items_paginated_returns_first_page(
  gen_test_admin,
  gen_test_item,
):
  gen_test_item(name="Apple")
  gen_test_item(name="Banana")
  gen_test_item(name="Cherry")

  result = get_items_paginated(
    page=1,
    per_page=2,
  )

  assert result["items"][0]["name"] == "Apple"
  assert result["items"][1]["name"] == "Banana"
  assert result["page"] == 1
  assert result["per_page"] == 2
  assert result["total"] == 3
  assert result["total_pages"] == 2


def test_get_items_paginated_returns_second_page(
  gen_test_admin,
  gen_test_item,
):
  gen_test_item(name="Apple")
  gen_test_item(name="Banana")
  gen_test_item(name="Cherry")

  result = get_items_paginated(
    page=2,
    per_page=2,
  )

  assert len(result["items"]) == 1
  assert result["items"][0]["name"] == "Cherry"
  assert result["page"] == 2
  assert result["per_page"] == 2
  assert result["total"] == 3
  assert result["total_pages"] == 2


def test_get_items_paginated_respects_search(
  gen_test_admin,
  gen_test_item,
):
  gen_test_item(name="Apple")
  gen_test_item(name="Apple Keyboard")
  gen_test_item(name="Banana")

  result = get_items_paginated(
    search="Apple",
    page=1,
    per_page=10,
  )

  assert [item["name"] for item in result["items"]] == [
    "Apple",
    "Apple Keyboard",
  ]
  assert result["total"] == 2
  assert result["total_pages"] == 1


def test_get_items_paginated_respects_location(
  gen_test_admin,
  gen_test_location,
  gen_test_item,
):
  location = gen_test_location(name="Storage")

  gen_test_item(
    name="Stored 1",
    location_id=location,
  )
  gen_test_item(
    name="Stored 2",
    location_id=location,
  )
  gen_test_item(name="Other")

  result = get_items_paginated(
    location_id=location,
    page=1,
    per_page=10,
  )

  assert [item["name"] for item in result["items"]] == [
    "Stored 1",
    "Stored 2",
  ]
  assert result["total"] == 2


def test_get_items_paginated_respects_sorting(
  gen_test_admin,
  gen_test_item,
):
  gen_test_item(name="Apple")
  gen_test_item(name="Banana")
  gen_test_item(name="Cherry")

  result = get_items_paginated(
    sort_by="name",
    sort_order="desc",
    page=1,
    per_page=10,
  )

  assert [item["name"] for item in result["items"]] == [
    "Cherry",
    "Banana",
    "Apple",
  ]


def test_get_items_paginated_rejects_invalid_page(
  gen_test_admin,
):
  with pytest.raises(InvalidInputError):
    get_items_paginated(page=0)


def test_get_items_paginated_rejects_invalid_per_page(
  gen_test_admin,
):
  with pytest.raises(InvalidInputError):
    get_items_paginated(per_page=0)

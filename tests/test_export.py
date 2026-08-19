import csv
import io

import pytest

from app.services.audit import get_audit_logs
from app.services.custom_field_values import set_custom_field_value
from app.services.custom_fields import create_custom_field
from app.services.export import export_inventory
from app.services.inventory import archive_item, create_item
from app.services.locations import create_location
from app.services.permissions import create_permission
from app.services.user_permissions import assign_permission_to_user


def _read_csv(content):
  return list(csv.DictReader(io.StringIO(content)))


def _csv_headers(content):
  reader = csv.reader(io.StringIO(content))
  return next(reader)


def _grant_export_permission(user_id):
  permission_id = create_permission(
    name="inventory.export",
  )

  assign_permission_to_user(
    user_id,
    permission_id,
  )


def _grant_field_read_permission(user_id, field_id):
  permission_id = create_permission(
    name=f"field.{field_id}.read",
  )

  assign_permission_to_user(
    user_id,
    permission_id,
  )


def test_export_requires_inventory_export_permission(
  test_db,
  authenticated_test_user,
):
  create_item("Laptop")

  with pytest.raises(PermissionError):
    export_inventory(
      authenticated_test_user,
    )


def test_export_returns_csv(
  test_db,
  authenticated_test_user,
):
  _grant_export_permission(
    authenticated_test_user,
  )

  create_item("Laptop")

  content = export_inventory(
    authenticated_test_user,
  )

  assert isinstance(content, str)
  assert _csv_headers(content) == [
    "id",
    "name",
    "location",
  ]


def test_export_includes_multiple_items(
  test_db,
  authenticated_test_user,
):
  _grant_export_permission(
    authenticated_test_user,
  )

  first_id = create_item("Laptop")
  second_id = create_item("Monitor")

  rows = _read_csv(
    export_inventory(
      authenticated_test_user,
    )
  )

  exported_ids = [row["id"] for row in rows]

  assert exported_ids == sorted(
    [
      first_id,
      second_id,
    ]
  )


def test_export_excludes_archived_items(
  test_db,
  authenticated_test_user,
):
  _grant_export_permission(
    authenticated_test_user,
  )

  active_id = create_item("Laptop")
  archived_id = create_item("Monitor")

  assert archive_item(archived_id) is True

  rows = _read_csv(
    export_inventory(
      authenticated_test_user,
    )
  )

  exported_ids = [row["id"] for row in rows]

  assert active_id in exported_ids
  assert archived_id not in exported_ids


def test_export_can_filter_by_search(
  test_db,
  authenticated_test_user,
):
  _grant_export_permission(
    authenticated_test_user,
  )

  laptop_id = create_item("Gaming Laptop")
  monitor_id = create_item("4K Monitor")

  rows = _read_csv(
    export_inventory(
      authenticated_test_user,
      search="Laptop",
    )
  )

  exported_ids = [row["id"] for row in rows]

  assert exported_ids == [laptop_id]
  assert monitor_id not in exported_ids


def test_export_can_filter_by_location(
  test_db,
  authenticated_test_user,
):
  _grant_export_permission(
    authenticated_test_user,
  )

  warehouse_id = create_location(
    name="Warehouse",
  )
  office_id = create_location(
    name="Office",
  )

  warehouse_item_id = create_item(
    "Laptop",
    location_id=warehouse_id,
  )
  office_item_id = create_item(
    "Monitor",
    location_id=office_id,
  )

  rows = _read_csv(
    export_inventory(
      authenticated_test_user,
      location_id=warehouse_id,
    )
  )

  exported_ids = [row["id"] for row in rows]

  assert exported_ids == [warehouse_item_id]
  assert office_item_id not in exported_ids


def test_export_can_select_fields(
  test_db,
  authenticated_test_user,
):
  _grant_export_permission(
    authenticated_test_user,
  )

  create_item("Laptop")

  content = export_inventory(
    authenticated_test_user,
    fields=[
      "id",
      "name",
    ],
  )

  assert _csv_headers(content) == [
    "id",
    "name",
  ]


def test_export_includes_custom_fields_with_values(
  test_db,
  authenticated_test_user,
):
  _grant_export_permission(
    authenticated_test_user,
  )

  field_id = create_custom_field(
    name="Purchase Price",
    field_type="decimal",
  )

  _grant_field_read_permission(
    authenticated_test_user,
    field_id,
  )

  item_id = create_item("Laptop")

  set_custom_field_value(
    item_id,
    field_id,
    "45000",
  )

  content = export_inventory(
    authenticated_test_user,
  )

  assert "Purchase Price" in _csv_headers(content)

  rows = _read_csv(content)

  assert rows[0]["Purchase Price"] == "45000"


def test_export_leaves_custom_field_blank_when_item_has_no_value(
  test_db,
  authenticated_test_user,
):
  _grant_export_permission(
    authenticated_test_user,
  )

  field_id = create_custom_field(
    name="Purchase Price",
    field_type="decimal",
  )

  _grant_field_read_permission(
    authenticated_test_user,
    field_id,
  )

  item_with_value_id = create_item("Laptop")
  item_without_value_id = create_item("Monitor")

  set_custom_field_value(
    item_with_value_id,
    field_id,
    "45000",
  )

  rows = _read_csv(
    export_inventory(
      authenticated_test_user,
    )
  )

  rows_by_id = {row["id"]: row for row in rows}

  assert rows_by_id[item_with_value_id]["Purchase Price"] == "45000"
  assert rows_by_id[item_without_value_id]["Purchase Price"] == ""


def test_export_prunes_custom_field_with_no_values(
  test_db,
  authenticated_test_user,
):
  _grant_export_permission(
    authenticated_test_user,
  )

  field_id = create_custom_field(
    name="Purchase Price",
    field_type="decimal",
  )

  _grant_field_read_permission(
    authenticated_test_user,
    field_id,
  )

  create_item("Laptop")

  content = export_inventory(
    authenticated_test_user,
  )

  assert "Purchase Price" not in _csv_headers(content)


def test_export_omits_unauthorized_custom_field(
  test_db,
  authenticated_test_user,
):
  _grant_export_permission(
    authenticated_test_user,
  )

  field_id = create_custom_field(
    name="Purchase Price",
    field_type="decimal",
  )

  item_id = create_item("Laptop")

  set_custom_field_value(
    item_id,
    field_id,
    "45000",
  )

  content = export_inventory(
    authenticated_test_user,
  )

  assert "Purchase Price" not in _csv_headers(content)


def test_export_omits_unauthorized_custom_field_even_with_read_permission_for_different_field(
  test_db,
  authenticated_test_user,
):
  _grant_export_permission(
    authenticated_test_user,
  )

  visible_field_id = create_custom_field(
    name="Purchase Price",
    field_type="decimal",
  )

  hidden_field_id = create_custom_field(
    name="Supplier",
    field_type="text",
  )

  _grant_field_read_permission(
    authenticated_test_user,
    visible_field_id,
  )

  item_id = create_item("Laptop")

  set_custom_field_value(
    item_id,
    visible_field_id,
    "45000",
  )

  set_custom_field_value(
    item_id,
    hidden_field_id,
    "Acme",
  )

  content = export_inventory(
    authenticated_test_user,
  )

  headers = _csv_headers(content)

  assert "Purchase Price" in headers
  assert "Supplier" not in headers


def test_export_includes_all_custom_fields_that_have_values(
  test_db,
  authenticated_test_user,
):
  _grant_export_permission(
    authenticated_test_user,
  )

  purchase_price_id = create_custom_field(
    name="Purchase Price",
    field_type="decimal",
  )

  supplier_id = create_custom_field(
    name="Supplier",
    field_type="text",
  )

  serial_number_id = create_custom_field(
    name="Serial Number",
    field_type="text",
  )

  _grant_field_read_permission(
    authenticated_test_user,
    purchase_price_id,
  )
  _grant_field_read_permission(
    authenticated_test_user,
    supplier_id,
  )
  _grant_field_read_permission(
    authenticated_test_user,
    serial_number_id,
  )

  item_id = create_item("Laptop")

  set_custom_field_value(
    item_id,
    purchase_price_id,
    "45000",
  )

  set_custom_field_value(
    item_id,
    supplier_id,
    "Acme",
  )

  set_custom_field_value(
    item_id,
    serial_number_id,
    "SN-123",
  )

  content = export_inventory(
    authenticated_test_user,
  )

  headers = _csv_headers(content)

  assert "Purchase Price" in headers
  assert "Supplier" in headers
  assert "Serial Number" in headers


def test_export_prunes_custom_fields_with_no_values(
  test_db,
  authenticated_test_user,
):
  _grant_export_permission(
    authenticated_test_user,
  )

  populated_field_id = create_custom_field(
    name="Purchase Price",
    field_type="decimal",
  )

  empty_field_id = create_custom_field(
    name="Supplier",
    field_type="text",
  )

  _grant_field_read_permission(
    authenticated_test_user,
    populated_field_id,
  )
  _grant_field_read_permission(
    authenticated_test_user,
    empty_field_id,
  )

  item_id = create_item("Laptop")

  set_custom_field_value(
    item_id,
    populated_field_id,
    "45000",
  )

  content = export_inventory(
    authenticated_test_user,
  )

  headers = _csv_headers(content)

  assert "Purchase Price" in headers
  assert "Supplier" not in headers


def test_export_has_headers_when_empty(
  test_db,
  authenticated_test_user,
):
  _grant_export_permission(
    authenticated_test_user,
  )

  content = export_inventory(
    authenticated_test_user,
  )

  assert _csv_headers(content) == [
    "id",
    "name",
    "location",
  ]


def test_export_creates_audit_log(
  test_db,
  authenticated_test_user,
):
  _grant_export_permission(
    authenticated_test_user,
  )

  create_item("Laptop")

  export_inventory(
    authenticated_test_user,
  )

  logs = get_audit_logs(
    entity_type="inventory_export",
  )

  assert len(logs) == 1
  assert logs[0]["user_id"] == authenticated_test_user
  assert logs[0]["action"] == "created"


def test_export_audit_log_created_for_empty_export(
  test_db,
  authenticated_test_user,
):
  _grant_export_permission(
    authenticated_test_user,
  )

  export_inventory(
    authenticated_test_user,
  )

  logs = get_audit_logs(
    entity_type="inventory_export",
  )

  assert len(logs) == 1
  assert logs[0]["user_id"] == authenticated_test_user
  assert logs[0]["action"] == "created"


def test_export_selected_fields_can_include_custom_fields(
  test_db,
  authenticated_test_user,
):
  _grant_export_permission(
    authenticated_test_user,
  )

  field_id = create_custom_field(
    name="Purchase Price",
    field_type="decimal",
  )

  _grant_field_read_permission(
    authenticated_test_user,
    field_id,
  )

  item_id = create_item("Laptop")

  set_custom_field_value(
    item_id,
    field_id,
    "45000",
  )

  content = export_inventory(
    authenticated_test_user,
    fields=[
      "id",
      "Purchase Price",
    ],
  )

  assert _csv_headers(content) == [
    "id",
    "Purchase Price",
  ]

  rows = _read_csv(content)

  assert rows[0]["id"] == item_id
  assert rows[0]["Purchase Price"] == "45000"


def test_export_selected_unauthorized_custom_field_is_omitted(
  test_db,
  authenticated_test_user,
):
  _grant_export_permission(
    authenticated_test_user,
  )

  field_id = create_custom_field(
    name="Purchase Price",
    field_type="decimal",
  )

  item_id = create_item("Laptop")

  set_custom_field_value(
    item_id,
    field_id,
    "45000",
  )

  content = export_inventory(
    authenticated_test_user,
    fields=[
      "id",
      "Purchase Price",
    ],
  )

  assert _csv_headers(content) == [
    "id",
  ]


def test_export_location_is_included_by_name(
  test_db,
  authenticated_test_user,
):
  _grant_export_permission(
    authenticated_test_user,
  )

  location_id = create_location(
    name="Warehouse",
  )

  create_item(
    "Laptop",
    location_id=location_id,
  )

  content = export_inventory(
    authenticated_test_user,
  )

  rows = _read_csv(content)

  assert rows[0]["location"] == "Warehouse"


def test_export_null_location_is_blank(
  test_db,
  authenticated_test_user,
):
  _grant_export_permission(
    authenticated_test_user,
  )

  create_item("Laptop")

  content = export_inventory(
    authenticated_test_user,
  )

  rows = _read_csv(content)

  assert rows[0]["location"] == ""


def test_export_excludes_archived_items(
  test_db,
  authenticated_test_user,
):
  _grant_export_permission(
    authenticated_test_user,
  )

  active_id = create_item("Laptop")
  archived_id = create_item("Monitor")

  assert archive_item(archived_id) is True

  rows = _read_csv(
    export_inventory(
      authenticated_test_user,
    )
  )

  exported_ids = [row["id"] for row in rows]

  assert active_id in exported_ids
  assert archived_id not in exported_ids


def test_export_search_filter(
  test_db,
  authenticated_test_user,
):
  _grant_export_permission(
    authenticated_test_user,
  )

  matching_id = create_item("Laptop")
  non_matching_id = create_item("Monitor")

  rows = _read_csv(
    export_inventory(
      authenticated_test_user,
      search="Laptop",
    )
  )

  exported_ids = [row["id"] for row in rows]

  assert exported_ids == [matching_id]
  assert non_matching_id not in exported_ids


def test_export_location_filter(
  test_db,
  authenticated_test_user,
):
  _grant_export_permission(
    authenticated_test_user,
  )

  first_location_id = create_location(
    name="Warehouse",
  )
  second_location_id = create_location(
    name="Office",
  )

  matching_id = create_item(
    "Laptop",
    location_id=first_location_id,
  )
  non_matching_id = create_item(
    "Monitor",
    location_id=second_location_id,
  )

  rows = _read_csv(
    export_inventory(
      authenticated_test_user,
      location_id=first_location_id,
    )
  )

  exported_ids = [row["id"] for row in rows]

  assert exported_ids == [matching_id]
  assert non_matching_id not in exported_ids


def test_export_omits_unauthorized_custom_fields(
  test_db,
  authenticated_test_user,
):
  _grant_export_permission(
    authenticated_test_user,
  )

  allowed_field_id = create_custom_field(
    name="Purchase Price",
    field_type="decimal",
  )
  denied_field_id = create_custom_field(
    name="Supplier Cost",
    field_type="decimal",
  )

  _grant_field_read_permission(
    authenticated_test_user,
    allowed_field_id,
  )

  item_id = create_item("Laptop")

  set_custom_field_value(
    item_id,
    allowed_field_id,
    "45000",
  )
  set_custom_field_value(
    item_id,
    denied_field_id,
    "30000",
  )

  content = export_inventory(
    authenticated_test_user,
  )

  headers = _csv_headers(content)

  assert "Purchase Price" in headers
  assert "Supplier Cost" not in headers


def test_export_invalid_field_is_rejected(
  test_db,
  authenticated_test_user,
):
  _grant_export_permission(
    authenticated_test_user,
  )

  create_item("Laptop")

  with pytest.raises(ValueError):
    export_inventory(
      authenticated_test_user,
      fields=[
        "id",
        "does_not_exist",
      ],
    )


def test_export_empty_result_returns_valid_csv(
  test_db,
  authenticated_test_user,
):
  _grant_export_permission(
    authenticated_test_user,
  )

  content = export_inventory(
    authenticated_test_user,
    search="does-not-exist",
  )

  assert _csv_headers(content) == [
    "id",
    "name",
    "location",
  ]

  assert _read_csv(content) == []


def test_export_escapes_csv_values(
  test_db,
  authenticated_test_user,
):
  _grant_export_permission(
    authenticated_test_user,
  )

  field_id = create_custom_field(
    name="Description",
    field_type="text",
  )

  _grant_field_read_permission(
    authenticated_test_user,
    field_id,
  )

  item_id = create_item(
    'Laptop, "Gaming"',
  )

  set_custom_field_value(
    item_id,
    field_id,
    'Fast, powerful "gaming" laptop',
  )

  content = export_inventory(
    authenticated_test_user,
  )

  rows = _read_csv(content)

  assert rows[0]["id"] == item_id
  assert rows[0]["name"] == 'Laptop, "Gaming"'
  assert rows[0]["Description"] == 'Fast, powerful "gaming" laptop'


def test_export_preserves_newlines_in_csv_values(
  test_db,
  authenticated_test_user,
):
  _grant_export_permission(
    authenticated_test_user,
  )

  field_id = create_custom_field(
    name="Notes",
    field_type="text",
  )

  _grant_field_read_permission(
    authenticated_test_user,
    field_id,
  )

  item_id = create_item("Laptop")

  set_custom_field_value(
    item_id,
    field_id,
    "Line one\nLine two",
  )

  content = export_inventory(
    authenticated_test_user,
  )

  rows = _read_csv(content)

  assert rows[0]["Notes"] == "Line one\nLine two"


def test_export_header_order_is_deterministic(
  test_db,
  authenticated_test_user,
):
  _grant_export_permission(
    authenticated_test_user,
  )

  first_field_id = create_custom_field(
    name="Purchase Price",
    field_type="decimal",
  )
  second_field_id = create_custom_field(
    name="Supplier",
    field_type="text",
  )

  _grant_field_read_permission(
    authenticated_test_user,
    first_field_id,
  )
  _grant_field_read_permission(
    authenticated_test_user,
    second_field_id,
  )

  item_id = create_item("Laptop")

  set_custom_field_value(
    item_id,
    first_field_id,
    "45000",
  )
  set_custom_field_value(
    item_id,
    second_field_id,
    "Acme",
  )

  content = export_inventory(
    authenticated_test_user,
  )

  assert _csv_headers(content) == [
    "id",
    "name",
    "location",
    "Purchase Price",
    "Supplier",
  ]

import csv
import io

import pytest
from app.services.import_inventory import import_inventory

from app.services.audit import get_audit_logs
from app.services.custom_field_values import get_custom_field_value
from app.services.custom_fields import create_custom_field
from app.services.inventory import get_item, get_items
from app.services.permissions import create_permission
from app.services.user_permissions import assign_permission_to_user


def _csv_content(headers, rows):
  output = io.StringIO()

  writer = csv.DictWriter(
    output,
    fieldnames=headers,
  )

  writer.writeheader()
  writer.writerows(rows)

  return output.getvalue()


def _grant_import_permission(user_id):
  permission_id = create_permission(
    name="inventory.import",
  )

  assign_permission_to_user(
    user_id,
    permission_id,
  )


def _grant_field_update_permission(user_id, field_id):
  permission_id = create_permission(
    name=f"field.{field_id}.update",
  )

  assign_permission_to_user(
    user_id,
    permission_id,
  )


def test_import_requires_inventory_import_permission(
  test_db,
  authenticated_test_user,
):
  content = _csv_content(
    ["name"],
    [
      {"name": "Laptop"},
    ],
  )

  with pytest.raises(PermissionError):
    import_inventory(
      authenticated_test_user,
      content,
    )


def test_import_creates_item(
  test_db,
  authenticated_test_user,
):
  _grant_import_permission(
    authenticated_test_user,
  )

  content = _csv_content(
    ["name"],
    [
      {"name": "Laptop"},
    ],
  )

  result = import_inventory(
    authenticated_test_user,
    content,
  )

  assert len(result) == 1

  item_id = result[0]["id"]

  assert result[0]["name"] == "Laptop"

  item = get_item(item_id)

  assert item is not None
  assert item["name"] == "Laptop"


def test_import_generates_uuid_when_id_is_missing(
  test_db,
  authenticated_test_user,
):
  _grant_import_permission(
    authenticated_test_user,
  )

  content = _csv_content(
    ["name"],
    [
      {"name": "Laptop"},
    ],
  )

  result = import_inventory(
    authenticated_test_user,
    content,
  )

  item_id = result[0]["id"]

  assert len(item_id) == 36
  assert item_id.count("-") == 4


def test_import_uses_provided_id(
  test_db,
  authenticated_test_user,
):
  _grant_import_permission(
    authenticated_test_user,
  )

  item_id = "11111111-1111-1111-1111-111111111111"

  content = _csv_content(
    ["id", "name"],
    [
      {
        "id": item_id,
        "name": "Laptop",
      },
    ],
  )

  result = import_inventory(
    authenticated_test_user,
    content,
  )

  assert result[0]["id"] == item_id
  assert get_item(item_id) is not None


def test_import_requires_name(
  test_db,
  authenticated_test_user,
):
  _grant_import_permission(
    authenticated_test_user,
  )

  content = _csv_content(
    ["id", "name"],
    [
      {
        "id": "",
        "name": "",
      },
    ],
  )

  with pytest.raises(ValueError):
    import_inventory(
      authenticated_test_user,
      content,
    )

  assert get_items() == []


def test_import_rejects_unknown_field(
  test_db,
  authenticated_test_user,
):
  _grant_import_permission(
    authenticated_test_user,
  )

  content = _csv_content(
    ["name", "Does Not Exist"],
    [
      {
        "name": "Laptop",
        "Does Not Exist": "value",
      },
    ],
  )

  with pytest.raises(ValueError):
    import_inventory(
      authenticated_test_user,
      content,
    )

  assert get_items() == []


def test_import_rejects_duplicate_id(
  test_db,
  authenticated_test_user,
):
  _grant_import_permission(
    authenticated_test_user,
  )

  item_id = "11111111-1111-1111-1111-111111111111"

  content = _csv_content(
    ["id", "name"],
    [
      {
        "id": item_id,
        "name": "Laptop",
      },
      {
        "id": item_id,
        "name": "Monitor",
      },
    ],
  )

  with pytest.raises(ValueError):
    import_inventory(
      authenticated_test_user,
      content,
    )

  assert get_items() == []


def test_import_rejects_existing_id(
  test_db,
  authenticated_test_user,
):
  _grant_import_permission(
    authenticated_test_user,
  )

  item_id = "11111111-1111-1111-1111-111111111111"

  from app.services.inventory import create_item

  create_item("Existing", location_id=None)

  # Use a directly supplied ID by creating the required record first
  connection = __import__("app.db", fromlist=["get_db"]).get_db()

  try:
    connection.execute(
      """
      UPDATE inventory_items
      SET id = ?
      WHERE name = ?
      """,
      (
        item_id,
        "Existing",
      ),
    )

    connection.commit()
  finally:
    connection.close()

  content = _csv_content(
    ["id", "name"],
    [
      {
        "id": item_id,
        "name": "Laptop",
      },
    ],
  )

  with pytest.raises(ValueError):
    import_inventory(
      authenticated_test_user,
      content,
    )


def test_import_allows_missing_optional_fields(
  test_db,
  authenticated_test_user,
):
  _grant_import_permission(
    authenticated_test_user,
  )

  content = _csv_content(
    ["name"],
    [
      {"name": "Laptop"},
    ],
  )

  result = import_inventory(
    authenticated_test_user,
    content,
  )

  item = get_item(result[0]["id"])

  assert item["name"] == "Laptop"
  assert item["location_id"] is None


def test_import_sets_location(
  test_db,
  authenticated_test_user,
):
  _grant_import_permission(
    authenticated_test_user,
  )

  from app.services.locations import create_location

  location_id = create_location(
    name="Warehouse",
  )

  content = _csv_content(
    ["name", "location"],
    [
      {
        "name": "Laptop",
        "location": "Warehouse",
      },
    ],
  )

  result = import_inventory(
    authenticated_test_user,
    content,
  )

  item = get_item(result[0]["id"])

  assert item["location_id"] == location_id


def test_import_rejects_unknown_location(
  test_db,
  authenticated_test_user,
):
  _grant_import_permission(
    authenticated_test_user,
  )

  content = _csv_content(
    ["name", "location"],
    [
      {
        "name": "Laptop",
        "location": "Does Not Exist",
      },
    ],
  )

  with pytest.raises(ValueError):
    import_inventory(
      authenticated_test_user,
      content,
    )

  assert get_items() == []


def test_import_sets_custom_field(
  test_db,
  authenticated_test_user,
):
  _grant_import_permission(
    authenticated_test_user,
  )

  field_id = create_custom_field(
    name="Purchase Price",
    field_type="decimal",
  )

  _grant_field_update_permission(
    authenticated_test_user,
    field_id,
  )

  content = _csv_content(
    ["name", "Purchase Price"],
    [
      {
        "name": "Laptop",
        "Purchase Price": "45000",
      },
    ],
  )

  result = import_inventory(
    authenticated_test_user,
    content,
  )

  item_id = result[0]["id"]

  assert (
    get_custom_field_value(
      item_id,
      field_id,
    )
    == 45000
  )


def test_import_omits_unauthorized_custom_field(
  test_db,
  authenticated_test_user,
):
  _grant_import_permission(
    authenticated_test_user,
  )

  field_id = create_custom_field(
    name="Purchase Price",
    field_type="decimal",
  )

  content = _csv_content(
    ["name", "Purchase Price"],
    [
      {
        "name": "Laptop",
        "Purchase Price": "45000",
      },
    ],
  )

  result = import_inventory(
    authenticated_test_user,
    content,
  )

  item_id = result[0]["id"]

  assert (
    get_custom_field_value(
      item_id,
      field_id,
    )
    is None
  )


def test_import_rejects_invalid_integer(
  test_db,
  authenticated_test_user,
):
  _grant_import_permission(
    authenticated_test_user,
  )

  field_id = create_custom_field(
    name="Quantity",
    field_type="integer",
  )

  _grant_field_update_permission(
    authenticated_test_user,
    field_id,
  )

  content = _csv_content(
    ["name", "Quantity"],
    [
      {
        "name": "Laptop",
        "Quantity": "not-an-integer",
      },
    ],
  )

  with pytest.raises(ValueError):
    import_inventory(
      authenticated_test_user,
      content,
    )

  assert get_items() == []


def test_import_rejects_invalid_decimal(
  test_db,
  authenticated_test_user,
):
  _grant_import_permission(
    authenticated_test_user,
  )

  field_id = create_custom_field(
    name="Purchase Price",
    field_type="decimal",
  )

  _grant_field_update_permission(
    authenticated_test_user,
    field_id,
  )

  content = _csv_content(
    ["name", "Purchase Price"],
    [
      {
        "name": "Laptop",
        "Purchase Price": "invalid",
      },
    ],
  )

  with pytest.raises(ValueError):
    import_inventory(
      authenticated_test_user,
      content,
    )

  assert get_items() == []


def test_import_rejects_invalid_boolean(
  test_db,
  authenticated_test_user,
):
  _grant_import_permission(
    authenticated_test_user,
  )

  field_id = create_custom_field(
    name="In Service",
    field_type="boolean",
  )

  _grant_field_update_permission(
    authenticated_test_user,
    field_id,
  )

  content = _csv_content(
    ["name", "In Service"],
    [
      {
        "name": "Laptop",
        "In Service": "maybe",
      },
    ],
  )

  with pytest.raises(ValueError):
    import_inventory(
      authenticated_test_user,
      content,
    )

  assert get_items() == []


def test_import_rejects_invalid_date(
  test_db,
  authenticated_test_user,
):
  _grant_import_permission(
    authenticated_test_user,
  )

  field_id = create_custom_field(
    name="Purchase Date",
    field_type="date",
  )

  _grant_field_update_permission(
    authenticated_test_user,
    field_id,
  )

  content = _csv_content(
    ["name", "Purchase Date"],
    [
      {
        "name": "Laptop",
        "Purchase Date": "not-a-date",
      },
    ],
  )

  with pytest.raises(ValueError):
    import_inventory(
      authenticated_test_user,
      content,
    )

  assert get_items() == []


def test_import_does_not_partially_create_items_on_validation_failure(
  test_db,
  authenticated_test_user,
):
  _grant_import_permission(
    authenticated_test_user,
  )

  field_id = create_custom_field(
    name="Quantity",
    field_type="integer",
  )

  _grant_field_update_permission(
    authenticated_test_user,
    field_id,
  )

  content = _csv_content(
    ["name", "Quantity"],
    [
      {
        "name": "Laptop",
        "Quantity": "10",
      },
      {
        "name": "Monitor",
        "Quantity": "invalid",
      },
    ],
  )

  with pytest.raises(ValueError):
    import_inventory(
      authenticated_test_user,
      content,
    )

  assert get_items() == []


def test_import_creates_multiple_items(
  test_db,
  authenticated_test_user,
):
  _grant_import_permission(
    authenticated_test_user,
  )

  content = _csv_content(
    ["name"],
    [
      {"name": "Laptop"},
      {"name": "Monitor"},
    ],
  )

  result = import_inventory(
    authenticated_test_user,
    content,
  )

  assert len(result) == 2
  assert {item["name"] for item in result} == {
    "Laptop",
    "Monitor",
  }


def test_import_creates_audit_log(
  test_db,
  authenticated_test_user,
):
  _grant_import_permission(
    authenticated_test_user,
  )

  content = _csv_content(
    ["name"],
    [
      {"name": "Laptop"},
    ],
  )

  result = import_inventory(
    authenticated_test_user,
    content,
  )

  item_logs = get_audit_logs(
    entity_type="inventory_item",
  )

  import_logs = get_audit_logs(
    entity_type="inventory_import",
  )

  assert len(item_logs) == 1
  assert item_logs[0]["entity_id"] == result[0]["id"]

  assert len(import_logs) == 1
  assert import_logs[0]["user_id"] == authenticated_test_user
  assert import_logs[0]["action"] == "created"


def test_import_empty_csv_is_valid(
  test_db,
  authenticated_test_user,
):
  _grant_import_permission(
    authenticated_test_user,
  )

  content = _csv_content(
    ["name"],
    [],
  )

  result = import_inventory(
    authenticated_test_user,
    content,
  )

  assert result == []
  assert get_items() == []

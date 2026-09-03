import importlib

from app.services.data.custom_fields import (
  get_custom_field,
  get_custom_fields,
)


def test_fragment_caps_per_page(
  gen_test_admin_client,
  monkeypatch,
):
  # Import the module explicitly: the "inventory" attribute on the package
  # is the Blueprint, not the module that owns the route's globals.
  inventory_routes = importlib.import_module("app.routes.inventory")

  captured = {}

  def fake_get_items_paginated(**kwargs):
    captured.update(kwargs)

    return {
      "items": [],
      "page": 1,
      "per_page": kwargs["per_page"],
      "total": 0,
      "total_pages": 1,
    }

  monkeypatch.setattr(
    inventory_routes,
    "get_items_paginated",
    fake_get_items_paginated,
  )

  response = gen_test_admin_client.get(
    "/inventory/fragment",
    query_string={
      "per_page": "100",
    },
  )

  assert response.status_code == 200
  assert captured["per_page"] == 50


def test_admin_can_create_asset(
  gen_test_admin_client,
):
  response = gen_test_admin_client.post(
    "/inventory",
    data={
      "name": "Test Asset",
    },
    headers={
      "Accept": "application/json",
    },
  )

  assert response.status_code == 200
  assert response.json["description"] is None
  assert response.json["location_id"] is None


def test_admin_cannot_create_asset_without_name(gen_test_admin_client):
  response = gen_test_admin_client.post(
    "/inventory",
    data={
      "name": "",
    },
  )

  assert response.status_code == 400
  assert response.json["error"]


def test_admin_can_create_asset_with_description(
  gen_test_admin_client,
):
  response = gen_test_admin_client.post(
    "/inventory",
    data={
      "name": "Test Asset",
      "description": "Test description",
    },
    headers={
      "Accept": "application/json",
    },
  )

  assert response.status_code == 200
  assert response.json["name"] == "Test Asset"
  assert response.json["description"] == "Test description"


def test_admin_can_view_created_asset(gen_test_admin_client):
  create_response = gen_test_admin_client.post(
    "/inventory",
    data={
      "name": "Test Asset",
    },
  )

  assert create_response.status_code == 302

  response = gen_test_admin_client.get("/inventory/fragment")

  assert response.status_code == 200
  assert b"Test Asset" in response.data


def test_admin_can_edit_asset(
  gen_test_admin_client,
  gen_test_item,
):
  item_id = gen_test_item(name="Test Asset")

  response = gen_test_admin_client.post(
    f"/inventory/{item_id}",
    data={
      "name": "Updated Asset",
    },
  )

  assert response.status_code == 302

  response = gen_test_admin_client.get(f"/inventory/{item_id}")

  assert response.status_code == 200
  assert response.json["name"] == "Updated Asset"


def test_admin_can_edit_asset_description(
  gen_test_admin_client,
  gen_test_item,
):
  item_id = gen_test_item(name="Test Asset")

  response = gen_test_admin_client.post(
    f"/inventory/{item_id}",
    data={
      "description": "Updated description",
    },
  )

  assert response.status_code == 302

  response = gen_test_admin_client.get(
    f"/inventory/{item_id}",
  )

  assert response.status_code == 200
  assert response.json["description"] == "Updated description"


def test_admin_can_clear_asset_description(
  gen_test_admin_client,
  gen_test_item,
):
  item_id = gen_test_item(name="Test Asset")

  gen_test_admin_client.post(
    f"/inventory/{item_id}",
    data={
      "description": "Test description",
    },
  )

  response = gen_test_admin_client.post(
    f"/inventory/{item_id}",
    data={
      "description": "",
    },
  )

  assert response.status_code == 302

  response = gen_test_admin_client.get(
    f"/inventory/{item_id}",
  )

  assert response.status_code == 200
  assert response.json["description"] is None


def test_admin_can_archive_asset(
  gen_test_admin_client,
  gen_test_item,
):
  item_id = gen_test_item(name="Test Asset")

  response = gen_test_admin_client.post(
    f"/inventory/{item_id}/archive",
  )

  assert response.status_code == 302

  response = gen_test_admin_client.get(f"/inventory/{item_id}")

  assert response.status_code == 404


def test_archived_asset_can_be_viewed(
  gen_test_admin_client,
  gen_test_item,
):
  item_id = gen_test_item(name="Test Asset")

  response = gen_test_admin_client.post(
    f"/inventory/{item_id}/archive",
  )

  assert response.status_code == 302

  response = gen_test_admin_client.get(
    f"/inventory/{item_id}?include_archived=true",
  )

  assert response.status_code == 200
  print(response.json)
  assert response.json["id"] == item_id
  assert response.json["archived_at"] is not None


def test_admin_can_restore_asset(
  gen_test_admin_client,
  gen_test_item,
):
  item_id = gen_test_item(name="Test Asset")

  gen_test_admin_client.post(
    f"/inventory/{item_id}/archive",
  )

  response = gen_test_admin_client.post(
    f"/inventory/{item_id}/restore",
  )

  assert response.status_code == 302

  response = gen_test_admin_client.get(
    f"/inventory/{item_id}?include_archived=true",
  )

  assert response.status_code == 200
  assert response.json["id"] == item_id
  assert response.json["archived_at"] is None


def test_admin_can_update_asset_custom_field_value(
  gen_test_admin_client,
  gen_test_item,
):
  field_response = gen_test_admin_client.post(
    "/custom-fields",
    data={
      "name": "Serial Number",
      "field_type": "text",
    },
    headers={
      "Accept": "application/json",
    },
  )

  field_name = field_response.json["name"]
  item_id = gen_test_item(name="Test Asset")

  response = gen_test_admin_client.post(
    f"/inventory/{item_id}",
    data={
      f"f_{field_name}": "SN12345",
      "name": "Test Asset",
    },
  )

  assert response.status_code == 302

  item_response = gen_test_admin_client.get(
    f"/inventory/{item_id}",
  )

  assert item_response.status_code == 200
  assert item_response.json["custom_fields"][field_name] == "SN12345"


def test_admin_cannot_update_asset_with_invalid_location(
  gen_test_admin_client,
  gen_test_item,
):
  item_id = gen_test_item()

  response = gen_test_admin_client.post(
    f"/inventory/{item_id}",
    data={
      "location_id": "999999",
    },
    headers={
      "Accept": "application/json",
    },
  )

  assert response.status_code == 400
  assert response.json["error"]


def test_admin_cannot_update_nonexistent_asset(
  gen_test_admin_client,
):
  response = gen_test_admin_client.post(
    "/inventory/does-not-exist",
    data={
      "name": "Updated Asset",
    },
    headers={
      "Accept": "application/json",
    },
  )

  assert response.status_code == 404
  assert response.json["error"]


def test_check_item(gen_test_admin_client, gen_test_item):
  item_id = gen_test_item("Laptop")

  response = gen_test_admin_client.post(
    f"/inventory/{item_id}/check",
  )

  assert response.status_code == 200
  assert response.json["id"] == item_id
  assert response.json["name"] == "Laptop"
  assert response.json["location_id"] is None


def test_check_item_not_found(gen_test_admin_client):
  response = gen_test_admin_client.post(
    "/inventory/does-not-exist/check",
  )

  assert response.status_code == 404
  assert response.json["error"]


def test_check_item_archived(gen_test_admin_client, gen_test_item):
  item_id = gen_test_item("Laptop")

  gen_test_admin_client.post(
    f"/inventory/{item_id}/archive",
  )

  response = gen_test_admin_client.post(
    f"/inventory/{item_id}/check",
  )

  assert response.status_code == 400
  assert response.json["error"]


def test_admin_can_search_inventory(
  gen_test_admin_client,
  gen_test_item,
):
  gen_test_item("Laptop")
  gen_test_item("Monitor")

  response = gen_test_admin_client.get(
    "/inventory/fragment?search=Laptop",
  )

  assert response.status_code == 200
  assert b"Laptop" in response.data
  assert b"Monitor" not in response.data


def test_admin_can_filter_inventory_by_location(
  gen_test_admin_client,
  gen_test_item,
):
  storage_response = gen_test_admin_client.post(
    "/locations",
    data={"name": "Storage"},
    headers={"Accept": "application/json"},
  )
  storage_id = storage_response.json["id"]

  gen_test_item(
    "Laptop",
    location_id=storage_id,
  )
  gen_test_item("Monitor")

  response = gen_test_admin_client.get(
    f"/inventory/fragment?location_id={storage_id}",
  )

  assert response.status_code == 200
  assert b"Laptop" in response.data
  assert b"Monitor" not in response.data


def test_admin_can_sort_inventory(
  gen_test_admin_client,
  gen_test_item,
):
  gen_test_item("Monitor")
  gen_test_item("Laptop")
  gen_test_item("Keyboard")

  response = gen_test_admin_client.get(
    "/inventory/fragment?sort_by=name&sort_order=desc",
  )

  assert response.status_code == 200
  data_str = response.data.decode("utf-8")
  monitor_index = data_str.index("Monitor")
  laptop_index = data_str.index("Laptop")
  keyboard_index = data_str.index("Keyboard")
  assert monitor_index < laptop_index < keyboard_index


def test_admin_cannot_use_invalid_sort_order(
  gen_test_admin_client,
):
  response = gen_test_admin_client.get(
    "/inventory/fragment?sort_order=invalid",
  )

  assert response.status_code == 400
  assert response.json["error"]


def test_inventory_page_filters_by_location(
  gen_test_admin_client,
  gen_test_location,
  gen_test_item,
):
  location_id = gen_test_location(name="Storage")

  gen_test_item(name="Stored item", location_id=location_id)
  gen_test_item(name="Other item")

  response = gen_test_admin_client.get(f"/inventory/fragment?location_id={location_id}")

  assert response.status_code == 200
  assert b"Stored item" in response.data
  assert b"Other item" not in response.data


def test_inventory_page_sorts_items(
  gen_test_admin_client,
  gen_test_item,
):
  gen_test_item(name="Zebra")
  gen_test_item(name="Apple")

  response = gen_test_admin_client.get(
    "/inventory/fragment?sort_by=name&sort_order=desc"
  )

  assert response.status_code == 200

  apple_position = response.data.index(b"Apple")
  zebra_position = response.data.index(b"Zebra")

  assert apple_position > zebra_position


def _create_field(
  client,
  name,
  field_type,
  required=False,
  enum_values=None,
):
  data = {
    "name": name,
    "field_type": field_type,
  }

  if required:
    data["required"] = "true"

  if enum_values:
    data["enum_values"] = ",".join(enum_values)

  client.post("/custom-fields", data=data)

  fields = get_custom_fields()

  field = next(field for field in fields if field["name"] == name)

  if required:
    client.post(
      f"/custom-fields/{field['id']}",
      data={
        "required": "true",
      },
    )

    field = get_custom_field(field["id"])

  return field


def test_admin_can_create_asset_with_custom_field_values(
  gen_test_admin_client,
):
  _create_field(gen_test_admin_client, "Serial Number", "text")
  _create_field(gen_test_admin_client, "Quantity", "integer")

  response = gen_test_admin_client.post(
    "/inventory",
    data={
      "name": "Test Asset",
      "f_Serial Number": "SN-001",
      "f_Quantity": "5",
    },
    headers={
      "Accept": "application/json",
    },
  )

  assert response.status_code == 200

  item_id = response.json["id"]

  response = gen_test_admin_client.get(f"/inventory/{item_id}")

  assert response.json["custom_fields"] == {
    "Serial Number": "SN-001",
    "Quantity": 5,
  }


def test_admin_creating_asset_with_empty_optional_value_stores_no_row(
  gen_test_admin_client,
):
  _create_field(gen_test_admin_client, "Serial Number", "text")

  response = gen_test_admin_client.post(
    "/inventory",
    data={
      "name": "Test Asset",
      "f_Serial Number": "",
    },
    headers={
      "Accept": "application/json",
    },
  )

  assert response.status_code == 200

  item_id = response.json["id"]

  response = gen_test_admin_client.get(f"/inventory/{item_id}")

  assert response.json["custom_fields"] == {}


def test_admin_cannot_create_asset_missing_required_custom_field(
  gen_test_admin_client,
):
  _create_field(gen_test_admin_client, "Serial Number", "text", required=True)

  response = gen_test_admin_client.post(
    "/inventory",
    data={
      "name": "Test Asset",
    },
  )

  assert response.status_code == 400
  assert response.json["error"]


def test_admin_cannot_create_asset_with_empty_required_custom_field(
  gen_test_admin_client,
):
  _create_field(gen_test_admin_client, "Serial Number", "text", required=True)

  response = gen_test_admin_client.post(
    "/inventory",
    data={
      "name": "Test Asset",
      "f_Serial Number": "",
    },
  )

  assert response.status_code == 400
  assert response.json["error"]


def test_admin_can_edit_asset_custom_field_values(
  gen_test_admin_client,
  gen_test_item,
):
  _create_field(gen_test_admin_client, "Serial Number", "text")
  _create_field(gen_test_admin_client, "Quantity", "integer")

  item_id = gen_test_item(name="Test Asset")

  response = gen_test_admin_client.post(
    f"/inventory/{item_id}",
    data={
      "f_Serial Number": "SN-002",
      "f_Quantity": "7",
    },
  )

  assert response.status_code == 302

  response = gen_test_admin_client.get(f"/inventory/{item_id}")

  assert response.json["custom_fields"] == {
    "Serial Number": "SN-002",
    "Quantity": 7,
  }


def test_admin_editing_asset_with_empty_optional_value_clears_it(
  gen_test_admin_client,
  gen_test_item,
):
  _create_field(gen_test_admin_client, "Serial Number", "text")

  item_id = gen_test_item(name="Test Asset")

  gen_test_admin_client.post(
    f"/inventory/{item_id}",
    data={
      "f_Serial Number": "SN-001",
    },
  )

  response = gen_test_admin_client.post(
    f"/inventory/{item_id}",
    data={
      "f_Serial Number": "",
    },
  )

  assert response.status_code == 302

  response = gen_test_admin_client.get(f"/inventory/{item_id}")

  assert response.json["custom_fields"] == {}


def test_admin_can_edit_asset_boolean_custom_field_false(
  gen_test_admin_client,
  gen_test_item,
):
  _create_field(gen_test_admin_client, "Active", "boolean")

  item_id = gen_test_item(name="Test Asset")

  gen_test_admin_client.post(
    f"/inventory/{item_id}",
    data={
      "f_Active": "true",
    },
  )

  response = gen_test_admin_client.post(
    f"/inventory/{item_id}",
    data={
      "f_Active": "false",
    },
  )

  assert response.status_code == 302

  response = gen_test_admin_client.get(f"/inventory/{item_id}")

  assert response.json["custom_fields"] == {"Active": False}


def test_admin_cannot_create_asset_with_invalid_decimal_custom_field(
  gen_test_admin_client,
):
  field = _create_field(gen_test_admin_client, "Price", "decimal")

  response = gen_test_admin_client.post(
    "/inventory",
    data={
      "name": "Test Asset",
      f"f_{field['name']}": "11ddddawd",
    },
    headers={
      "Accept": "application/json",
    },
  )

  assert response.status_code == 400
  assert response.json["error"]


def test_admin_cannot_edit_asset_with_invalid_decimal_custom_field(
  gen_test_admin_client,
  gen_test_item,
):
  field = _create_field(gen_test_admin_client, "Price", "decimal")

  item_id = gen_test_item(name="Test Asset")

  response = gen_test_admin_client.post(
    f"/inventory/{item_id}",
    data={
      f"f_{field['name']}": "11ddddawd",
    },
    headers={
      "Accept": "application/json",
    },
  )

  assert response.status_code == 400
  assert response.json["error"]


def test_admin_cannot_edit_asset_missing_required_custom_field(
  gen_test_admin_client,
  gen_test_item,
):
  _create_field(gen_test_admin_client, "Serial Number", "text", required=True)

  item_id = gen_test_item(name="Test Asset")

  response = gen_test_admin_client.post(
    f"/inventory/{item_id}",
    data={},
  )

  assert response.status_code == 400
  assert response.json["error"]


def test_fragment_filters_by_custom_field(
  gen_test_admin_client,
  gen_test_item,
):
  field = _create_field(gen_test_admin_client, "Serial Number", "text")

  match_id = gen_test_item(name="Match")
  gen_test_item(name="Other")

  gen_test_admin_client.post(
    f"/inventory/{match_id}",
    data={
      f"f_{field['name']}": "contains NEEDLE here",
    },
  )

  response = gen_test_admin_client.get(
    f"/inventory/fragment?f_field={field['id']}&f_op=contains&f_value=NEEDLE"
  )

  assert response.status_code == 200
  assert b"Match" in response.data
  assert b"Other" not in response.data


def test_fragment_ignores_empty_filter_values(
  gen_test_admin_client,
  gen_test_item,
):
  field = _create_field(gen_test_admin_client, "Serial Number", "text")

  gen_test_item(name="Match")
  gen_test_item(name="Other")

  response = gen_test_admin_client.get(
    f"/inventory/fragment?f_field={field['id']}&f_op=contains&f_value="
  )

  assert response.status_code == 200
  assert b"Match" in response.data
  assert b"Other" in response.data


def test_fragment_rejects_invalid_filter_operator(
  gen_test_admin_client,
  gen_test_item,
):
  field = _create_field(gen_test_admin_client, "Serial Number", "text")

  gen_test_item(name="Match")

  response = gen_test_admin_client.get(
    f"/inventory/fragment?f_field={field['id']}&f_op=gte&f_value=5"
  )

  assert response.status_code == 400
  assert response.json["error"]


def test_export_applies_custom_field_filters(
  gen_test_admin_client,
  gen_test_item,
):
  field = _create_field(gen_test_admin_client, "Serial Number", "text")

  match_id = gen_test_item(name="Match")
  gen_test_item(name="Other")

  gen_test_admin_client.post(
    f"/inventory/{match_id}",
    data={
      f"f_{field['name']}": "contains NEEDLE here",
    },
  )

  response = gen_test_admin_client.get(
    f"/inventory/export?f_field={field['id']}&f_op=contains&f_value=NEEDLE"
  )

  assert response.status_code == 200
  assert b"Match" in response.data
  assert b"Other" not in response.data

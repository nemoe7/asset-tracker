from app.services.data.custom_fields import (
  get_custom_field,
  get_custom_fields,
)
from app.services.data.locations import get_location

# ==================== Admin Page ====================


def test_admin_can_view_admin_page(
  gen_test_admin_client,
):
  response = gen_test_admin_client.get(
    "/admin",
  )

  assert response.status_code == 200


def test_admin_page_renders_all_tabs(
  gen_test_admin_client,
):
  response = gen_test_admin_client.get(
    "/admin",
  )

  html = response.data.decode()

  assert "Locations" in html
  assert "Custom fields" in html


def test_admin_page_requires_login(
  gen_test_client,
):
  response = gen_test_client.get(
    "/admin",
  )

  assert response.status_code == 302


# ==================== User Management (not implemented) ====================


def test_admin_user_routes_redirect_to_index_without_side_effects(
  gen_test_admin_client,
):
  response = gen_test_admin_client.post(
    "/admin/users",
    data={
      "username": "new_user",
      "display_name": "New User",
      "password": "password123",
    },
  )

  assert response.status_code == 302
  assert response.location.endswith("/")

  response = gen_test_admin_client.post(
    "/admin/users/1",
    data={
      "username": "renamed_user",
    },
  )

  assert response.status_code == 302
  assert response.location.endswith("/")

  response = gen_test_admin_client.post(
    "/admin/users/1/archive",
  )

  assert response.status_code == 302
  assert response.location.endswith("/")

  response = gen_test_admin_client.post(
    "/admin/users/1/restore",
  )

  assert response.status_code == 302
  assert response.location.endswith("/")


# ==================== Locations Tab ====================


def test_admin_can_create_location_from_admin_page(
  gen_test_admin_client,
):
  response = gen_test_admin_client.post(
    "/admin/locations",
    data={
      "name": "Warehouse",
      "description": "Main storage area",
    },
  )

  assert response.status_code == 302
  assert get_location(1)["name"] == "Warehouse"


def test_admin_cannot_create_location_with_empty_name(
  gen_test_admin_client,
):
  response = gen_test_admin_client.post(
    "/admin/locations",
    data={
      "name": "   ",
    },
  )

  assert response.status_code == 200
  assert "Location name cannot be empty" in response.data.decode()


def test_admin_cannot_create_duplicate_location(
  gen_test_admin_client,
):
  gen_test_admin_client.post(
    "/admin/locations",
    data={
      "name": "Warehouse",
    },
  )

  response = gen_test_admin_client.post(
    "/admin/locations",
    data={
      "name": "Warehouse",
    },
  )

  assert response.status_code == 200
  assert "Location already exists" in response.data.decode()


def test_admin_can_delete_location_from_admin_page(
  gen_test_admin_client,
  gen_test_location,
):
  location_id = gen_test_location()

  response = gen_test_admin_client.post(
    f"/admin/locations/{location_id}/delete",
    data={
      "confirm": "true",
    },
  )

  assert response.status_code == 302
  assert get_location(location_id) is None


def test_admin_can_update_location_from_admin_page(
  gen_test_admin_client,
  gen_test_location,
):
  location_id = gen_test_location()

  response = gen_test_admin_client.post(
    f"/admin/locations/{location_id}",
    data={
      "name": "Main Warehouse",
      "description": "Updated description",
    },
  )

  assert response.status_code == 302

  location = get_location(location_id)

  assert location["name"] == "Main Warehouse"
  assert location["description"] == "Updated description"


def test_admin_cannot_update_location_to_duplicate_name(
  gen_test_admin_client,
  gen_test_location,
):
  gen_test_location("Warehouse")
  location_id = gen_test_location("Office")

  response = gen_test_admin_client.post(
    f"/admin/locations/{location_id}",
    data={
      "name": "Warehouse",
    },
  )

  assert response.status_code == 200
  assert "Location already exists" in response.data.decode()


def test_admin_cannot_update_location_with_empty_name(
  gen_test_admin_client,
  gen_test_location,
):
  location_id = gen_test_location()

  response = gen_test_admin_client.post(
    f"/admin/locations/{location_id}",
    data={
      "name": "   ",
    },
  )

  assert response.status_code == 200
  assert "Location name cannot be empty" in response.data.decode()


def test_admin_cannot_update_nonexistent_location(
  gen_test_admin_client,
):
  response = gen_test_admin_client.post(
    "/admin/locations/999",
    data={
      "name": "Warehouse",
    },
  )

  assert response.status_code == 404


# ==================== Custom Fields Tab ====================


def test_admin_can_create_custom_field_from_admin_page(
  gen_test_admin_client,
):
  response = gen_test_admin_client.post(
    "/admin/custom-fields",
    data={
      "name": "Serial Number",
      "field_type": "text",
    },
  )

  assert response.status_code == 302

  fields = [field for field in get_custom_fields() if field["name"] == "Serial Number"]

  assert len(fields) == 1
  assert fields[0]["field_type"] == "text"


def test_admin_cannot_create_custom_field_with_empty_name(
  gen_test_admin_client,
):
  response = gen_test_admin_client.post(
    "/admin/custom-fields",
    data={
      "name": "",
      "field_type": "text",
    },
  )

  assert response.status_code == 200
  assert "Custom field name cannot be empty" in response.data.decode()


def test_admin_cannot_create_duplicate_custom_field(
  gen_test_admin_client,
):
  gen_test_admin_client.post(
    "/admin/custom-fields",
    data={
      "name": "Serial Number",
      "field_type": "text",
    },
  )

  response = gen_test_admin_client.post(
    "/admin/custom-fields",
    data={
      "name": "Serial Number",
      "field_type": "text",
    },
  )

  assert response.status_code == 200
  assert "Custom field already exists" in response.data.decode()


def test_admin_cannot_create_custom_field_with_invalid_type(
  gen_test_admin_client,
):
  response = gen_test_admin_client.post(
    "/admin/custom-fields",
    data={
      "name": "Serial Number",
      "field_type": "invalid",
    },
  )

  assert response.status_code == 200
  assert "Invalid custom field type" in response.data.decode()


def test_admin_can_rename_custom_field_from_admin_page(
  gen_test_admin_client,
):
  gen_test_admin_client.post(
    "/admin/custom-fields",
    data={
      "name": "Serial Number",
      "field_type": "text",
    },
  )

  field = next(
    field for field in get_custom_fields() if field["name"] == "Serial Number"
  )

  response = gen_test_admin_client.post(
    f"/admin/custom-fields/{field['id']}",
    data={
      "name": "Asset Serial Number",
    },
  )

  assert response.status_code == 302
  assert get_custom_field(field["id"])["name"] == "Asset Serial Number"


def test_admin_cannot_rename_custom_field_to_empty_name(
  gen_test_admin_client,
):
  gen_test_admin_client.post(
    "/admin/custom-fields",
    data={
      "name": "Serial Number",
      "field_type": "text",
    },
  )

  field = next(
    field for field in get_custom_fields() if field["name"] == "Serial Number"
  )

  response = gen_test_admin_client.post(
    f"/admin/custom-fields/{field['id']}",
    data={
      "name": "",
    },
  )

  assert response.status_code == 200
  assert "Custom field name cannot be empty" in response.data.decode()


def test_admin_cannot_rename_custom_field_to_duplicate_name(
  gen_test_admin_client,
):
  gen_test_admin_client.post(
    "/admin/custom-fields",
    data={
      "name": "Serial Number",
      "field_type": "text",
    },
  )

  gen_test_admin_client.post(
    "/admin/custom-fields",
    data={
      "name": "Asset Tag",
      "field_type": "text",
    },
  )

  field = next(field for field in get_custom_fields() if field["name"] == "Asset Tag")

  response = gen_test_admin_client.post(
    f"/admin/custom-fields/{field['id']}",
    data={
      "name": "Serial Number",
    },
  )

  assert response.status_code == 200
  assert "Custom field already exists" in response.data.decode()


def test_admin_can_create_enum_custom_field_from_admin_page(
  gen_test_admin_client,
):
  response = gen_test_admin_client.post(
    "/admin/custom-fields",
    data={
      "name": "Category",
      "field_type": "enum",
      "enum_values": "IT\nHR\nFinance",
    },
  )

  assert response.status_code == 302

  field = next(field for field in get_custom_fields() if field["name"] == "Category")

  assert field["field_type"] == "enum"
  assert field["enum_values"] == ["IT", "HR", "Finance"]


def test_admin_cannot_create_enum_custom_field_without_values(
  gen_test_admin_client,
):
  response = gen_test_admin_client.post(
    "/admin/custom-fields",
    data={
      "name": "Category",
      "field_type": "enum",
    },
  )

  assert response.status_code == 200
  assert "Enum values must be a non-empty list" in response.data.decode()


def test_admin_can_create_custom_field_with_description_and_required(
  gen_test_admin_client,
):
  response = gen_test_admin_client.post(
    "/admin/custom-fields",
    data={
      "name": "Serial Number",
      "field_type": "text",
      "description": "Manufacturer serial number",
      "required": "true",
    },
  )

  assert response.status_code == 302

  field = next(
    field for field in get_custom_fields() if field["name"] == "Serial Number"
  )

  assert field["description"] == "Manufacturer serial number"
  assert field["required"] == 1


def test_admin_can_update_enum_custom_field_values(
  gen_test_admin_client,
):
  gen_test_admin_client.post(
    "/admin/custom-fields",
    data={
      "name": "Category",
      "field_type": "enum",
      "enum_values": "IT\nHR",
    },
  )

  field = next(field for field in get_custom_fields() if field["name"] == "Category")

  response = gen_test_admin_client.post(
    f"/admin/custom-fields/{field['id']}",
    data={
      "name": "Category",
      "field_type": "enum",
      "enum_values": "IT\nHR\nFinance",
    },
  )

  assert response.status_code == 302
  assert get_custom_field(field["id"])["enum_values"] == ["IT", "HR", "Finance"]


def test_admin_can_update_custom_field_description_and_required(
  gen_test_admin_client,
):
  gen_test_admin_client.post(
    "/admin/custom-fields",
    data={
      "name": "Serial Number",
      "field_type": "text",
    },
  )

  field = next(
    field for field in get_custom_fields() if field["name"] == "Serial Number"
  )

  response = gen_test_admin_client.post(
    f"/admin/custom-fields/{field['id']}",
    data={
      "name": "Serial Number",
      "field_type": "text",
      "description": "Manufacturer serial number",
      "required": "true",
    },
  )

  assert response.status_code == 302

  updated = get_custom_field(field["id"])

  assert updated["description"] == "Manufacturer serial number"
  assert updated["required"] == 1

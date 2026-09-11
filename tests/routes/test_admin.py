from app.services.data.custom_fields import (
  get_custom_field,
  get_custom_fields,
)
from app.services.data.db import db_transaction
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


# ==================== Data Tab ====================


def test_reset_database_requires_login(
  gen_test_client,
):
  response = gen_test_client.post(
    "/admin/data/reset",
    data={
      "password": "test_admin",
      "confirm_password": "test_admin",
    },
  )

  assert response.status_code == 302


def test_reset_database_returns_404_when_debug_is_off(
  gen_test_admin_client,
  monkeypatch,
):
  import config

  monkeypatch.setattr(config, "DEBUG", False)

  response = gen_test_admin_client.post(
    "/admin/data/reset",
    data={
      "password": "test_admin",
      "confirm_password": "test_admin",
    },
  )

  assert response.status_code == 404


def test_reset_database_rejects_wrong_password(
  gen_test_admin_client,
  monkeypatch,
):
  import config

  monkeypatch.setattr(config, "DEBUG", True)

  response = gen_test_admin_client.post(
    "/admin/data/reset",
    data={
      "password": "wrong_password",
      "confirm_password": "wrong_password",
    },
  )

  assert response.status_code == 200
  assert "Incorrect password" in response.data.decode()


def test_reset_database_rejects_mismatched_passwords(
  gen_test_admin_client,
  monkeypatch,
):
  import config

  monkeypatch.setattr(config, "DEBUG", True)

  response = gen_test_admin_client.post(
    "/admin/data/reset",
    data={
      "password": "test_admin",
      "confirm_password": "different",
    },
  )

  assert response.status_code == 200
  assert "Passwords do not match" in response.data.decode()


def test_reset_database_clears_data(
  gen_test_admin_client,
  gen_test_location,
  monkeypatch,
):
  import config

  monkeypatch.setattr(config, "DEBUG", True)

  location_id = gen_test_location()

  response = gen_test_admin_client.post(
    "/admin/data/reset",
    data={
      "password": "test_admin",
      "confirm_password": "test_admin",
    },
  )

  assert response.status_code == 302
  assert response.location.endswith("/auth/login")
  assert get_location(location_id) is None


# ==================== Audit Log ====================


def _login_restricted_user(gen_test_client):
  from werkzeug.security import generate_password_hash

  import sqlite3

  import config

  connection = sqlite3.connect(config.DB_PATH)

  connection.execute(
    """
    INSERT INTO users (
      username,
      name,
      password_hash,
      created_at,
      updated_at
    )
    VALUES (?, ?, ?, datetime('now'), datetime('now'))
    """,
    ("restricted_user", "Restricted", generate_password_hash("restricted1")),
  )

  connection.commit()
  connection.close()

  gen_test_client.post(
    "/auth/login",
    data={
      "username": "restricted_user",
      "password": "restricted1",
    },
  )


def test_audit_page_requires_login(
  gen_test_client,
):
  response = gen_test_client.get(
    "/admin/audit",
  )

  assert response.status_code == 302


def test_audit_fragment_requires_login(
  gen_test_client,
):
  response = gen_test_client.get(
    "/admin/audit/fragment",
  )

  assert response.status_code == 302


def test_audit_page_requires_audit_read_permission(
  gen_test_client,
  gen_test_admin,
):
  _login_restricted_user(gen_test_client)

  response = gen_test_client.get("/admin/audit")

  assert response.status_code == 403


def test_audit_fragment_requires_audit_read_permission(
  gen_test_client,
  gen_test_admin,
):
  _login_restricted_user(gen_test_client)

  response = gen_test_client.get("/admin/audit/fragment")

  assert response.status_code == 403


def test_admin_can_view_audit_page(
  gen_test_admin_client,
  gen_test_item,
):
  gen_test_item()

  response = gen_test_admin_client.get("/admin/audit")

  assert response.status_code == 200

  html = response.data.decode()

  assert 'data-audit-row=' in html
  assert "inventory_item" in html


def test_audit_page_applies_entity_type_filter(
  gen_test_admin_client,
  gen_test_item,
  gen_test_location,
):
  gen_test_item()
  gen_test_location()

  unfiltered = gen_test_admin_client.get("/admin/audit")

  assert unfiltered.data.decode().count('data-audit-row=') == 2

  filtered = gen_test_admin_client.get(
    "/admin/audit?entity_type=location",
  )

  assert filtered.status_code == 200
  assert filtered.data.decode().count('data-audit-row=') == 1


def test_audit_page_rejects_invalid_page(
  gen_test_admin_client,
):
  response = gen_test_admin_client.get("/admin/audit?page=abc")

  assert response.status_code == 400


def test_audit_page_rejects_zero_page(
  gen_test_admin_client,
):
  response = gen_test_admin_client.get("/admin/audit?page=0")

  assert response.status_code == 400


def test_audit_page_rejects_invalid_from_date(
  gen_test_admin_client,
):
  response = gen_test_admin_client.get("/admin/audit?from=not-a-date")

  assert response.status_code == 400


def test_audit_page_rejects_from_after_to(
  gen_test_admin_client,
):
  response = gen_test_admin_client.get(
    "/admin/audit?from=2026-01-02&to=2026-01-01",
  )

  assert response.status_code == 400


def test_audit_page_escapes_reflected_entity_id(
  gen_test_admin_client,
):
  response = gen_test_admin_client.get(
    "/admin/audit",
    query_string={"entity_id": '" onmouseover="alert(1)'},
  )

  assert response.status_code == 200
  assert '" onmouseover="' not in response.data.decode()


def test_audit_page_escapes_details_values(
  gen_test_admin_client,
  gen_test_admin,
):
  with db_transaction() as connection:
    connection.execute(
      """
      INSERT INTO audit_log (
        user_id,
        action,
        entity_type,
        entity_id,
        details,
        timestamp
      )
      VALUES (?, 'updated', 'test', '1', '<script>alert(1)</script>', datetime('now'))
      """,
      (gen_test_admin,),
    )

  response = gen_test_admin_client.get("/admin/audit")

  html = response.data.decode()

  assert '<script>alert(1)</script>' not in html
  assert '&lt;script&gt;alert(1)&lt;/script&gt;' in html


def test_audit_fragment_renders_rows_for_admin(
  gen_test_admin_client,
  gen_test_item,
):
  gen_test_item()

  response = gen_test_admin_client.get("/admin/audit/fragment?page=1")

  assert response.status_code == 200

  html = response.data.decode()

  assert 'data-audit-row=' in html
  assert 'data-has-more="false"' in html


def test_audit_fragment_reports_more_pages(
  gen_test_admin_client,
  gen_test_admin,
):
  with db_transaction() as connection:
    for index in range(51):
      connection.execute(
        """
        INSERT INTO audit_log (
          user_id,
          action,
          entity_type,
          entity_id,
          timestamp
        )
        VALUES (?, 'created', 'test', ?, datetime('now'))
        """,
        (gen_test_admin, str(index)),
      )

  response = gen_test_admin_client.get("/admin/audit/fragment?page=1")

  assert response.status_code == 200
  assert 'data-has-more="true"' in response.data.decode()

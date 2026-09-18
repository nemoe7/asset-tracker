import csv
import io

from app.services.export import _csv_safe


def test_csv_safe_passes_through_plain_negative_number():
  assert _csv_safe("-5") == "-5"
  assert _csv_safe("-12.75") == "-12.75"


def test_csv_safe_still_prefixes_formula_characters():
  assert _csv_safe("=cmd()") == "'=cmd()"
  assert _csv_safe("+1") == "'+1"
  assert _csv_safe("@x") == "'@x"
  assert _csv_safe("-1;drop") == "'-1;drop"


def test_export_returns_csv_with_built_in_fields(
  gen_test_admin_client,
  gen_test_item,
):
  item_id = gen_test_item(name="Alpha Asset")

  response = gen_test_admin_client.get("/inventory/export")

  assert response.status_code == 200
  assert response.mimetype == "text/csv"
  assert "attachment" in response.headers["Content-Disposition"]

  rows = list(
    csv.reader(
      io.StringIO(response.get_data(as_text=True)),
    )
  )

  assert rows[0] == [
    "id",
    "name",
    "description",
    "location",
    "created_at",
    "updated_at",
    "archival_reason",
    "archival_notes",
  ]
  assert len(rows) == 2
  assert rows[1][0] == item_id
  assert rows[1][1] == "Alpha Asset"


def test_export_search_filter_matches_name(
  gen_test_admin_client,
  gen_test_item,
):
  gen_test_item(name="Alpha Asset")
  gen_test_item(name="Beta Asset")

  response = gen_test_admin_client.get(
    "/inventory/export",
    query_string={"search": "Alpha"},
  )

  rows = list(
    csv.reader(
      io.StringIO(response.get_data(as_text=True)),
    )
  )

  assert [row[1] for row in rows[1:]] == ["Alpha Asset"]


def test_export_location_filter(
  gen_test_admin_client,
  gen_test_item,
  gen_test_location,
):
  location_id = gen_test_location(name="Office")
  gen_test_item(name="Alpha Asset")
  gen_test_item(name="Beta Asset", location_id=location_id)

  response = gen_test_admin_client.get(
    "/inventory/export",
    query_string={"location_id": location_id},
  )

  rows = list(
    csv.reader(
      io.StringIO(response.get_data(as_text=True)),
    )
  )

  assert [row[1] for row in rows[1:]] == ["Beta Asset"]
  assert rows[1][3] == "Office"


def test_export_filters_exclude_archived_items(
  gen_test_admin_client,
  gen_test_item,
):
  gen_test_item(name="Alpha Asset")
  archived_id = gen_test_item(name="Archived Asset")
  gen_test_admin_client.post(
    f"/inventory/{archived_id}/archive",
    data={"archival_reason": "Damaged"},
  )

  response = gen_test_admin_client.get("/inventory/export")

  rows = list(
    csv.reader(
      io.StringIO(response.get_data(as_text=True)),
    )
  )

  assert [row[1] for row in rows[1:]] == ["Alpha Asset"]

  response = gen_test_admin_client.get(
    "/inventory/export",
    query_string={"include_archived": "true"},
  )

  rows = list(
    csv.reader(
      io.StringIO(response.get_data(as_text=True)),
    )
  )

  assert sorted(row[1] for row in rows[1:]) == [
    "Alpha Asset",
    "Archived Asset",
  ]


def test_export_selected_fields(
  gen_test_admin_client,
  gen_test_item,
  gen_test_location,
):
  location_id = gen_test_location(name="Office")
  gen_test_item(name="Alpha Asset", location_id=location_id)

  response = gen_test_admin_client.get(
    "/inventory/export",
    query_string={"fields": ["name", "location"]},
  )

  rows = list(
    csv.reader(
      io.StringIO(response.get_data(as_text=True)),
    )
  )

  assert rows[0] == ["name", "location"]
  assert rows[1] == ["Alpha Asset", "Office"]


def test_export_archival_reason_and_notes(
  gen_test_admin_client,
  gen_test_item,
):
  item_id = gen_test_item(name="Archived Asset")

  gen_test_admin_client.post(
    f"/inventory/{item_id}/archive",
    data={
      "archival_reason": "Disposed",
      "archival_notes": "End of life",
    },
  )

  response = gen_test_admin_client.get(
    "/inventory/export",
    query_string={
      "fields": ["name", "archival_reason", "archival_notes"],
      "include_archived": "true",
    },
  )

  assert response.status_code == 200

  rows = list(
    csv.reader(
      io.StringIO(response.get_data(as_text=True)),
    )
  )

  assert rows[0] == ["name", "archival_reason", "archival_notes"]
  assert rows[1] == ["Archived Asset", "Disposed", "End of life"]


def test_export_active_items_have_empty_archival_fields(
  gen_test_admin_client,
  gen_test_item,
):
  gen_test_item(name="Alpha Asset")

  response = gen_test_admin_client.get(
    "/inventory/export",
    query_string={"fields": ["name", "archival_reason", "archival_notes"]},
  )

  rows = list(
    csv.reader(
      io.StringIO(response.get_data(as_text=True)),
    )
  )

  assert rows[1] == ["Alpha Asset", "", ""]


def test_export_empty_field_selection_is_rejected(gen_test_admin_client):
  response = gen_test_admin_client.get(
    "/inventory/export",
    query_string={"fields": ""},
  )

  assert response.status_code == 400
  assert response.json["error"]


def test_export_duplicate_fields_are_rejected(gen_test_admin_client):
  response = gen_test_admin_client.get(
    "/inventory/export",
    query_string={"fields": ["name", "name"]},
  )

  assert response.status_code == 400
  assert response.json["error"]


def test_export_unknown_field_is_rejected(gen_test_admin_client):
  response = gen_test_admin_client.get(
    "/inventory/export",
    query_string={"fields": "not_a_field"},
  )

  assert response.status_code == 400
  assert response.json["error"]


def test_export_field_keys_resolve_case_insensitively(
  gen_test_admin_client,
  gen_test_item,
):
  gen_test_item(name="Alpha Asset")

  response = gen_test_admin_client.get(
    "/inventory/export",
    query_string={"fields": ["Name", "LOCATION"]},
  )

  assert response.status_code == 200
  rows = list(
    csv.reader(
      io.StringIO(response.get_data(as_text=True)),
    )
  )
  # Resolved to canonical builtin keys in the CSV header.
  assert rows[0] == ["name", "location"]
  assert rows[1][0] == "Alpha Asset"


def test_export_case_duplicate_fields_are_rejected(gen_test_admin_client):
  response = gen_test_admin_client.get(
    "/inventory/export",
    query_string={"fields": ["name", "Name"]},
  )

  assert response.status_code == 400
  assert response.json["error"]


def test_export_custom_field_keys_resolve_case_insensitively(
  gen_test_admin_client,
  gen_test_item,
  gen_test_admin,
):
  from app.services.auth.context import reset_current_user, set_current_user
  from app.services.data.custom_field_values import set_custom_field_value
  from app.services.data.custom_fields import create_custom_field

  token = set_current_user(gen_test_admin)

  try:
    serial_id = create_custom_field("Serial Number", "text")
    item_id = gen_test_item(name="Alpha Asset")
    set_custom_field_value(item_id, serial_id, "SN-001")
  finally:
    reset_current_user(token)

  response = gen_test_admin_client.get(
    "/inventory/export",
    query_string={"fields": "serial number"},
  )

  assert response.status_code == 200
  rows = list(
    csv.reader(
      io.StringIO(response.get_data(as_text=True)),
    )
  )
  assert rows[0] == ["Serial Number"]
  assert rows[1] == ["SN-001"]


def test_export_includes_custom_fields(
  gen_test_admin_client,
  gen_test_item,
  gen_test_admin,
):
  from app.services.auth.context import reset_current_user, set_current_user
  from app.services.data.custom_field_values import set_custom_field_value
  from app.services.data.custom_fields import create_custom_field

  token = set_current_user(gen_test_admin)

  try:
    serial_id = create_custom_field("Serial Number", "text")
    create_custom_field("Quantity", "integer")

    item_id = gen_test_item(name="Alpha Asset")
    set_custom_field_value(item_id, serial_id, "SN-001")
  finally:
    reset_current_user(token)

  response = gen_test_admin_client.get("/inventory/export")

  rows = list(
    csv.reader(
      io.StringIO(response.get_data(as_text=True)),
    )
  )

  assert rows[0] == [
    "id",
    "name",
    "description",
    "location",
    "created_at",
    "updated_at",
    "archival_reason",
    "archival_notes",
    "Quantity",
    "Serial Number",
  ]
  assert rows[1][6] == ""
  assert rows[1][7] == ""
  assert rows[1][8] == ""
  assert rows[1][9] == "SN-001"


def test_export_selected_custom_fields(
  gen_test_admin_client,
  gen_test_item,
  gen_test_admin,
):
  from app.services.auth.context import reset_current_user, set_current_user
  from app.services.data.custom_field_values import set_custom_field_value
  from app.services.data.custom_fields import create_custom_field

  token = set_current_user(gen_test_admin)

  try:
    serial_id = create_custom_field("Serial Number", "text")

    item_id = gen_test_item(name="Alpha Asset")
    set_custom_field_value(item_id, serial_id, "SN-001")
  finally:
    reset_current_user(token)

  response = gen_test_admin_client.get(
    "/inventory/export",
    query_string={"fields": ["name", "Serial Number"]},
  )

  rows = list(
    csv.reader(
      io.StringIO(response.get_data(as_text=True)),
    )
  )

  assert rows[0] == ["name", "Serial Number"]
  assert rows[1] == ["Alpha Asset", "SN-001"]


def test_export_excludes_non_readable_custom_fields(
  gen_test_admin,
  gen_test_client,
  gen_test_item,
):
  from app.services.auth.context import reset_current_user, set_current_user
  from app.services.data.custom_field_values import set_custom_field_value
  from app.services.data.custom_fields import create_custom_field
  from app.services.data.permissions import (
    create_permission,
    get_permission_by_name,
  )
  from app.services.data.role_permissions import set_role_permission
  from app.services.data.roles import create_role
  from app.services.data.user_roles import set_user_role
  from app.services.data.users import create_user

  token = set_current_user(gen_test_admin)

  try:
    serial_id = create_custom_field("Serial Number", "text")
    create_custom_field("Secret", "text")

    item_id = gen_test_item(name="Alpha Asset")
    set_custom_field_value(item_id, serial_id, "SN-001")
  finally:
    reset_current_user(token)

  token = set_current_user(gen_test_admin)

  try:
    user_id = create_user("checker", "checker123", "Checker")
    role_id = create_role("Checker", "Inspects assets")

    permission = get_permission_by_name(f"field.{serial_id}.read")
    permission_id = (
      permission["id"]
      if permission is not None
      else create_permission(f"field.{serial_id}.read")
    )
    set_role_permission(role_id, permission_id, True)

    set_user_role(user_id, role_id)
  finally:
    reset_current_user(token)

  gen_test_client.post(
    "/auth/login",
    data={
      "username": "checker",
      "password": "checker123",
    },
  )

  response = gen_test_client.get("/inventory/export")

  rows = list(
    csv.reader(
      io.StringIO(response.get_data(as_text=True)),
    )
  )

  assert "Secret" not in rows[0]
  assert "Serial Number" in rows[0]


def test_export_empty_result_returns_headers(gen_test_admin_client):
  response = gen_test_admin_client.get("/inventory/export")

  rows = list(
    csv.reader(
      io.StringIO(response.get_data(as_text=True)),
    )
  )

  assert rows == [
    [
      "id",
      "name",
      "description",
      "location",
      "created_at",
      "updated_at",
      "archival_reason",
      "archival_notes",
    ]
  ]


def test_export_escapes_formula_injection_values(
  gen_test_admin_client,
  gen_test_item,
):
  gen_test_item(name="=cmd|'/c calc'!A0")
  gen_test_item(name="+SUM(A1)")
  gen_test_item(name="@import")
  gen_test_item(name="-3dB attenuator")
  gen_test_item(name="Normal Asset")

  response = gen_test_admin_client.get("/inventory/export")

  rows = list(
    csv.reader(
      io.StringIO(response.get_data(as_text=True)),
    )
  )

  names = [row[1] for row in rows[1:]]

  assert names == [
    "'+SUM(A1)",
    "'-3dB attenuator",
    "'=cmd|'/c calc'!A0",
    "'@import",
    "Normal Asset",
  ]


def test_export_creates_audit_log(
  gen_test_admin_client,
  gen_test_item,
):
  from app.services.data.audit import get_audit_logs

  gen_test_item(name="Alpha Asset")

  gen_test_admin_client.get("/inventory/export")

  logs = get_audit_logs()

  assert any(log["action"] == "exported" for log in logs)


def test_failed_export_creates_no_audit_log(gen_test_admin_client):
  from app.services.data.audit import get_audit_logs

  gen_test_admin_client.get(
    "/inventory/export",
    query_string={"fields": "not_a_field"},
  )

  logs = get_audit_logs()

  assert not any(log["action"] == "exported" for log in logs)


def test_export_requires_login(gen_test_client):
  response = gen_test_client.get("/inventory/export")

  assert response.status_code == 302

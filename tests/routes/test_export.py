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
  gen_test_admin_client.post(f"/inventory/{archived_id}/archive")

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


def test_export_includes_custom_fields(
  gen_test_admin_client,
  gen_test_item,
  gen_test_admin,
):
  from app.services.auth.context import set_current_user, reset_current_user
  from app.services.data.custom_field_values import set_custom_field_value
  from app.services.data.custom_fields import create_custom_field

  token = set_current_user(gen_test_admin)

  try:
    serial_id = create_custom_field("Serial Number", "text")
    quantity_id = create_custom_field("Quantity", "integer")

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
    "Quantity",
    "Serial Number",
  ]
  assert rows[1][6] == ""
  assert rows[1][7] == "SN-001"


def test_export_selected_custom_fields(
  gen_test_admin_client,
  gen_test_item,
  gen_test_admin,
):
  from app.services.auth.context import set_current_user, reset_current_user
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

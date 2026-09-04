import io

import pytest
from werkzeug.datastructures import FileStorage

from app.services.exceptions.data.common import InvalidInputError
from app.services.import_svc import parse_import_file


def make_upload(filename, content):
  return FileStorage(
    stream=io.BytesIO(content.encode("utf-8")),
    filename=filename,
    content_type="text/csv",
  )


def test_parse_csv_returns_rows():
  upload = make_upload(
    "items.csv",
    "name,description,location,Serial\nAlpha,,Office,SN-1\nBeta,With desc,,\n",
  )

  rows = parse_import_file(upload)

  assert rows == [
    {
      "name": "Alpha",
      "description": None,
      "location": "Office",
      "custom_fields": {"Serial": "SN-1"},
    },
    {
      "name": "Beta",
      "description": "With desc",
      "location": None,
      "custom_fields": {},
    },
  ]


def test_parse_csv_missing_name_column_raises():
  upload = make_upload("items.csv", "description,location\n,Office\n")

  with pytest.raises(InvalidInputError):
    parse_import_file(upload)


def test_parse_csv_ignores_id_and_timestamp_columns():
  upload = make_upload(
    "items.csv",
    "id,name,created_at,updated_at\n123,Alpha,2026-01-01,2026-01-02\n",
  )

  rows = parse_import_file(upload)

  assert rows == [
    {
      "name": "Alpha",
      "description": None,
      "location": None,
      "custom_fields": {},
    },
  ]


def make_xlsx_upload(rows):
  from openpyxl import Workbook

  workbook = Workbook()

  sheet = workbook.active

  for row in rows:
    sheet.append(row)

  stream = io.BytesIO()

  workbook.save(stream)

  stream.seek(0)

  return FileStorage(
    stream=stream,
    filename="items.xlsx",
    content_type=(
      "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    ),
  )


def test_parse_xlsx_returns_rows():
  upload = make_xlsx_upload(
    [
      ["name", "description", "location", "Serial"],
      ["Alpha", None, "Office", "SN-1"],
      ["Beta", "With desc", None, None],
    ],
  )

  rows = parse_import_file(upload)

  assert rows == [
    {
      "name": "Alpha",
      "description": None,
      "location": "Office",
      "custom_fields": {"Serial": "SN-1"},
    },
    {
      "name": "Beta",
      "description": "With desc",
      "location": None,
      "custom_fields": {},
    },
  ]


def test_parse_xlsx_missing_name_column_raises():
  upload = make_xlsx_upload(
    [
      ["description", "location"],
      [None, "Office"],
    ],
  )

  with pytest.raises(InvalidInputError):
    parse_import_file(upload)


def test_parse_unknown_extension_raises():
  upload = make_upload("items.txt", "name\nAlpha\n")

  with pytest.raises(InvalidInputError):
    parse_import_file(upload)


# ==================== import_items ====================


def test_import_items_generates_uuid_ids(gen_test_data_admin):
  from app.services.data.inventory import get_item, import_items

  result = import_items(
    [
      {"name": "Alpha", "description": None, "location": None, "custom_fields": {}},
      {"name": "Beta", "description": None, "location": None, "custom_fields": {}},
    ],
  )

  assert result["imported_count"] == 2
  assert len(result["item_ids"]) == 2

  for item_id in result["item_ids"]:
    assert get_item(item_id) is not None

  assert all("-" in item_id for item_id in result["item_ids"])
  assert len(set(result["item_ids"])) == 2


def test_import_items_requires_name(gen_test_data_admin):
  from app.services.data.inventory import import_items

  with pytest.raises(InvalidInputError):
    import_items(
      [{"name": None, "description": None, "location": None, "custom_fields": {}}],
    )


def test_import_items_leaves_unsupplied_fields_unset(gen_test_data_admin):
  from app.services.data.inventory import get_item, import_items

  result = import_items(
    [{"name": "Alpha", "description": None, "location": None, "custom_fields": {}}],
  )

  item = get_item(result["item_ids"][0])

  assert item["description"] is None
  assert item["location_name"] is None
  assert item["custom_fields"] == {}


def test_import_items_resolves_location_by_name(gen_test_data_admin):
  from app.services.auth.context import reset_current_user, set_current_user
  from app.services.data.inventory import get_item, import_items
  from app.services.data.locations import create_location

  token = set_current_user(gen_test_data_admin)

  try:
    create_location("Office")
  finally:
    reset_current_user(token)

  result = import_items(
    [
      {
        "name": "Alpha",
        "description": None,
        "location": "Office",
        "custom_fields": {},
      },
    ],
  )

  item = get_item(result["item_ids"][0])

  assert item["location_name"] == "Office"


def test_import_items_sets_custom_fields_skips_user_type(
  gen_test_data_admin,
):
  from app.services.auth.context import reset_current_user, set_current_user
  from app.services.data.custom_fields import create_custom_field
  from app.services.data.inventory import get_item, import_items

  token = set_current_user(gen_test_data_admin)

  try:
    serial_id = create_custom_field("Serial", "text")
    owner_id = create_custom_field("Owner", "user")
  finally:
    reset_current_user(token)

  result = import_items(
    [
      {
        "name": "Alpha",
        "description": None,
        "location": None,
        "custom_fields": {"Serial": "SN-1", "Owner": "test_admin"},
      },
    ],
  )

  item = get_item(result["item_ids"][0])

  assert item["custom_fields"]["Serial"] == "SN-1"
  assert "Owner" not in item["custom_fields"]


def test_import_items_unknown_location_rejects_atomically(gen_test_data_admin):
  from app.services.data.audit import get_audit_logs
  from app.services.data.inventory import get_items, import_items
  from app.services.exceptions.data.locations import LocationNotFoundError

  with pytest.raises(LocationNotFoundError):
    import_items(
      [
        {"name": "Alpha", "description": None, "location": None, "custom_fields": {}},
        {"name": "Beta", "description": None, "location": "Nope", "custom_fields": {}},
      ],
    )

  assert get_items() == []
  assert not any(log["action"] == "imported" for log in get_audit_logs())


def test_import_items_unknown_custom_field_rejects_atomically(
  gen_test_data_admin,
):
  from app.services.data.audit import get_audit_logs
  from app.services.data.inventory import get_items, import_items

  with pytest.raises(InvalidInputError):
    import_items(
      [
        {
          "name": "Alpha",
          "description": None,
          "location": None,
          "custom_fields": {"Nope": "x"},
        },
      ],
    )

  assert get_items() == []
  assert not any(log["action"] == "imported" for log in get_audit_logs())


def test_import_items_creates_imported_audit_log(gen_test_data_admin):
  from app.services.data.audit import get_audit_logs
  from app.services.data.inventory import import_items

  result = import_items(
    [{"name": "Alpha", "description": None, "location": None, "custom_fields": {}}],
  )

  imported = [
    log
    for log in get_audit_logs()
    if log["action"] == "imported"
  ]

  assert len(imported) == 1
  assert imported[0]["details"] == {"item_count": len(result["item_ids"])}
  assert imported[0]["user_id"] == gen_test_data_admin


# ==================== POST /inventory/import ====================


def test_import_requires_login(gen_test_client):
  response = gen_test_client.post("/inventory/import")

  assert response.status_code == 302


def test_import_requires_inventory_import_permission(
  gen_test_client,
  gen_test_admin,
):
  # The permission decorator denies unauthorized users; the existing
  # app-wide behavior raises PermissionDeniedError (unhandled → 500).
  from app.services.exceptions.auth.authorization import PermissionDeniedError
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

  with pytest.raises(PermissionDeniedError):
    gen_test_client.post(
      "/inventory/import",
      data={"file": (io.BytesIO(b"name\nAlpha\n"), "items.csv")},
      content_type="multipart/form-data",
    )


def test_import_returns_imported_count(gen_test_admin_client):
  response = gen_test_admin_client.post(
    "/inventory/import",
    data={
      "file": (
        io.BytesIO("name,description\nAlpha,First\nBeta,\n".encode("utf-8")),
        "items.csv",
      ),
    },
    content_type="multipart/form-data",
  )

  assert response.status_code == 200
  assert response.get_json() == {"imported_count": 2}


def test_import_invalid_file_returns_400(gen_test_admin_client):
  response = gen_test_admin_client.post(
    "/inventory/import",
    data={
      "file": (
        io.BytesIO("description\nFirst\n".encode("utf-8")),
        "items.csv",
      ),
    },
    content_type="multipart/form-data",
  )

  assert response.status_code == 400
  assert "error" in response.get_json()

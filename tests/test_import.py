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

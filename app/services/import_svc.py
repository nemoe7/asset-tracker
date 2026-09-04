import csv

from openpyxl import load_workbook

from .exceptions.data.common import InvalidInputError

_BUILTIN_COLUMNS = {"name", "description", "location"}
_IGNORED_COLUMNS = {"id", "created_at", "updated_at"}


def _cell(row, column):
  value = row.get(column)

  if value is None or str(value).strip() == "":
    return None

  return str(value).strip()


def _build_rows(dict_rows, columns):
  rows = []

  for row in dict_rows:
    custom_fields = {}

    for column in columns:
      value = _cell(row, column)

      if value is not None:
        custom_fields[column] = value

    rows.append(
      {
        "name": _cell(row, "name"),
        "description": _cell(row, "description"),
        "location": _cell(row, "location"),
        "custom_fields": custom_fields,
      },
    )

  return rows


def _parse_csv(file_storage):
  reader = csv.DictReader(
    line.decode("utf-8-sig") for line in file_storage.stream
  )

  fieldnames = reader.fieldnames

  if not fieldnames or "name" not in fieldnames:
    raise InvalidInputError("Import requires a name column")

  columns = [
    name
    for name in fieldnames
    if name and name not in _IGNORED_COLUMNS
    and name not in _BUILTIN_COLUMNS
  ]

  return _build_rows(reader, columns)


def _parse_xlsx(file_storage):
  try:
    workbook = load_workbook(file_storage, read_only=True, data_only=True)
  except Exception:
    raise InvalidInputError("Unreadable xlsx file") from None

  try:
    sheet = workbook.active

    dict_rows = sheet.values

    try:
      header = next(dict_rows)
    except StopIteration:
      raise InvalidInputError("Import requires a name column") from None

    header = [str(value) if value is not None else "" for value in header]

    if "name" not in header:
      raise InvalidInputError("Import requires a name column")

    rows = [
      dict(zip(header, row))
      for row in dict_rows
    ]

    columns = [
      name
      for name in header
      if name and name not in _IGNORED_COLUMNS
      and name not in _BUILTIN_COLUMNS
    ]

    return _build_rows(rows, columns)
  finally:
    workbook.close()


def parse_import_file(file_storage):
  filename = file_storage.filename or ""
  extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""

  if extension == "csv":
    return _parse_csv(file_storage)

  if extension == "xlsx":
    return _parse_xlsx(file_storage)

  raise InvalidInputError("Unsupported import file type")

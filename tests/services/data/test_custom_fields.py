import pytest

from app.services.data.custom_field_values import set_custom_field_value
from app.services.data.custom_fields import (
  archive_custom_field,
  create_custom_field,
  get_custom_field,
  get_custom_field_by_name,
  get_custom_fields,
  restore_custom_field,
  update_custom_field,
)
from app.services.data.db import db_transaction
from app.services.data.inventory import create_item
from app.services.exceptions.data.common import InvalidInputError
from app.services.exceptions.data.custom_fields import *


def test_get_custom_fields_tolerate_corrupt_enum_values(gen_test_data_admin):
  field_id = create_custom_field(
    name="Color",
    field_type="enum",
    enum_values=["red", "green"],
  )

  with db_transaction() as connection:
    connection.execute(
      """
      UPDATE custom_fields
      SET enum_values = 'not-json'
      WHERE id = ?
      """,
      (field_id,),
    )

  field = get_custom_field(field_id)

  assert field is not None
  assert field["enum_values"] is None

  fields = get_custom_fields()

  assert field_id in [entry["id"] for entry in fields]

  by_name = get_custom_field_by_name("Color")

  assert by_name is not None
  assert by_name["enum_values"] is None


def test_create_custom_field(gen_test_data_admin):
  field_id = create_custom_field(
    name="Serial Number",
    field_type="text",
    description="Item serial number",
    required=True,
  )

  field = get_custom_field(field_id)

  assert field["id"] == field_id
  assert field["name"] == "Serial Number"
  assert field["field_type"] == "text"
  assert field["description"] == "Item serial number"
  assert field["required"] == 1
  assert field["enum_values"] is None
  assert field["archived_at"] is None


def test_create_enum_custom_field(gen_test_data_admin):
  field_id = create_custom_field(
    name="Condition",
    field_type="enum",
    enum_values=["New", "Used", "Damaged"],
  )

  field = get_custom_field(field_id)

  assert field["field_type"] == "enum"
  assert field["enum_values"] == ["New", "Used", "Damaged"]


def test_create_custom_field_defaults(gen_test_data_admin):
  field_id = create_custom_field(
    name="Notes",
    field_type="text",
  )

  field = get_custom_field(field_id)

  assert field["description"] is None
  assert field["required"] == 0
  assert field["enum_values"] is None
  assert field["archived_at"] is None


def test_create_custom_field_rejects_empty_name(gen_test_data_admin):
  with pytest.raises(InvalidCustomFieldNameError):
    create_custom_field(
      name="",
      field_type="text",
    )


def test_create_custom_field_rejects_whitespace_name(gen_test_data_admin):
  with pytest.raises(InvalidCustomFieldNameError):
    create_custom_field(
      name="   ",
      field_type="text",
    )


def test_create_custom_field_rejects_non_string_name(gen_test_data_admin):
  with pytest.raises(InvalidCustomFieldNameError):
    create_custom_field(
      name=123,
      field_type="text",
    )


def test_create_custom_field_rejects_invalid_type(gen_test_data_admin):
  with pytest.raises(InvalidCustomFieldTypeError):
    create_custom_field(
      name="Test",
      field_type="invalid",
    )


def test_create_custom_field_rejects_non_boolean_required(gen_test_data_admin):
  with pytest.raises(InvalidCustomFieldRequiredError):
    create_custom_field(
      name="Test",
      field_type="text",
      required=1,
    )


def test_create_enum_custom_field_requires_values(gen_test_data_admin):
  with pytest.raises(
    InvalidCustomFieldEnumValuesError,
    match="non-empty list",
  ):
    create_custom_field(
      name="Condition",
      field_type="enum",
    )


def test_create_enum_custom_field_rejects_empty_values(gen_test_data_admin):
  with pytest.raises(
    InvalidCustomFieldEnumValuesError,
    match="non-empty list",
  ):
    create_custom_field(
      name="Condition",
      field_type="enum",
      enum_values=[],
    )


def test_create_enum_custom_field_rejects_non_list_values(gen_test_data_admin):
  with pytest.raises(
    InvalidCustomFieldEnumValuesError,
    match="non-empty list",
  ):
    create_custom_field(
      name="Condition",
      field_type="enum",
      enum_values='["New", "Used"]',
    )


def test_create_enum_custom_field_rejects_non_string_values(gen_test_data_admin):
  with pytest.raises(
    InvalidCustomFieldEnumValuesError,
    match="non-empty strings",
  ):
    create_custom_field(
      name="Condition",
      field_type="enum",
      enum_values=["New", 123],
    )


def test_create_enum_custom_field_rejects_duplicate_values(gen_test_data_admin):
  with pytest.raises(
    InvalidCustomFieldEnumValuesError,
    match="unique",
  ):
    create_custom_field(
      name="Condition",
      field_type="enum",
      enum_values=["New", "Used", "New"],
    )


def test_create_non_enum_custom_field_rejects_enum_values(gen_test_data_admin):
  with pytest.raises(
    InvalidCustomFieldEnumValuesError,
    match="only valid for enum fields",
  ):
    create_custom_field(
      name="Serial Number",
      field_type="text",
      enum_values=["A", "B"],
    )


def test_create_custom_field_rejects_duplicate_name(gen_test_data_admin):
  create_custom_field(
    name="Serial Number",
    field_type="text",
  )

  with pytest.raises(CustomFieldAlreadyExistsError):
    create_custom_field(
      name="Serial Number",
      field_type="text",
    )


def test_create_custom_field_rejects_name_reserved_by_archived_field(
  gen_test_data_admin,
):
  field_id = create_custom_field(
    name="Serial Number",
    field_type="text",
  )

  archive_custom_field(field_id)

  with pytest.raises(CustomFieldAlreadyExistsError):
    create_custom_field(
      name="Serial Number",
      field_type="text",
    )


def test_get_custom_field_returns_none_for_missing_field(gen_test_data_admin):
  assert get_custom_field(999) is None


def test_get_custom_fields_excludes_archived_by_default(gen_test_data_admin):
  active_id = create_custom_field(
    name="Active",
    field_type="text",
  )
  archived_id = create_custom_field(
    name="Archived",
    field_type="text",
  )

  archive_custom_field(archived_id)

  fields = get_custom_fields()

  assert [field["id"] for field in fields] == [active_id]


def test_get_custom_fields_can_include_archived(gen_test_data_admin):
  active_id = create_custom_field(
    name="Active",
    field_type="text",
  )
  archived_id = create_custom_field(
    name="Archived",
    field_type="text",
  )

  archive_custom_field(archived_id)

  fields = get_custom_fields(include_archived=True)
  field_ids = [field["id"] for field in fields]

  assert active_id in field_ids
  assert archived_id in field_ids


def test_get_custom_fields_orders_by_name(gen_test_data_admin):
  create_custom_field(
    name="Zebra",
    field_type="text",
  )
  create_custom_field(
    name="Alpha",
    field_type="text",
  )
  create_custom_field(
    name="Middle",
    field_type="text",
  )

  fields = get_custom_fields()

  assert [field["name"] for field in fields] == [
    "Alpha",
    "Middle",
    "Zebra",
  ]


def test_update_custom_field(gen_test_data_admin):
  field_id = create_custom_field(
    name="Serial Number",
    field_type="text",
  )

  assert update_custom_field(
    field_id,
    name="Asset Number",
    description="Internal asset identifier",
    required=True,
  )

  field = get_custom_field(field_id)

  assert field["name"] == "Asset Number"
  assert field["field_type"] == "text"
  assert field["description"] == "Internal asset identifier"
  assert field["required"] == 1


def test_update_custom_field_can_clear_description(gen_test_data_admin):
  field_id = create_custom_field(
    name="Serial Number",
    field_type="text",
    description="Description",
  )

  update_custom_field(
    field_id,
    description=None,
  )

  field = get_custom_field(field_id)

  assert field["description"] is None


def test_update_custom_field_can_clear_enum_values(gen_test_data_admin):
  field_id = create_custom_field(
    name="Condition",
    field_type="enum",
    enum_values=["New", "Used"],
  )

  update_custom_field(
    field_id,
    field_type="text",
    enum_values=None,
  )

  field = get_custom_field(field_id)

  assert field["field_type"] == "text"
  assert field["enum_values"] is None


def test_update_custom_field_can_change_enum_values(gen_test_data_admin):
  field_id = create_custom_field(
    name="Condition",
    field_type="enum",
    enum_values=["New", "Used"],
  )

  update_custom_field(
    field_id,
    enum_values=["New", "Used", "Damaged"],
  )

  field = get_custom_field(field_id)

  assert field["enum_values"] == ["New", "Used", "Damaged"]


def test_update_custom_field_preserves_unspecified_values(gen_test_data_admin):
  field_id = create_custom_field(
    name="Serial Number",
    field_type="text",
    description="Original",
    required=True,
  )

  update_custom_field(
    field_id,
    name="Asset Number",
  )

  field = get_custom_field(field_id)

  assert field["name"] == "Asset Number"
  assert field["description"] == "Original"
  assert field["required"] == 1
  assert field["field_type"] == "text"


def test_update_custom_field_requires_at_least_one_field(gen_test_data_admin):
  field_id = create_custom_field(
    name="Serial Number",
    field_type="text",
  )

  with pytest.raises(
    InvalidInputError,
    match="No fields to update",
  ):
    update_custom_field(field_id)


def test_update_custom_field_rejects_invalid_name(gen_test_data_admin):
  field_id = create_custom_field(
    name="Serial Number",
    field_type="text",
  )

  with pytest.raises(InvalidCustomFieldNameError):
    update_custom_field(
      field_id,
      name="",
    )


def test_update_custom_field_rejects_invalid_type(gen_test_data_admin):
  field_id = create_custom_field(
    name="Serial Number",
    field_type="text",
  )

  with pytest.raises(InvalidCustomFieldTypeError):
    update_custom_field(
      field_id,
      field_type="invalid",
    )


def test_update_custom_field_rejects_invalid_required(gen_test_data_admin):
  field_id = create_custom_field(
    name="Serial Number",
    field_type="text",
  )

  with pytest.raises(InvalidCustomFieldRequiredError):
    update_custom_field(
      field_id,
      required=1,
    )


def test_update_custom_field_rejects_invalid_enum_configuration(gen_test_data_admin):
  field_id = create_custom_field(
    name="Condition",
    field_type="enum",
    enum_values=["New", "Used"],
  )

  with pytest.raises(
    InvalidCustomFieldEnumValuesError,
    match="only valid for enum fields",
  ):
    update_custom_field(
      field_id,
      field_type="text",
      enum_values=["New", "Used"],
    )


def test_update_custom_field_rejects_empty_enum_values(gen_test_data_admin):
  field_id = create_custom_field(
    name="Condition",
    field_type="enum",
    enum_values=["New", "Used"],
  )

  with pytest.raises(
    InvalidCustomFieldEnumValuesError,
    match="non-empty list",
  ):
    update_custom_field(
      field_id,
      enum_values=[],
    )


def test_update_custom_field_rejects_duplicate_enum_values(gen_test_data_admin):
  field_id = create_custom_field(
    name="Condition",
    field_type="enum",
    enum_values=["New", "Used"],
  )

  with pytest.raises(
    InvalidCustomFieldEnumValuesError,
    match="unique",
  ):
    update_custom_field(
      field_id,
      enum_values=["New", "Used", "New"],
    )


def test_update_custom_field_rejects_duplicate_name(gen_test_data_admin):
  create_custom_field(
    name="Serial Number",
    field_type="text",
  )

  field_id = create_custom_field(
    name="Asset Number",
    field_type="text",
  )

  with pytest.raises(CustomFieldAlreadyExistsError):
    update_custom_field(
      field_id,
      name="Serial Number",
    )


def test_update_custom_field_missing_field(gen_test_data_admin):
  with pytest.raises(CustomFieldNotFoundError):
    update_custom_field(
      999,
      name="Test",
    )


def test_update_custom_field_can_change_type(gen_test_data_admin):
  field_id = create_custom_field(
    name="Value",
    field_type="text",
  )

  update_custom_field(
    field_id,
    field_type="integer",
  )

  field = get_custom_field(field_id)

  assert field["field_type"] == "integer"


def test_update_custom_field_rejects_type_change_when_in_use(
  gen_test_data_admin,
):
  field_id = create_custom_field(
    name="Value",
    field_type="text",
  )
  item_id = create_item(name="Test Item")

  set_custom_field_value(item_id, field_id, "value")

  with pytest.raises(CustomFieldInUseError):
    update_custom_field(
      field_id,
      field_type="integer",
    )


def test_archive_custom_field(gen_test_data_admin):
  field_id = create_custom_field(
    name="Serial Number",
    field_type="text",
  )

  assert archive_custom_field(field_id) is True

  field = get_custom_field(field_id)

  assert field["archived_at"] is not None


def test_archive_custom_field_missing_field(gen_test_data_admin):
  with pytest.raises(CustomFieldNotFoundError):
    archive_custom_field(999)


def test_unarchive_custom_field(gen_test_data_admin):
  field_id = create_custom_field(
    name="Serial Number",
    field_type="text",
  )

  archive_custom_field(field_id)

  assert restore_custom_field(field_id) is True

  field = get_custom_field(field_id)

  assert field["archived_at"] is None


def test_unarchive_custom_field_missing_field(gen_test_data_admin):
  with pytest.raises(CustomFieldNotFoundError):
    restore_custom_field(999)


def test_archive_custom_field_rejects_archived_field(gen_test_data_admin):
  field_id = create_custom_field(
    name="Serial Number",
    field_type="text",
  )

  archive_custom_field(field_id)

  with pytest.raises(CustomFieldIsArchivedError):
    archive_custom_field(field_id)


def test_restore_custom_field_rejects_active_field(gen_test_data_admin):
  field_id = create_custom_field(
    name="Serial Number",
    field_type="text",
  )

  with pytest.raises(CustomFieldIsNotArchivedError):
    restore_custom_field(field_id)


def test_restore_custom_field_succeeds_for_archived_field(gen_test_data_admin):
  field_id = create_custom_field(
    name="Serial Number",
    field_type="text",
  )

  archive_custom_field(field_id)

  assert restore_custom_field(field_id) is True

def test_get_custom_field_by_name(gen_test_data_admin):
  field_id = create_custom_field(
    name="Serial Number",
    field_type="text",
  )

  field = get_custom_field_by_name("Serial Number")

  assert field["id"] == field_id
  assert field["name"] == "Serial Number"
  assert field["field_type"] == "text"


def test_get_nonexistent_custom_field_by_name(gen_test_data_admin):
  assert get_custom_field_by_name("does-not-exist") is None

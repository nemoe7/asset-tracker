import pytest

from app.services.data.custom_field_values import (
  delete_custom_field_value,
  get_custom_field_value,
  get_custom_field_values,
  set_custom_field_value,
)
from app.services.data.custom_fields import (
  archive_custom_field,
  create_custom_field,
)
from app.services.data.inventory import (
  archive_item,
  create_item,
)
from app.services.exceptions.data.custom_field_values import *
from app.services.exceptions.data.custom_fields import (
  CustomFieldArchivedError,
  CustomFieldNotFoundError,
)
from app.services.exceptions.data.inventory import ItemNotFoundError


def test_set_custom_field_value(gen_test_admin):
  field_id = create_custom_field(
    name="Serial Number",
    field_type="text",
  )
  item_id = create_item(
    name="Test Item",
  )

  assert (
    set_custom_field_value(
      item_id,
      field_id,
      "SN-123",
    )
    is True
  )

  value = get_custom_field_value(
    item_id,
    field_id,
  )

  assert value["item_id"] == item_id
  assert value["field_id"] == field_id
  assert value["value"] == "SN-123"


def test_set_custom_field_value_updates_existing_value(gen_test_admin):
  field_id = create_custom_field(
    name="Serial Number",
    field_type="text",
  )
  item_id = create_item(
    name="Test Item",
  )

  set_custom_field_value(
    item_id,
    field_id,
    "SN-123",
  )
  set_custom_field_value(
    item_id,
    field_id,
    "SN-456",
  )

  value = get_custom_field_value(
    item_id,
    field_id,
  )

  assert value["value"] == "SN-456"


def test_set_custom_field_value_can_clear_optional_value(gen_test_admin):
  field_id = create_custom_field(
    name="Serial Number",
    field_type="text",
  )
  item_id = create_item(
    name="Test Item",
  )

  set_custom_field_value(
    item_id,
    field_id,
    "SN-123",
  )
  set_custom_field_value(
    item_id,
    field_id,
    None,
  )

  assert (
    get_custom_field_value(
      item_id,
      field_id,
    )
    is None
  )


def test_required_custom_field_can_initially_be_unset(gen_test_admin):
  field_id = create_custom_field(
    name="Serial Number",
    field_type="text",
    required=True,
  )
  item_id = create_item(
    name="Test Item",
  )

  assert (
    get_custom_field_value(
      item_id,
      field_id,
    )
    is None
  )


def test_set_required_custom_field_value_rejects_none(gen_test_admin):
  field_id = create_custom_field(
    name="Serial Number",
    field_type="text",
    required=True,
  )
  item_id = create_item(
    name="Test Item",
  )

  with pytest.raises(RequiredCustomFieldError):
    set_custom_field_value(
      item_id,
      field_id,
      None,
    )


def test_set_required_custom_field_value_rejects_clearing_existing_value(
  gen_test_admin,
):
  field_id = create_custom_field(
    name="Serial Number",
    field_type="text",
    required=True,
  )
  item_id = create_item(
    name="Test Item",
  )

  set_custom_field_value(
    item_id,
    field_id,
    "SN-123",
  )

  with pytest.raises(RequiredCustomFieldError):
    set_custom_field_value(
      item_id,
      field_id,
      None,
    )

  value = get_custom_field_value(
    item_id,
    field_id,
  )

  assert value["value"] == "SN-123"


def test_set_custom_field_value_rejects_missing_item(gen_test_admin):
  field_id = create_custom_field(
    name="Serial Number",
    field_type="text",
  )

  with pytest.raises(ItemNotFoundError):
    set_custom_field_value(
      "missing-item",
      field_id,
      "SN-123",
    )


def test_set_custom_field_value_rejects_missing_field(gen_test_admin):
  item_id = create_item(
    name="Test Item",
  )

  with pytest.raises(CustomFieldNotFoundError):
    set_custom_field_value(
      item_id,
      999,
      "SN-123",
    )


def test_set_custom_field_value_rejects_archived_field(gen_test_admin):
  field_id = create_custom_field(
    name="Serial Number",
    field_type="text",
  )
  item_id = create_item(
    name="Test Item",
  )

  archive_custom_field(field_id)

  with pytest.raises(CustomFieldArchivedError):
    set_custom_field_value(
      item_id,
      field_id,
      "SN-123",
    )


def test_set_text_custom_field_value(gen_test_admin):
  field_id = create_custom_field(
    name="Notes",
    field_type="text",
  )
  item_id = create_item(
    name="Test Item",
  )

  set_custom_field_value(
    item_id,
    field_id,
    "Some notes",
  )

  value = get_custom_field_value(
    item_id,
    field_id,
  )

  assert value["value"] == "Some notes"


def test_set_text_custom_field_value_rejects_non_string(gen_test_admin):
  field_id = create_custom_field(
    name="Notes",
    field_type="text",
  )
  item_id = create_item(
    name="Test Item",
  )

  with pytest.raises(InvalidCustomFieldValueError):
    set_custom_field_value(
      item_id,
      field_id,
      123,
    )


def test_set_integer_custom_field_value(gen_test_admin):
  field_id = create_custom_field(
    name="Quantity",
    field_type="integer",
  )
  item_id = create_item(
    name="Test Item",
  )

  set_custom_field_value(
    item_id,
    field_id,
    42,
  )

  value = get_custom_field_value(
    item_id,
    field_id,
  )

  assert value["value"] == "42"


def test_set_integer_custom_field_value_rejects_invalid_value(gen_test_admin):
  field_id = create_custom_field(
    name="Quantity",
    field_type="integer",
  )
  item_id = create_item(
    name="Test Item",
  )

  with pytest.raises(InvalidCustomFieldValueError):
    set_custom_field_value(
      item_id,
      field_id,
      "not an integer",
    )


def test_set_integer_custom_field_value_rejects_boolean(gen_test_admin):
  field_id = create_custom_field(
    name="Quantity",
    field_type="integer",
  )
  item_id = create_item(
    name="Test Item",
  )

  with pytest.raises(InvalidCustomFieldValueError):
    set_custom_field_value(
      item_id,
      field_id,
      True,
    )


def test_set_decimal_custom_field_value(gen_test_admin):
  field_id = create_custom_field(
    name="Weight",
    field_type="decimal",
  )
  item_id = create_item(
    name="Test Item",
  )

  set_custom_field_value(
    item_id,
    field_id,
    12.5,
  )

  value = get_custom_field_value(
    item_id,
    field_id,
  )

  assert value["value"] == "12.5"


def test_set_decimal_custom_field_value_rejects_invalid_value(gen_test_admin):
  field_id = create_custom_field(
    name="Weight",
    field_type="decimal",
  )
  item_id = create_item(
    name="Test Item",
  )

  with pytest.raises(InvalidCustomFieldValueError):
    set_custom_field_value(
      item_id,
      field_id,
      "not a decimal",
    )


def test_set_boolean_custom_field_value(gen_test_admin):
  field_id = create_custom_field(
    name="Active",
    field_type="boolean",
  )
  item_id = create_item(
    name="Test Item",
  )

  set_custom_field_value(
    item_id,
    field_id,
    True,
  )

  value = get_custom_field_value(
    item_id,
    field_id,
  )

  assert value["value"] == "1"


def test_set_boolean_custom_field_value_rejects_invalid_value(gen_test_admin):
  field_id = create_custom_field(
    name="Active",
    field_type="boolean",
  )
  item_id = create_item(
    name="Test Item",
  )

  with pytest.raises(InvalidCustomFieldValueError):
    set_custom_field_value(
      item_id,
      field_id,
      "true",
    )


def test_set_date_custom_field_value(gen_test_admin):
  field_id = create_custom_field(
    name="Purchase Date",
    field_type="date",
  )
  item_id = create_item(
    name="Test Item",
  )

  set_custom_field_value(
    item_id,
    field_id,
    "2026-08-20",
  )

  value = get_custom_field_value(
    item_id,
    field_id,
  )

  assert value["value"] == "2026-08-20"


def test_set_date_custom_field_value_rejects_invalid_value(gen_test_admin):
  field_id = create_custom_field(
    name="Purchase Date",
    field_type="date",
  )
  item_id = create_item(
    name="Test Item",
  )

  with pytest.raises(InvalidCustomFieldValueError):
    set_custom_field_value(
      item_id,
      field_id,
      "not a date",
    )


def test_set_enum_custom_field_value(gen_test_admin):
  field_id = create_custom_field(
    name="Condition",
    field_type="enum",
    enum_values=[
      "New",
      "Used",
      "Damaged",
    ],
  )
  item_id = create_item(
    name="Test Item",
  )

  set_custom_field_value(
    item_id,
    field_id,
    "Used",
  )

  value = get_custom_field_value(
    item_id,
    field_id,
  )

  assert value["value"] == "Used"


def test_set_enum_custom_field_value_rejects_invalid_value(gen_test_admin):
  field_id = create_custom_field(
    name="Condition",
    field_type="enum",
    enum_values=[
      "New",
      "Used",
      "Damaged",
    ],
  )
  item_id = create_item(
    name="Test Item",
  )

  with pytest.raises(InvalidCustomFieldEnumValueError):
    set_custom_field_value(
      item_id,
      field_id,
      "Broken",
    )


def test_set_enum_custom_field_value_rejects_non_string(gen_test_admin):
  field_id = create_custom_field(
    name="Condition",
    field_type="enum",
    enum_values=[
      "New",
      "Used",
      "Damaged",
    ],
  )
  item_id = create_item(
    name="Test Item",
  )

  with pytest.raises(InvalidCustomFieldEnumValueError):
    set_custom_field_value(
      item_id,
      field_id,
      1,
    )


def test_set_user_custom_field_value(
  gen_test_admin,
  gen_test_user,
):
  field_id = create_custom_field(
    name="Assigned To",
    field_type="user",
  )
  item_id = create_item(
    name="Test Item",
  )
  user_id = gen_test_user(
    "item_owner",
  )

  set_custom_field_value(
    item_id,
    field_id,
    user_id,
  )

  value = get_custom_field_value(
    item_id,
    field_id,
  )

  assert value["value"] == str(user_id)


def test_set_user_custom_field_value_rejects_missing_user(gen_test_admin):
  field_id = create_custom_field(
    name="Assigned To",
    field_type="user",
  )
  item_id = create_item(
    name="Test Item",
  )

  with pytest.raises(InvalidCustomFieldValueError):
    set_custom_field_value(
      item_id,
      field_id,
      999,
    )


def test_set_user_custom_field_value_rejects_non_integer(gen_test_admin):
  field_id = create_custom_field(
    name="Assigned To",
    field_type="user",
  )
  item_id = create_item(
    name="Test Item",
  )

  with pytest.raises(InvalidCustomFieldValueError):
    set_custom_field_value(
      item_id,
      field_id,
      "not a user id",
    )


def test_get_custom_field_values(gen_test_admin):
  first_field_id = create_custom_field(
    name="Serial Number",
    field_type="text",
  )
  second_field_id = create_custom_field(
    name="Quantity",
    field_type="integer",
  )
  item_id = create_item(
    name="Test Item",
  )

  set_custom_field_value(
    item_id,
    first_field_id,
    "SN-123",
  )
  set_custom_field_value(
    item_id,
    second_field_id,
    42,
  )

  values = get_custom_field_values(
    item_id,
  )

  assert len(values) == 2

  assert values[0]["item_id"] == item_id
  assert values[0]["field_id"] == first_field_id
  assert values[0]["value"] == "SN-123"

  assert values[1]["item_id"] == item_id
  assert values[1]["field_id"] == second_field_id
  assert values[1]["value"] == "42"


def test_get_custom_field_values_returns_empty_list(gen_test_admin):
  item_id = create_item(
    name="Test Item",
  )

  assert (
    get_custom_field_values(
      item_id,
    )
    == []
  )


def test_get_custom_field_value_returns_none_when_missing(gen_test_admin):
  field_id = create_custom_field(
    name="Serial Number",
    field_type="text",
  )
  item_id = create_item(
    name="Test Item",
  )

  assert (
    get_custom_field_value(
      item_id,
      field_id,
    )
    is None
  )


def test_delete_custom_field_value(gen_test_admin):
  field_id = create_custom_field(
    name="Serial Number",
    field_type="text",
  )
  item_id = create_item(
    name="Test Item",
  )

  set_custom_field_value(
    item_id,
    field_id,
    "SN-123",
  )

  assert (
    delete_custom_field_value(
      item_id,
      field_id,
    )
    is True
  )

  assert (
    get_custom_field_value(
      item_id,
      field_id,
    )
    is None
  )


def test_delete_custom_field_value_rejects_missing_value(
  gen_test_admin,
):
  field_id = create_custom_field(
    name="Serial Number",
    field_type="text",
  )
  item_id = create_item(
    name="Test Item",
  )

  with pytest.raises(CustomFieldValueNotFoundError):
    delete_custom_field_value(
      item_id,
      field_id,
    )


def test_custom_field_values_are_preserved_when_inventory_item_is_archived(
  gen_test_admin,
):
  field_id = create_custom_field(
    name="Serial Number",
    field_type="text",
  )
  item_id = create_item(
    name="Test Item",
  )

  set_custom_field_value(
    item_id,
    field_id,
    "SN-123",
  )

  archive_item(
    item_id,
  )

  value = get_custom_field_value(
    item_id,
    field_id,
  )

  assert value["value"] == "SN-123"

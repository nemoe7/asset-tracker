import pytest
from playwright.sync_api import expect


@pytest.fixture
def typed_fields(create_custom_field):
  return {
    "text": create_custom_field("Serial Number", "text"),
    "integer": create_custom_field("Quantity", "integer"),
    "decimal": create_custom_field("Price", "decimal"),
    "date": create_custom_field("Purchased", "date"),
    "boolean": create_custom_field("Active", "boolean"),
    "enum": create_custom_field(
      "Category",
      "enum",
      enum_values=["Electronics", "Furniture"],
    ),
  }


@pytest.mark.e2e
def test_add_item_modal_renders_custom_field_inputs(
  page,
  live_server,
  typed_fields,
):
  page.goto(f"{live_server}/")
  page.locator("#add-item-button").click()

  modal = page.get_by_role("dialog")

  expect(modal.locator('input[name="f_Serial Number"]')).to_be_visible()
  expect(modal.locator('input[name="f_Quantity"]')).to_be_visible()
  expect(modal.locator('input[name="f_Quantity"]')).to_have_attribute(
    "type",
    "number",
  )
  expect(modal.locator('input[name="f_Price"]')).to_have_attribute(
    "type",
    "number",
  )
  expect(modal.locator('input[name="f_Purchased"]')).to_have_attribute(
    "type",
    "date",
  )

  boolean_select = modal.locator('select[name="f_Active"]')

  expect(boolean_select).to_be_visible()
  expect(boolean_select.locator('option[value="true"]')).to_have_count(1)
  expect(boolean_select.locator('option[value="false"]')).to_have_count(1)

  enum_select = modal.locator('select[name="f_Category"]')

  expect(enum_select).to_be_visible()
  expect(enum_select.locator('option[value="Electronics"]')).to_have_count(1)
  expect(enum_select.locator('option[value="Furniture"]')).to_have_count(1)


@pytest.mark.e2e
def test_add_item_modal_marks_required_custom_fields(
  page,
  live_server,
  create_custom_field,
):
  create_custom_field("Serial Number", "text", required=True)
  create_custom_field("Notes", "text")

  page.goto(f"{live_server}/")
  page.locator("#add-item-button").click()

  modal = page.get_by_role("dialog")

  expect(modal.locator('input[name="f_Serial Number"]')).to_have_attribute(
    "required",
    "",
  )
  expect(modal.locator('input[name="f_Notes"]')).not_to_have_attribute(
    "required",
    "",
  )


@pytest.mark.e2e
def test_add_item_modal_does_not_render_user_type_fields(
  page,
  live_server,
  create_custom_field,
):
  create_custom_field("Assignee", "user")

  page.goto(f"{live_server}/")
  page.locator("#add-item-button").click()

  modal = page.get_by_role("dialog")

  expect(modal.locator('input[name="f_Assignee"]')).to_have_count(0)
  expect(modal.locator('select[name="f_Assignee"]')).to_have_count(0)


@pytest.mark.e2e
def test_add_item_persists_custom_field_values(
  page,
  live_server,
  typed_fields,
):
  page.goto(f"{live_server}/")
  page.locator("#add-item-button").click()

  modal = page.get_by_role("dialog")

  modal.locator("#item-name").fill("Labeled Asset")
  modal.locator('input[name="f_Serial Number"]').fill("SN-100")
  modal.locator('input[name="f_Quantity"]').fill("5")
  modal.locator('select[name="f_Active"]').select_option("true")
  modal.locator('select[name="f_Category"]').select_option("Electronics")

  modal.get_by_role("button", name="Add item").click()

  row = page.get_by_role("row").filter(has_text="Labeled Asset")

  expect(row).to_be_visible()

  row.click()

  view_modal = page.get_by_role("dialog")

  expect(view_modal.get_by_text("SN-100")).to_be_visible()
  expect(view_modal.get_by_text("True")).to_be_visible()
  expect(view_modal.get_by_text("Electronics")).to_be_visible()


@pytest.mark.e2e
def test_add_item_required_custom_field_blocks_submit(
  page,
  live_server,
  create_custom_field,
):
  create_custom_field("Serial Number", "text", required=True)

  page.goto(f"{live_server}/")
  page.locator("#add-item-button").click()

  modal = page.get_by_role("dialog")

  modal.locator("#item-name").fill("Blocked Asset")
  modal.get_by_role("button", name="Add item").click()

  expect(page.get_by_role("row").filter(has_text="Blocked Asset")).to_have_count(0)
  expect(modal.locator('input[name="f_Serial Number"]')).to_be_visible()


@pytest.mark.e2e
def test_view_modal_shows_custom_field_values(
  page,
  live_server,
  create_custom_field,
  create_item,
  set_item_custom_field,
):
  text_field = create_custom_field("Serial Number", "text")
  boolean_field = create_custom_field("Active", "boolean")
  create_custom_field("Notes", "text")

  item = create_item("Viewed Asset")

  set_item_custom_field(item["id"], text_field["name"], "SN-200")
  set_item_custom_field(item["id"], boolean_field["name"], "true")

  page.goto(f"{live_server}/")
  page.get_by_role("row").filter(has_text="Viewed Asset").click()

  view_modal = page.get_by_role("dialog")

  expect(view_modal.get_by_text("Serial Number")).to_be_visible()
  expect(view_modal.get_by_text("SN-200")).to_be_visible()
  expect(view_modal.get_by_text("True")).to_be_visible()
  # Empty Notes + the built-in Description and Location placeholders.
  expect(view_modal.get_by_text("—")).to_have_count(3)


@pytest.mark.e2e
def test_edit_modal_prefills_and_updates_custom_fields(
  page,
  live_server,
  create_custom_field,
  create_item,
  set_item_custom_field,
):
  text_field = create_custom_field("Serial Number", "text")
  boolean_field = create_custom_field("Active", "boolean")

  item = create_item("Edited Asset")

  set_item_custom_field(item["id"], text_field["name"], "SN-300")
  set_item_custom_field(item["id"], boolean_field["name"], "true")

  page.goto(f"{live_server}/")

  row = page.get_by_role("row").filter(has_text="Edited Asset")

  row.locator(".edit-item").click()

  edit_modal = page.get_by_role("dialog")

  expect(edit_modal.locator('input[name="f_Serial Number"]')).to_have_value(
    "SN-300"
  )
  expect(edit_modal.locator('select[name="f_Active"]')).to_have_value("true")

  edit_modal.locator('input[name="f_Serial Number"]').fill("SN-301")
  edit_modal.locator('select[name="f_Active"]').select_option("false")
  edit_modal.get_by_role("button", name="Save changes").click()

  row.click()

  view_modal = page.get_by_role("dialog")

  expect(view_modal.get_by_text("SN-301")).to_be_visible()
  expect(view_modal.get_by_text("False")).to_be_visible()


@pytest.mark.e2e
def test_edit_modal_clearing_optional_custom_field(
  page,
  live_server,
  create_custom_field,
  create_item,
  set_item_custom_field,
):
  text_field = create_custom_field("Serial Number", "text")

  item = create_item("Cleared Asset")

  set_item_custom_field(item["id"], text_field["name"], "SN-400")

  page.goto(f"{live_server}/")

  row = page.get_by_role("row").filter(has_text="Cleared Asset")

  row.locator(".edit-item").click()

  edit_modal = page.get_by_role("dialog")

  edit_modal.locator('input[name="f_Serial Number"]').fill("")

  edit_modal.get_by_role("button", name="Save changes").click()

  row.click()

  view_modal = page.get_by_role("dialog")

  expect(view_modal.get_by_text("SN-400")).to_have_count(0)

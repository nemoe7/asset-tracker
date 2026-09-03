import pytest
from playwright.sync_api import expect


@pytest.fixture
def sort_fields(create_custom_field):
  return {
    "text": create_custom_field("Serial", "text"),
    "integer": create_custom_field("Quantity", "integer"),
    "date": create_custom_field("Purchased", "date"),
    "enum": create_custom_field(
      "Category",
      "enum",
      enum_values=["Electronics", "Furniture"],
    ),
    "boolean": create_custom_field("Active", "boolean"),
  }


def open_filter_modal(page, live_server):
  page.goto(f"{live_server}/")
  page.locator("#filter-item-button").click()

  return page.get_by_role("dialog")


def add_field_filter_row(page):
  page.locator("#add-field-filter-button").click()

  return page.locator("#custom-field-filter-rows .cf-filter-row").last


@pytest.mark.e2e
def test_filter_modal_adds_and_removes_field_filter_rows(
  page,
  live_server,
  sort_fields,
):
  modal = open_filter_modal(page, live_server)

  rows = page.locator("#custom-field-filter-rows .cf-filter-row")

  expect(rows).to_have_count(0)

  page.locator("#add-field-filter-button").click()

  row = rows.nth(0)

  expect(row.locator("select.cf-filter-field")).to_be_visible()
  expect(row.locator("select.cf-filter-op")).to_have_count(0)

  row.locator("select.cf-filter-field").select_option(label="Serial")

  expect(row.locator("select.cf-filter-op")).to_be_visible()
  expect(row.locator("[name='f_value']")).to_be_visible()

  page.locator("#add-field-filter-button").click()

  expect(rows).to_have_count(2)

  rows.nth(1).locator(".cf-filter-row-remove").click()

  expect(rows).to_have_count(1)

  expect(modal.get_by_role("heading", name="Filter & Sort")).to_be_visible()


@pytest.mark.e2e
def test_filter_row_controls_change_with_field_type(
  page,
  live_server,
  sort_fields,
):
  open_filter_modal(page, live_server)
  page.locator("#add-field-filter-button").click()

  row = page.locator("#custom-field-filter-rows .cf-filter-row").last
  field_select = row.locator("select.cf-filter-field")
  op_select = row.locator("select.cf-filter-op")

  field_select.select_option(label="Quantity")

  expect(op_select.locator("option")).to_have_text(
    ["=", "!=", "<", "<=", ">", ">="]
  )
  expect(row.locator("input[name='f_value']")).to_have_attribute("type", "number")

  field_select.select_option(label="Purchased")

  expect(op_select.locator("option")).to_have_text(
    ["On", "Not on", "Before", "No later than", "After", "No earlier than"]
  )
  expect(row.locator("input[name='f_value']")).to_have_attribute("type", "date")

  field_select.select_option(label="Category")

  expect(op_select.locator("option")).to_have_text(["Is", "Is not"])
  expect(row.locator("select[name='f_value']")).to_be_visible()

  field_select.select_option(label="Active")

  expect(op_select).to_have_count(0)
  expect(row.locator("select[name='f_value']")).to_be_visible()
  expect(row.locator("select[name='f_value'] option")).to_have_text(
    ["—", "True", "False"]
  )

  field_select.select_option(label="Serial")

  expect(row.locator("select.cf-filter-op option")).to_have_text(
    ["Contains", "Excludes"]
  )
  expect(row.locator(".cf-filter-match-case")).to_be_visible()


@pytest.mark.e2e
def test_filter_rows_persist_when_modal_reopened(page, live_server, sort_fields):
  open_filter_modal(page, live_server)
  page.locator("#add-field-filter-button").click()

  row = page.locator("#custom-field-filter-rows .cf-filter-row").last

  row.locator("select.cf-filter-field").select_option(label="Serial")
  row.locator("input[name='f_value']").fill("SN-1")

  page.get_by_role("button", name="Close").click()
  page.locator("#filter-item-button").click()

  row = page.locator("#custom-field-filter-rows .cf-filter-row").last

  expect(row.locator("select.cf-filter-field")).to_have_value(
    str(sort_fields["text"]["id"])
  )
  expect(row.locator("input[name='f_value']")).to_have_value("SN-1")


@pytest.mark.e2e
def test_filter_applies_custom_field_filters(
  page,
  live_server,
  create_custom_field,
  create_item,
  set_item_custom_field,
):
  text_field = create_custom_field("Serial", "text")

  match_id = create_item("Matched")
  create_item("Unmatched")

  set_item_custom_field(match_id["id"], text_field["name"], "has NEEDLE inside")

  modal = open_filter_modal(page, live_server)
  page.locator("#add-field-filter-button").click()

  row = page.locator("#custom-field-filter-rows .cf-filter-row").last

  row.locator("select.cf-filter-field").select_option(label="Serial")
  row.locator("select.cf-filter-op").select_option("contains")
  row.locator("input[name='f_value']").fill("needle")

  # An empty second row must be ignored on Apply.
  page.locator("#add-field-filter-button").click()

  modal.get_by_role("button", name="Apply").click()

  expect(page.get_by_role("row").filter(has_text="Matched")).to_be_visible()
  expect(page.get_by_role("row").filter(has_text="Unmatched")).to_have_count(0)


@pytest.mark.e2e
def test_filter_clear_removes_field_filter_rows(page, live_server, sort_fields):
  open_filter_modal(page, live_server)

  page.locator("#add-field-filter-button").click()
  page.locator("#add-field-filter-button").click()

  page.get_by_role("button", name="Clear").click()

  page.locator("#filter-item-button").click()

  expect(page.locator("#custom-field-filter-rows .cf-filter-row")).to_have_count(0)


@pytest.mark.e2e
def test_filter_sort_by_lists_custom_fields_and_sorts(
  page,
  live_server,
  create_custom_field,
  create_item,
  set_item_custom_field,
):
  integer_field = create_custom_field("Quantity", "integer")

  item_b = create_item("Beta")
  item_a = create_item("Alpha")

  set_item_custom_field(item_b["id"], integer_field["name"], "2")
  set_item_custom_field(item_a["id"], integer_field["name"], "1")

  modal = open_filter_modal(page, live_server)

  sort_select = modal.locator("#filter-sort-by")

  sort_select.select_option(label="Quantity")
  modal.get_by_role("button", name="Apply").click()

  items = page.locator("#inventory-items article")

  expect(items).to_have_count(2)
  expect(items.nth(0)).to_contain_text("Alpha")
  expect(items.nth(1)).to_contain_text("Beta")


@pytest.mark.e2e
def test_filtered_custom_fields_shown_in_table_and_cards(
  page,
  live_server,
  create_custom_field,
  create_item,
  set_item_custom_field,
):
  text_field = create_custom_field("Serial", "text")
  boolean_field = create_custom_field("Active", "boolean")

  item_one = create_item("Asset One")
  item_two = create_item("Asset Two")

  set_item_custom_field(item_one["id"], text_field["name"], "SN-ONE")
  set_item_custom_field(item_one["id"], boolean_field["name"], "true")
  set_item_custom_field(item_two["id"], text_field["name"], "SN-TWO")
  set_item_custom_field(item_two["id"], boolean_field["name"], "true")

  modal = open_filter_modal(page, live_server)

  # Row 1: Serial contains SN.
  page.locator("#add-field-filter-button").click()

  row = page.locator("#custom-field-filter-rows .cf-filter-row").last

  row.locator("select.cf-filter-field").select_option(label="Serial")
  row.locator("select.cf-filter-op").select_option("contains")
  row.locator("input[name='f_value']").fill("SN")

  # Row 2: Active is True.
  page.locator("#add-field-filter-button").click()

  row = page.locator("#custom-field-filter-rows .cf-filter-row").last

  row.locator("select.cf-filter-field").select_option(label="Active")
  row.locator("select[name='f_value']").select_option("true")

  modal.get_by_role("button", name="Apply").click()

  expect(page.get_by_role("row").filter(has_text="Asset One")).to_be_visible()

  # Desktop table: a column per filtered field.
  header_row = page.locator("#inventory-items thead tr")

  expect(header_row.locator("th").filter(has_text="Serial")).to_be_visible()
  expect(header_row.locator("th").filter(has_text="Active")).to_be_visible()

  row_one = page.get_by_role("row").filter(has_text="Asset One")

  expect(row_one.get_by_text("SN-ONE")).to_be_visible()
  expect(row_one.get_by_text("True")).to_be_visible()

  row_two = page.get_by_role("row").filter(has_text="Asset Two")

  expect(row_two.get_by_text("SN-TWO")).to_be_visible()

  # Mobile cards: filtered field values are listed on the card.
  cards = page.locator("#inventory-items article")

  expect(cards.filter(has_text="Asset One")).to_contain_text("SN-ONE")
  expect(cards.filter(has_text="Asset Two")).to_contain_text("SN-TWO")
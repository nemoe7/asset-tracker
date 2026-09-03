import pytest
from playwright.sync_api import expect


def open_export_modal(page):
  menu = page.locator("details")

  menu.locator("summary").click()
  menu.locator("#export-button").click()

  return page.get_by_role("dialog")


def apply_filter(page):
  page.locator("#filter-item-button").click()

  modal = page.locator("#filter-item-modal")

  expect(modal).to_be_visible()

  return modal


def add_field_filter_row(page, label):
  page.locator("#add-field-filter-button").click()

  row = page.locator("#custom-field-filter-rows .cf-filter-row").last

  row.locator("select.cf-filter-field").select_option(label=label)


@pytest.fixture
def serial_field(create_custom_field):
  return create_custom_field("Serial", "text")


@pytest.mark.e2e
def test_export_button_opens_export_modal(page, live_server, setup_admin):
  page.goto(f"{live_server}/")

  modal = open_export_modal(page)

  expect(modal.get_by_role("heading", name="Export CSV")).to_be_visible()
  expect(page.locator("#add-export-column")).to_be_visible()
  expect(page.locator("#export-column-options")).to_be_attached()


@pytest.mark.e2e
def test_export_modal_prefills_columns_from_active_filters(
  page,
  live_server,
  setup_admin,
  create_location,
):
  create_location("HQ")

  page.goto(f"{live_server}/")

  page.locator("#search").fill("Alpha")

  modal = apply_filter(page)

  modal.locator("#filter-include-archived").check()
  modal.locator("#filter-location").select_option(label="HQ")
  modal.get_by_role("button", name="Apply").click()

  rows = page.locator("#export-column-rows .export-column-row")

  open_export_modal(page)

  expect(rows).to_have_count(3)
  expect(rows.nth(0).locator(".export-column-name")).to_have_text("id")
  expect(rows.nth(1).locator(".export-column-name")).to_have_text("name")
  expect(rows.nth(2).locator(".export-column-name")).to_have_text("location")


@pytest.mark.e2e
def test_export_modal_prefills_custom_fields_from_field_filters(
  page,
  live_server,
  setup_admin,
  serial_field,
):
  page.goto(f"{live_server}/")

  modal = apply_filter(page)

  add_field_filter_row(page, "Serial")
  modal.get_by_role("button", name="Apply").click()

  rows = page.locator("#export-column-rows .export-column-row")

  open_export_modal(page)

  expect(rows).to_have_count(3)
  expect(rows.nth(0).locator(".export-column-name")).to_have_text("id")
  expect(rows.nth(1).locator(".export-column-name")).to_have_text("name")
  expect(rows.nth(2).locator(".export-column-name")).to_have_text("Serial")


@pytest.mark.e2e
def test_export_modal_starts_empty_without_field_filters(
  page,
  live_server,
  setup_admin,
  create_location,
):
  create_location("HQ")

  page.goto(f"{live_server}/")

  page.locator("#search").fill("Alpha")

  modal = apply_filter(page)

  modal.locator("#filter-location").select_option(label="HQ")
  modal.get_by_role("button", name="Apply").click()

  # A location filter pre-fills; clear it again so no field-bearing filter
  # remains active.
  modal = apply_filter(page)

  modal.locator("#filter-location").select_option("")
  modal.get_by_role("button", name="Apply").click()

  open_export_modal(page)

  expect(page.locator("#export-column-rows .export-column-row")).to_have_count(0)


@pytest.mark.e2e
def test_export_modal_suggests_builtin_and_custom_fields(
  page,
  live_server,
  setup_admin,
  serial_field,
):
  page.goto(f"{live_server}/")

  open_export_modal(page)

  options = page.locator("#export-column-options option")

  values = options.evaluate_all("options => options.map(o => o.value)")

  assert "id" in values
  assert "name" in values
  assert "Serial" in values


@pytest.mark.e2e
def test_export_modal_adds_and_removes_columns(
  page,
  live_server,
  setup_admin,
  serial_field,
):
  page.goto(f"{live_server}/")

  open_export_modal(page)

  rows = page.locator("#export-column-rows .export-column-row")
  column_input = page.locator("#add-export-column")
  column_button = page.locator("#add-export-column-button")

  def datalist_values():
    return page.locator("#export-column-options option").evaluate_all(
      "options => options.map(o => o.value.toLowerCase())"
    )

  column_input.fill("Name")
  column_button.click()

  expect(rows).to_have_count(1)

  # Added columns are removed from the datalist suggestions.
  assert "name" not in datalist_values()

  # Duplicate adds are prevented.
  column_input.fill("name")
  column_button.click()

  expect(rows).to_have_count(1)

  column_input.fill("Serial")
  column_button.click()

  expect(rows).to_have_count(2)

  # Unknown names are rejected with an inline error.
  column_input.fill("Bogus")
  column_button.click()

  expect(page.locator("#add-export-column-error")).to_be_visible()
  expect(rows).to_have_count(2)

  rows.nth(1).locator(".export-column-remove").click()

  expect(rows).to_have_count(1)

  # Removed columns return to the datalist suggestions.
  assert "serial" in datalist_values()

  page.locator("#export-columns-reset").click()

  expect(rows).to_have_count(0)


@pytest.mark.e2e
def test_export_selected_fields_csv(
  page,
  live_server,
  setup_admin,
  create_item,
  serial_field,
  set_item_custom_field,
):
  item = create_item("Alpha Asset")

  set_item_custom_field(item["id"], "Serial", "SN-1")

  page.goto(f"{live_server}/")

  open_export_modal(page)

  rows = page.locator("#export-column-rows .export-column-row")
  column_input = page.locator("#add-export-column")

  column_input.fill("id")
  column_input.press("Enter")

  column_input.fill("Serial")
  column_input.press("Enter")

  with page.expect_download() as download_info:
    page.locator("#export-submit-button").click()

  download = download_info.value
  content = download.path().read_text(encoding="utf-8")

  lines = [line for line in content.strip().splitlines() if line]

  assert lines[0] == "id,Serial"
  assert len(lines) == 2
  assert item["id"] in lines[1]
  assert "SN-1" in lines[1]

  expect(rows).to_have_count(2)


@pytest.mark.e2e
def test_export_without_columns_keeps_all_fields(
  page,
  live_server,
  setup_admin,
  create_item,
  serial_field,
  set_item_custom_field,
):
  item = create_item("Alpha Asset")

  set_item_custom_field(item["id"], "Serial", "SN-1")

  page.goto(f"{live_server}/")

  open_export_modal(page)

  with page.expect_download() as download_info:
    page.locator("#export-submit-button").click()

  content = download_info.value.path().read_text(encoding="utf-8")

  header = content.strip().splitlines()[0]

  assert header == "id,name,description,location,created_at,updated_at,Serial"


@pytest.mark.e2e
def test_export_modal_keeps_current_filters_in_download(
  page,
  live_server,
  setup_admin,
  create_item,
  create_location,
):
  location = create_location("HQ")

  create_item("Alpha Asset", location_id=location["id"])
  create_item("Beta Asset")

  page.goto(f"{live_server}/")

  page.locator("#search").fill("Alpha")

  modal = apply_filter(page)

  modal.locator("#filter-location").select_option(label="HQ")
  modal.get_by_role("button", name="Apply").click()

  open_export_modal(page)

  # Pre-filled columns: id + name + location (from the location filter).
  rows = page.locator("#export-column-rows .export-column-row")

  expect(rows).to_have_count(3)

  with page.expect_download() as download_info:
    page.locator("#export-submit-button").click()

  content = download_info.value.path().read_text(encoding="utf-8")

  lines = [line for line in content.strip().splitlines() if line]

  assert lines[0] == "id,name,location"
  assert len(lines) == 2
  assert "Alpha Asset" in lines[1]
  assert "HQ" in lines[1]

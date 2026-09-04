import pytest
from playwright.sync_api import expect


def open_export_modal(page, live_server):
  page.goto(f"{live_server}/admin?tab=data")

  page.locator("#export-button").click()

  return page.get_by_role("dialog")


def datalist_values(page):
  return page.locator("#export-column-options option").evaluate_all(
    "options => options.map(o => o.value.toLowerCase())"
  )


@pytest.fixture
def serial_field(create_custom_field):
  return create_custom_field("Serial", "text")


@pytest.mark.e2e
def test_export_button_opens_export_modal(page, live_server, setup_admin):
  modal = open_export_modal(page, live_server)

  expect(modal.get_by_role("heading", name="Export CSV")).to_be_visible()
  expect(page.locator("#add-export-column")).to_be_visible()
  expect(page.locator("#export-column-options")).to_be_attached()


@pytest.mark.e2e
def test_export_modal_starts_empty_without_columns(page, live_server, setup_admin):
  open_export_modal(page, live_server)

  expect(page.locator("#export-column-rows .export-column-row")).to_have_count(0)


@pytest.mark.e2e
def test_export_modal_suggests_builtin_and_custom_fields(
  page,
  live_server,
  setup_admin,
  serial_field,
):
  open_export_modal(page, live_server)

  values = datalist_values(page)

  assert "id" in values
  assert "name" in values
  assert "serial" in values


@pytest.mark.e2e
def test_export_modal_adds_and_removes_columns(
  page,
  live_server,
  setup_admin,
  serial_field,
):
  open_export_modal(page, live_server)

  rows = page.locator("#export-column-rows .export-column-row")
  column_input = page.locator("#add-export-column")
  column_button = page.locator("#add-export-column-button")

  column_input.fill("id")
  column_button.click()

  expect(rows).to_have_count(1)
  assert "id" not in datalist_values(page)

  column_input.fill("Serial")
  column_input.press("Enter")

  expect(rows).to_have_count(2)

  # Unknown names are rejected with an inline error.
  column_input.fill("Bogus")
  column_button.click()

  expect(page.locator("#add-export-column-error")).to_be_visible()
  expect(rows).to_have_count(2)

  rows.nth(1).locator(".export-column-remove").click()

  expect(rows).to_have_count(1)
  assert "serial" in datalist_values(page)

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

  open_export_modal(page, live_server)

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

  open_export_modal(page, live_server)

  with page.expect_download() as download_info:
    page.locator("#export-submit-button").click()

  content = download_info.value.path().read_text(encoding="utf-8")

  header = content.strip().splitlines()[0]

  assert header == "id,name,description,location,created_at,updated_at,Serial"
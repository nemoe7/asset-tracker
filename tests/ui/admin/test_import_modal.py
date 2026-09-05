import pytest
from playwright.sync_api import expect


def open_import_modal(page, live_server):
  page.goto(f"{live_server}/admin?tab=data")

  page.locator("#import-button").click()

  return page.get_by_role("dialog")


@pytest.mark.e2e
def test_import_button_opens_import_modal(page, live_server, setup_admin):
  modal = open_import_modal(page, live_server)

  expect(modal.get_by_role("heading", name="Import assets")).to_be_visible()
  expect(page.locator("#import-file")).to_be_visible()
  expect(page.locator("#import-submit-button")).to_be_visible()


@pytest.mark.e2e
def test_import_uploads_csv_and_creates_items(
  page,
  live_server,
  setup_admin,
  tmp_path,
):
  import_file = tmp_path / "items.csv"

  import_file.write_text("name,description\nAlpha Asset,First\n", encoding="utf-8")

  modal = open_import_modal(page, live_server)

  page.locator("#import-file").set_input_files(import_file)
  page.locator("#import-submit-button").click()

  expect(page.locator("#import-status")).to_contain_text("Imported 1 item.")
  expect(modal).not_to_be_visible()


@pytest.mark.e2e
def test_import_missing_name_column_shows_error(
  page,
  live_server,
  setup_admin,
  tmp_path,
):
  import_file = tmp_path / "items.csv"

  import_file.write_text("description\nNo name here\n", encoding="utf-8")

  modal = open_import_modal(page, live_server)

  page.locator("#import-file").set_input_files(import_file)
  page.locator("#import-submit-button").click()

  expect(page.locator("#import-error")).to_be_visible()
  expect(modal).to_be_visible()

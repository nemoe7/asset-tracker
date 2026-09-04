import pytest
from playwright.sync_api import expect


@pytest.mark.e2e
def test_backups_tab_shows_manual_backup_controls(page, live_server, setup_admin):
  page.goto(f"{live_server}/admin?tab=backups")

  panel = page.locator("#tab-backups")

  expect(panel).to_be_visible()
  expect(page.locator("#backup-button")).to_be_visible()


@pytest.mark.e2e
def test_backup_button_downloads_backup_file(page, live_server, setup_admin):
  page.goto(f"{live_server}/admin?tab=backups")

  with page.expect_download() as download_info:
    page.locator("#backup-button").click()

  download = download_info.value

  assert download.suggested_filename.startswith("backup-")
  assert download.suggested_filename.endswith(".db")

  header = download.path().read_bytes()[:16]

  assert header.startswith(b"SQLite format 3\x00")

  expect(page.locator("#backup-status")).to_contain_text("downloaded successfully")

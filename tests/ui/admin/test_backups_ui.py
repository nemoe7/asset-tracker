import pytest
from playwright.sync_api import expect


@pytest.mark.e2e
def test_backups_tab_shows_manual_backup_controls(page, live_server, setup_admin):
  page.goto(f"{live_server}/admin?tab=backups")

  panel = page.locator("#tab-backups")

  expect(panel).to_be_visible()
  expect(page.locator("#backup-button")).to_be_visible()


@pytest.mark.e2e
def test_restore_section_shows_warning_password_and_file_inputs(
  page,
  live_server,
  setup_admin,
):
  page.goto(f"{live_server}/admin?tab=backups")

  expect(page.get_by_text("Restore from backup")).to_be_visible()
  expect(
    page.get_by_text("overwrites", exact=False)
  ).to_contain_text("all current data")
  expect(page.locator("#restore-file")).to_be_visible()
  expect(page.locator("#restore-password")).to_be_visible()
  expect(page.locator("#restore-button")).to_be_visible()


@pytest.mark.e2e
def test_restore_with_wrong_password_shows_error(
  page,
  live_server,
  setup_admin,
  tmp_path,
):
  backup_file = tmp_path / "backup.db"

  backup_file.write_bytes(b"SQLite format 3\x00" + b"\x00" * 64)

  page.goto(f"{live_server}/admin?tab=backups")

  page.locator("#restore-file").set_input_files(backup_file)
  page.locator("#restore-password").fill("wrong-password")

  page.on("dialog", lambda dialog: dialog.accept())

  page.locator("#restore-button").click()

  expect(page.locator("#restore-status")).to_contain_text("Incorrect password")



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

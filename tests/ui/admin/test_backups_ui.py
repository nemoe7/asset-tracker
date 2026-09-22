import pytest
from playwright.sync_api import expect


@pytest.mark.e2e
def test_data_tab_shows_manual_backup_controls(page, live_server, setup_admin):
  page.goto(f"{live_server}/admin?tab=data")

  panel = page.locator("#tab-data")

  expect(panel).to_be_visible()
  expect(page.locator("#backup-button")).to_be_visible()


@pytest.mark.e2e
def test_restore_section_shows_file_input_and_restore_button(
  page,
  live_server,
  setup_admin,
):
  page.goto(f"{live_server}/admin?tab=data")

  expect(page.get_by_text("Restore from backup")).to_be_visible()
  expect(
    page.locator("#tab-data").get_by_text("overwrites", exact=False)
  ).to_contain_text("all current data")
  expect(page.locator("#restore-file")).to_be_visible()
  expect(page.locator("#restore-button")).to_be_visible()

  # The password prompt moved into the confirmation modal.
  expect(page.locator("#restore-confirm-dialog")).to_be_hidden()


@pytest.mark.e2e
def test_restore_opens_password_modal_after_choosing_file(
  page,
  live_server,
  setup_admin,
  tmp_path,
):
  backup_file = tmp_path / "backup.db"

  backup_file.write_bytes(b"SQLite format 3\x00" + b"\x00" * 64)

  page.goto(f"{live_server}/admin?tab=data")

  page.locator("#restore-file").set_input_files(backup_file)
  page.locator("#restore-button").click()

  dialog = page.locator("#restore-confirm-dialog")
  expect(dialog).to_be_visible()
  expect(page.locator("#restore-confirm-password")).to_be_visible()

  # Cancelling closes the modal without restoring.
  page.get_by_role("button", name="Cancel", exact=True).click()

  expect(dialog).to_be_hidden()


@pytest.mark.e2e
def test_restore_with_wrong_password_shows_error(
  page,
  live_server,
  setup_admin,
  tmp_path,
):
  backup_file = tmp_path / "backup.db"

  backup_file.write_bytes(b"SQLite format 3\x00" + b"\x00" * 64)

  page.goto(f"{live_server}/admin?tab=data")

  page.locator("#restore-file").set_input_files(backup_file)
  page.locator("#restore-button").click()

  dialog = page.locator("#restore-confirm-dialog")
  expect(dialog).to_be_visible()

  page.locator("#restore-confirm-password").fill("wrong-password")

  dialog.get_by_role("button", name="Restore backup").click()

  expect(page.locator("#restore-confirm-status")).to_contain_text("Incorrect password")
  expect(dialog).to_be_visible()


@pytest.mark.e2e
def test_backup_button_downloads_backup_file(page, live_server, setup_admin):
  page.goto(f"{live_server}/admin?tab=data")

  with page.expect_download() as download_info:
    page.locator("#backup-button").click()

  download = download_info.value

  assert download.suggested_filename.startswith("backup-")
  assert download.suggested_filename.endswith(".db")

  header = download.path().read_bytes()[:16]

  assert header.startswith(b"SQLite format 3\x00")

  expect(page.locator("#backup-status")).to_contain_text("downloaded successfully")


@pytest.mark.e2e
def test_automatic_backup_section_shows_disabled_default(
  page, live_server, setup_admin
):
  page.goto(f"{live_server}/admin?tab=data")
  expect(page.get_by_role("heading", name="Automatic backup")).to_be_visible()
  expect(page.locator("#backup-schedule-summary")).to_contain_text("Disabled")
  expect(page.locator("#backup-config-edit-button")).to_be_visible()


@pytest.mark.e2e
def test_backup_config_modal_updates_day_selector_visibility(
  page, live_server, setup_admin
):
  page.goto(f"{live_server}/admin?tab=data")

  dialog = page.locator("#backup-config-dialog")
  expect(dialog).to_be_hidden()

  page.locator("#backup-config-edit-button").click()

  expect(dialog).to_be_visible()
  expect(page.locator("#modal-manager")).to_be_visible()

  recurrence = page.locator("#backup-recurrence")
  expect(page.locator("#backup-day-weekly-wrap")).to_be_visible()
  expect(page.locator("#backup-day-monthly-wrap")).to_be_hidden()

  recurrence.select_option("daily")
  expect(page.locator("#backup-day-weekly-wrap")).to_be_hidden()
  expect(page.locator("#backup-day-monthly-wrap")).to_be_hidden()

  recurrence.select_option("monthly")
  expect(page.locator("#backup-day-weekly-wrap")).to_be_hidden()
  expect(page.locator("#backup-day-monthly-wrap")).to_be_visible()

  page.locator("#backup-config-cancel").click()
  expect(dialog).to_be_hidden()


@pytest.mark.e2e
def test_backup_config_save_persists_and_updates_summary(
  page, live_server, setup_admin
):
  page.goto(f"{live_server}/admin?tab=data")
  page.locator("#backup-config-edit-button").click()

  page.locator("#backup-enabled").check()
  page.locator("#backup-recurrence").select_option("monthly")
  page.locator("#backup-day-monthly").select_option("15")
  page.locator("#backup-time").fill("04:30")
  page.locator("#backup-config-save").click()

  expect(page.locator("#backup-config-status")).to_contain_text("saved")
  expect(page.locator("#backup-schedule-summary")).to_contain_text("Enabled")
  expect(page.locator("#backup-schedule-summary")).to_contain_text("day 15")

  page.reload()
  expect(page.locator("#backup-schedule-summary")).to_contain_text("day 15")


@pytest.mark.e2e
def test_backup_config_save_invalid_time_shows_error(
  page, live_server, setup_admin
):
  page.goto(f"{live_server}/admin?tab=data")
  page.locator("#backup-config-edit-button").click()
  page.locator("#backup-recurrence").select_option("daily")
  page.locator("#backup-time").fill("")
  page.locator("#backup-config-save").click()
  expect(page.locator("#backup-config-error")).to_be_visible()

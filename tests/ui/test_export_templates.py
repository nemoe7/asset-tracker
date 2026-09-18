import pytest


@pytest.fixture
def admin_page(live_server, page):
  page.goto(f"{live_server}/auth/setup")

  page.fill("#username", "admin")
  page.fill("#display_name", "Admin")
  page.fill("#password", "password123")
  page.fill("#confirm_password", "password123")
  page.click("button[type=submit]")

  page.wait_for_url(f"{live_server}/")

  return page


def open_export_modal(page, live_server):
  page.goto(f"{live_server}/admin?tab=data")
  page.click("#export-button")
  page.wait_for_selector("#export-template-name:not(.hidden)")


def test_save_and_apply_export_template(admin_page, live_server):
  page = admin_page
  open_export_modal(page, live_server)

  # Save a template with a subset of columns.
  for column in ("Name", "Location"):
    page.fill("#add-export-column", column)
    page.click("#add-export-column-button")

  page.fill("#export-template-name", "My template")
  page.click("#export-template-save-button")

  page.wait_for_selector(
    "#export-template-select option:not([value=''])",
    state="attached",
  )

  label = page.locator("#export-template-select option").nth(1).text_content()
  assert label == "My template"

  # Selecting it enables Apply; applying lands on the export URL.
  page.select_option("#export-template-select", index=1)
  assert page.is_enabled("#export-template-apply-button")

  # /inventory/export returns a CSV attachment, so the browser starts a
  # download instead of navigating; assert on the redirect request.
  with page.expect_request(
    lambda request: "/inventory/export" in request.url
  ) as request_info:
    page.click("#export-template-apply-button")

  assert "fields=" in request_info.value.url

import pytest
from playwright.sync_api import expect


@pytest.fixture
def logged_in(page, live_server, setup_admin):
  # The admin created during /auth/setup is already authenticated,
  # so the session is established by just visiting the page.
  page.goto(f"{live_server}/")


@pytest.mark.e2e
def test_audit_tab_opens_from_tab_bar(page, live_server, logged_in):
  page.goto(f"{live_server}/admin")

  page.locator("#admin-tabs").get_by_role("button", name="Activity").click()

  expect(page.locator("#tab-audit")).to_be_visible()
  expect(page.get_by_role("heading", name="Activity")).to_be_visible()


@pytest.mark.e2e
def test_audit_page_shows_created_item_event(page, live_server, logged_in, create_item):
  create_item("Test Asset")

  page.goto(f"{live_server}/admin?tab=audit")

  # Baseline: the /auth/setup audit event for the admin user.
  expect(page.locator("#audit-rows-desktop tr[data-audit-row]")).to_have_count(2)
  expect(
    page.locator("#audit-rows-desktop").get_by_text("inventory_item")
  ).to_be_visible()
  expect(page.get_by_text("Showing 2 of 2 events")).to_be_visible()
  expect(page.locator("#audit-end")).to_be_visible()


@pytest.mark.e2e
def test_audit_page_infinite_scroll_loads_until_end(
  page, live_server, logged_in, create_item
):
  for index in range(55):
    create_item(f"Asset {index}")

  page.goto(f"{live_server}/admin?tab=audit")

  # 55 item events + the /auth/setup audit event for the admin user.
  expect(page.locator("#audit-rows-desktop tr[data-audit-row]")).to_have_count(50)
  expect(page.get_by_text("Showing 50 of 56 events")).to_be_visible()
  expect(page.locator("#audit-sentinel")).to_be_attached()

  page.locator("#audit-sentinel").scroll_into_view_if_needed()

  expect(page.locator("#audit-rows-desktop tr[data-audit-row]")).to_have_count(56)
  expect(page.get_by_text("Showing 56 of 56 events")).to_be_visible()
  expect(page.get_by_text("End of activity · 56 events")).to_be_visible()
  expect(page.locator("#audit-sentinel")).to_have_count(0)


@pytest.mark.e2e
def test_audit_page_filter_narrows_events(
  page,
  live_server,
  logged_in,
  create_item,
  create_location,
):
  create_item("Test Asset")
  create_location("Warehouse")

  page.goto(f"{live_server}/admin?tab=audit")

  # Item + location + the /auth/setup audit event for the admin user.
  expect(page.locator("#audit-rows-desktop tr[data-audit-row]")).to_have_count(3)

  page.locator("#audit-filter-button").click()

  form = page.locator("#audit-filter-form")
  expect(form).to_be_visible()

  form.locator("#audit-filter-entity-type").select_option("location")
  form.get_by_role("button", name="Apply").click()

  page.wait_for_url("**/admin?tab=audit&entity_type=location*")

  expect(page.locator("#audit-rows-desktop tr[data-audit-row]")).to_have_count(1)
  expect(page.get_by_text("Type: location")).to_be_visible()


@pytest.mark.e2e
def test_audit_page_removes_filter_via_chip(page, live_server, logged_in):
  page.goto(f"{live_server}/admin?tab=audit&entity_type=location")

  chip = page.locator("[data-filter-chip]")
  expect(chip).to_be_visible()
  expect(page.get_by_text("Type: location")).to_be_visible()

  chip.click()

  page.wait_for_url(f"{live_server}/admin?tab=audit")

  expect(page.locator("[data-filter-chip]")).to_have_count(0)
  expect(page.locator("#audit-rows-desktop tr[data-audit-row]")).to_have_count(1)


@pytest.mark.e2e
def test_audit_filter_modal_closes(page, live_server, logged_in):
  page.goto(f"{live_server}/admin?tab=audit")

  page.locator("#audit-filter-button").click()

  form = page.locator("#audit-filter-form")
  expect(form).to_be_visible()

  page.keyboard.press("Escape")

  expect(form).to_be_hidden()


@pytest.mark.e2e
def test_audit_page_mobile_cards_render(page, live_server, logged_in, create_item):
  create_item("Test Asset")

  page.set_viewport_size({"width": 375, "height": 667})
  page.goto(f"{live_server}/admin?tab=audit")

  expect(page.locator("#audit-rows-mobile [data-audit-card]")).to_have_count(2)
  expect(
    page.locator("#audit-rows-mobile").get_by_text("inventory_item")
  ).to_be_visible()
  expect(page.get_by_role("table")).to_be_hidden()


@pytest.mark.e2e
def test_audit_timestamps_use_browser_local_time(
  page, live_server, logged_in, create_item
):
  create_item("Test Asset")

  page.goto(f"{live_server}/admin?tab=audit")

  cell = page.locator("#audit-rows-desktop [data-audit-timestamp]").first
  expect(cell).to_be_visible()

  utc = cell.get_attribute("data-utc")
  assert utc is not None
  assert len(utc) == 19  # YYYY-MM-DD HH:MM:SS

  # The rendered text must equal the browser's own local rendering of the stored UTC.
  expected = page.evaluate(
    "(utc) => new Date(utc.replace(' ', 'T') + 'Z').toLocaleString()",
    utc,
  )
  assert cell.inner_text().strip() == expected

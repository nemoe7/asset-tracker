import pytest
from playwright.sync_api import expect


@pytest.fixture
def logged_in(page, live_server, setup_admin):
  # The admin created during /auth/setup is already authenticated,
  # so the session is established by just visiting the page.
  page.goto(f"{live_server}/")


@pytest.mark.e2e
def test_audit_menu_link_opens_audit_page(page, live_server, logged_in):
  menu = page.locator("details")
  menu.locator("summary").click()

  page.get_by_role("link", name="Activity", exact=True).click()

  page.wait_for_url(f"{live_server}/admin/audit")

  expect(page.get_by_role("heading", name="Activity")).to_be_visible()


@pytest.mark.e2e
def test_audit_page_shows_created_item_event(page, live_server, logged_in, create_item):
  create_item("Test Asset")

  page.goto(f"{live_server}/admin/audit")

  # Baseline: the /auth/setup audit event for the admin user.
  expect(page.locator("#audit-rows-desktop tr[data-audit-row]")).to_have_count(2)
  expect(page.locator("#audit-rows-desktop").get_by_text("inventory_item")).to_be_visible()
  expect(page.get_by_text("Showing 2 of 2 events")).to_be_visible()
  expect(page.locator("#audit-end")).to_be_visible()


@pytest.mark.e2e
def test_audit_page_infinite_scroll_loads_until_end(page, live_server, logged_in, create_item):
  for index in range(55):
    create_item(f"Asset {index}")

  page.goto(f"{live_server}/admin/audit")

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

  page.goto(f"{live_server}/admin/audit")

  # Item + location + the /auth/setup audit event for the admin user.
  expect(page.locator("#audit-rows-desktop tr[data-audit-row]")).to_have_count(3)

  page.locator("#audit-entity-type").select_option("location")
  page.get_by_role("button", name="Apply").click()

  page.wait_for_url(f"**/admin/audit*entity_type=location*")

  expect(page.locator("#audit-rows-desktop tr[data-audit-row]")).to_have_count(1)
  expect(page.locator("#audit-rows-desktop").get_by_text("location", exact=True)).to_be_visible()


@pytest.mark.e2e
def test_audit_page_mobile_cards_render(page, live_server, logged_in, create_item):
  create_item("Test Asset")

  page.set_viewport_size({"width": 375, "height": 667})
  page.goto(f"{live_server}/admin/audit")

  expect(page.locator("#audit-rows-mobile [data-audit-card]")).to_have_count(2)
  expect(page.locator("#audit-rows-mobile").get_by_text("inventory_item")).to_be_visible()
  expect(page.get_by_role("table")).to_be_hidden()

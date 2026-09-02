import pytest
from playwright.sync_api import expect


@pytest.fixture
def logged_in(page, live_server, setup_admin):
  # The admin created during /auth/setup is already authenticated,
  # so the session is established by just visiting the page.
  page.goto(f"{live_server}/")


@pytest.mark.e2e
def test_menu_contains_admin_panel_link(page, live_server, logged_in):
  menu = page.locator("details")
  menu.locator("summary").click()

  expect(
    page.get_by_role("link", name="Admin Panel", exact=True)
  ).to_be_visible()

  # The individual tab links are no longer in the menu.
  expect(page.get_by_role("link", name="Locations", exact=True)).to_have_count(0)
  expect(page.get_by_role("link", name="Custom fields", exact=True)).to_have_count(0)


@pytest.mark.e2e
def test_menu_admin_panel_opens_admin_page(page, live_server, logged_in):
  menu = page.locator("details")
  menu.locator("summary").click()

  page.get_by_role("link", name="Admin Panel", exact=True).click()

  page.wait_for_url(f"{live_server}/admin")

  expect(page.get_by_role("heading", name="Add location")).to_be_visible()


@pytest.mark.e2e
def test_admin_page_creates_location(page, live_server, logged_in):
  page.goto(f"{live_server}/admin?tab=locations")

  page.locator("#add-location-name").fill("Warehouse")
  page.locator("#add-location-description").fill("Main storage area")

  page.get_by_role("button", name="Add location").click()

  page.wait_for_url(f"{live_server}/admin?tab=locations")

  expect(page.get_by_text("Warehouse", exact=True)).to_be_visible()
  expect(page.get_by_text("Main storage area")).to_be_visible()


@pytest.mark.e2e
def test_admin_page_creates_custom_field(page, live_server, logged_in):
  page.goto(f"{live_server}/admin?tab=custom-fields")

  page.locator("#add-field-name").fill("Serial Number")
  page.locator("#add-field-type").select_option("text")

  page.get_by_role("button", name="Add field").click()

  page.wait_for_url(f"{live_server}/admin?tab=custom-fields")

  expect(page.get_by_text("Serial Number")).to_be_visible()
  expect(page.get_by_text("text", exact=True)).to_be_visible()


@pytest.mark.e2e
def test_admin_page_tabs_switch_client_side(page, live_server, logged_in):
  page.goto(f"{live_server}/admin")

  expect(page.locator("#tab-locations")).to_be_visible()
  expect(page.locator("#tab-custom-fields")).to_be_hidden()

  page.locator("[data-tab-button='custom-fields']").click()

  expect(page.locator("#tab-locations")).to_be_hidden()
  expect(page.locator("#tab-custom-fields")).to_be_visible()

  page.locator("[data-tab-button='locations']").click()

  expect(page.locator("#tab-locations")).to_be_visible()
  expect(page.locator("#tab-custom-fields")).to_be_hidden()


@pytest.mark.e2e
def test_admin_page_has_hamburger_menu(page, live_server, logged_in):
  page.goto(f"{live_server}/admin")

  menu = page.locator("details")
  expect(menu).to_be_visible()
  expect(menu.get_by_text("@test_admin", exact=True)).to_be_hidden()

  menu.locator("summary").click()

  expect(menu.get_by_text("@test_admin", exact=True)).to_be_visible()
  expect(page.get_by_role("link", name="Admin Panel", exact=True)).to_be_visible()
  expect(page.get_by_role("button", name="Log out")).to_be_visible()


@pytest.mark.e2e
def test_admin_page_delete_location_requires_confirmation(
  page,
  live_server,
  logged_in,
  create_location,
):
  create_location("Warehouse")

  page.goto(f"{live_server}/admin?tab=locations")

  page.locator("[data-delete-location] button[type='submit']").click()

  dialog = page.locator("#delete-location-dialog")
  expect(dialog).to_be_visible()

  page.locator("#cancel-delete-location").click()

  expect(dialog).to_be_hidden()
  expect(page.get_by_text("Warehouse", exact=True)).to_be_visible()

  page.locator("[data-delete-location] button[type='submit']").click()
  expect(dialog).to_be_visible()
  page.locator("#confirm-delete-location").click()

  expect(page.get_by_text("Warehouse", exact=True)).to_be_hidden()

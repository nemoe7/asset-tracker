import pytest
from playwright.sync_api import expect


@pytest.mark.e2e
def test_main_page_loads(page, live_server):
  page.goto(f"{live_server}/")

  expect(page.locator("#search-form")).to_be_visible()
  expect(page.locator("#filter-item-button")).to_be_visible()
  expect(page.locator("#add-item-button")).to_be_visible()
  expect(page.locator("#inventory-items")).to_be_visible()
  expect(page.get_by_role("button", name="Log out")).to_be_visible()


@pytest.mark.e2e
def test_main_page_shows_empty_inventory(page, live_server):
  page.goto(f"{live_server}/")

  expect(page.get_by_role("heading", name="No inventory items")).to_be_visible()


@pytest.mark.e2e
def test_main_page_search_has_correct_input(page, live_server):
  page.goto(f"{live_server}/")

  search = page.locator("#search")

  expect(search).to_be_visible()
  expect(search).to_have_attribute("name", "search")
  expect(search).to_have_attribute("type", "search")
  expect(search).to_have_attribute("placeholder", "Search inventory...")


@pytest.mark.e2e
def test_main_page_filter_modal_opens_and_closes(page, live_server):
  page.goto(f"{live_server}/")

  page.locator("#filter-item-button").click()

  modal = page.locator("#filter-item-modal")
  expect(modal).to_be_visible()

  expect(modal.get_by_role("heading", name="Filter & Sort")).to_be_visible()

  expect(page.locator("#filter-location")).to_be_visible()
  expect(page.locator("#filter-sort-by")).to_be_visible()
  expect(page.get_by_text("Ascending", exact=True)).to_be_visible()
  expect(page.get_by_text("Descending", exact=True)).to_be_visible()

  modal.locator(".modal-close").click()

  expect(modal).to_be_hidden()


@pytest.mark.e2e
def test_main_page_filter_modal_can_be_cleared(page, live_server):
  page.goto(f"{live_server}/")

  page.locator("#filter-item-button").click()

  modal = page.locator("#filter-item-modal")
  expect(modal).to_be_visible()

  page.locator("#clear-filter-item").click()

  expect(modal).to_be_hidden()


@pytest.mark.e2e
def test_main_page_add_item_modal_opens_and_closes(page, live_server):
  page.goto(f"{live_server}/")

  page.locator("#add-item-button").click()

  modal = page.locator("#add-item-modal")
  expect(modal).to_be_visible()

  expect(modal.get_by_role("heading", name="Add item")).to_be_visible()

  expect(page.locator("#item-name")).to_be_visible()
  expect(page.locator("#item-location")).to_be_visible()

  modal.locator(".modal-close").click()

  expect(modal).to_be_hidden()


@pytest.mark.e2e
def test_main_page_add_item_modal_can_be_cancelled(page, live_server):
  page.goto(f"{live_server}/")

  page.locator("#add-item-button").click()

  modal = page.locator("#add-item-modal")
  expect(modal).to_be_visible()

  page.locator("#item-name").fill("Test Asset")
  modal.locator(".modal-close").click()

  expect(modal).to_be_hidden()


@pytest.mark.e2e
def test_main_page_edit_modal_starts_hidden(page, live_server):
  page.goto(f"{live_server}/")

  expect(page.locator("#edit-item-modal")).to_be_hidden()


@pytest.mark.e2e
def test_main_page_logout(page, live_server):
  page.goto(f"{live_server}/")

  page.get_by_role("button", name="Log out").click()

  page.wait_for_url(f"{live_server}/auth/login")

  expect(page.get_by_role("button", name="Log in")).to_be_visible()


@pytest.mark.e2e
def test_main_page_requires_authentication(page, live_server):
  page.goto(f"{live_server}/")

  page.get_by_role("button", name="Log out").click()
  page.wait_for_url(f"{live_server}/auth/login")

  page.goto(f"{live_server}/")

  page.wait_for_url(f"{live_server}/auth/login")

  expect(page.get_by_role("button", name="Log in")).to_be_visible()


@pytest.mark.e2e
def test_add_item_modal_requires_name(page, live_server):
  page.goto(f"{live_server}/")

  page.locator("#add-item-button").click()

  modal = page.locator("#add-item-modal")
  expect(modal).to_be_visible()

  page.get_by_role("button", name="Add item", exact=True).last.click()

  expect(modal).to_be_visible()
  expect(page.locator("#item-name")).to_have_attribute("required", "")


@pytest.mark.e2e
def test_add_item_modal_shows_locations(
  page,
  live_server,
  create_location,
):
  location_a = create_location("Location A")
  location_b = create_location("Location B")

  page.goto(f"{live_server}/")
  page.locator("#add-item-button").click()

  location_select = page.locator("#item-location")

  expect(location_select).to_be_visible()

  expect(
    location_select.locator(f'option[value="{location_a["id"]}"]')
  ).to_be_attached()

  expect(
    location_select.locator(f'option[value="{location_b["id"]}"]')
  ).to_be_attached()

  expect(location_select.locator('option[value=""]')).to_have_count(1)


@pytest.mark.e2e
def test_main_page_desktop_header_actions(page, live_server, setup_admin):
  page.set_viewport_size({"width": 1280, "height": 720})
  page.goto(f"{live_server}/")

  expect(
    page.locator("span").filter(has_text=f"@{setup_admin['username']}")
  ).to_be_visible()
  expect(page.locator("#qr-scanner-button")).to_be_visible()
  expect(page.locator("form").first).to_be_visible()

  expect(page.locator("details")).to_be_hidden()


@pytest.mark.e2e
def test_main_page_mobile_header_actions(
  page,
  live_server,
  setup_admin,
):
  page.set_viewport_size({"width": 375, "height": 667})
  page.goto(f"{live_server}/")

  # Scan remains directly available.
  expect(page.locator("#qr-scanner-button")).to_be_visible()

  # Desktop actions are hidden.
  expect(page.get_by_text("admin", exact=True)).to_be_hidden()
  expect(page.get_by_role("link", name="Users")).to_be_hidden()

  # Hamburger is visible.
  menu = page.locator("details")
  expect(menu).to_be_visible()

  # Menu contents are initially hidden.
  expect(menu.get_by_text(f"@{setup_admin['username']}", exact=True)).to_be_hidden()
  expect(menu.locator('form[action="/auth/logout"]')).to_be_hidden()


@pytest.mark.e2e
def test_main_page_mobile_menu_contains_user_actions(
  page,
  live_server,
  setup_admin,
):
  page.set_viewport_size({"width": 375, "height": 667})
  page.goto(f"{live_server}/")

  menu = page.locator("details")

  menu.locator("summary").click()

  expect(menu.get_by_text(f"@{setup_admin['username']}", exact=True)).to_be_visible()
  expect(menu.locator('form[action="/auth/logout"]')).to_be_visible()

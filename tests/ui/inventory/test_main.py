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

  page.locator("#close-filter-item-modal").click()

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

  page.locator("#close-add-item-modal").click()

  expect(modal).to_be_hidden()


@pytest.mark.e2e
def test_main_page_add_item_modal_can_be_cancelled(page, live_server):
  page.goto(f"{live_server}/")

  page.locator("#add-item-button").click()

  modal = page.locator("#add-item-modal")
  expect(modal).to_be_visible()

  page.locator("#item-name").fill("Test Asset")
  page.locator("#cancel-add-item").click()

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

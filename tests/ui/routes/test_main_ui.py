import pytest
from playwright.sync_api import expect


@pytest.fixture(autouse=True)
def e2e_admin(
  page,
  live_server,
  gen_password,
):
  page.goto(f"{live_server}/auth/setup")

  page.locator("#username").fill("test_admin")
  page.locator("#display_name").fill("Test Admin")
  password = gen_password("test_admin")
  page.locator("#password").fill(password)
  page.locator("#confirm_password").fill(password)
  page.locator("button[type='submit']").click()


@pytest.fixture
def e2e_add_item(page, live_server):
  def create(name, location_id=None):
    page.goto(f"{live_server}/")

    page.locator("#add-item-button").click()

    page.locator("#item-name").fill(name)

    if location_id is not None:
      page.locator("#location_id").fill(str(location_id))

    page.locator("#add-item-modal").get_by_role("button", name="Add item").click()

  return create


@pytest.mark.e2e
def test_main_page_loads(page, live_server):
  page.goto(f"{live_server}/")

  assert page.locator("#search-form").is_visible()
  assert page.locator("#filter-item-button").is_visible()
  assert page.locator("#add-item-button").is_visible()
  assert page.locator("#inventory-items").is_visible()
  assert page.get_by_role("button", name="Log out").is_visible()


@pytest.mark.e2e
def test_main_page_shows_empty_inventory(page, live_server):
  page.goto(f"{live_server}/")

  assert page.get_by_role("heading", name="No inventory items").is_visible()


@pytest.mark.e2e
def test_main_page_can_search_inventory(page, live_server, e2e_add_item):
  e2e_add_item("Test Asset")
  page.goto(f"{live_server}/")

  search = page.locator("#search-form input")
  search.fill("Test Asset")

  expect(page.get_by_role("cell", name="Test Asset")).to_be_visible()


@pytest.mark.e2e
def test_main_page_can_open_filter_modal(page, live_server):
  page.goto(f"{live_server}/")

  page.locator("#filter-item-button").click()

  assert page.get_by_role("dialog").is_visible()


@pytest.mark.e2e
def test_main_page_can_open_add_item_modal(page, live_server):
  page.goto(f"{live_server}/")

  page.locator("#add-item-button").click()

  assert page.get_by_role("dialog").is_visible()


@pytest.mark.e2e
def test_main_page_can_log_out(page, live_server):
  page.goto(f"{live_server}/")

  page.get_by_role("button", name="Log out").click()

  page.wait_for_url(f"{live_server}/auth/login")

  assert page.get_by_role("button", name="Log in")

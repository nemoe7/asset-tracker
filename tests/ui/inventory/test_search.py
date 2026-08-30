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
  page.wait_for_url(f"{live_server}/")


@pytest.fixture
def add_item(page, live_server):
  def create(name, location_id=None):
    page.locator("#add-item-button").click()

    modal = page.locator("#add-item-modal")
    expect(modal).to_be_visible()

    page.locator("#item-name").fill(name)

    if location_id is not None:
      page.locator("#item-location").select_option(str(location_id))

    modal.get_by_role("button", name="Add item").click()

    expect(modal).to_be_hidden()

  return create


@pytest.mark.e2e
def test_inventory_can_create_item(page, live_server, add_item):
  page.goto(f"{live_server}/")

  add_item("Test Asset")

  expect(page.get_by_role("cell", name="Test Asset")).to_be_visible()


@pytest.mark.e2e
def test_inventory_search_finds_item(page, live_server, add_item):
  page.goto(f"{live_server}/")

  add_item("Test Asset")

  search = page.locator("#search")
  search.fill("Test Asset")

  expect(page.get_by_role("cell", name="Test Asset")).to_be_visible()


@pytest.mark.e2e
def test_inventory_search_hides_non_matching_items(
  page,
  live_server,
  add_item,
):
  page.goto(f"{live_server}/")

  add_item("Test Asset")
  add_item("Another Asset")

  search = page.locator("#search")
  search.fill("Test Asset")

  expect(page.get_by_role("cell", name="Test Asset")).to_be_visible()
  expect(page.get_by_role("cell", name="Another Asset")).to_be_hidden()


@pytest.mark.e2e
def test_inventory_search_shows_no_results(
  page,
  live_server,
  add_item,
):
  page.goto(f"{live_server}/")

  add_item("Test Asset")

  page.locator("#search").fill("Does Not Exist")

  expect(page.get_by_role("heading", name="No inventory items")).to_be_visible()


@pytest.mark.e2e
def test_inventory_search_can_be_cleared(
  page,
  live_server,
  add_item,
):
  page.goto(f"{live_server}/")

  add_item("Test Asset")
  add_item("Another Asset")

  search = page.locator("#search")

  search.fill("Test Asset")

  expect(page.get_by_role("cell", name="Test Asset")).to_be_visible()
  expect(page.get_by_role("cell", name="Another Asset")).to_be_hidden()

  search.fill("")

  expect(page.get_by_role("cell", name="Test Asset")).to_be_visible()
  expect(page.get_by_role("cell", name="Another Asset")).to_be_visible()


@pytest.mark.e2e
def test_inventory_search_is_case_insensitive(
  page,
  live_server,
  add_item,
):
  page.goto(f"{live_server}/")

  add_item("Test Asset")

  page.locator("#search").fill("test asset")

  expect(page.get_by_role("cell", name="Test Asset")).to_be_visible()


@pytest.mark.e2e
def test_inventory_search_matches_partial_name(
  page,
  live_server,
  add_item,
):
  page.goto(f"{live_server}/")

  add_item("Test Asset")

  page.locator("#search").fill("Test")

  expect(page.get_by_role("cell", name="Test Asset")).to_be_visible()


@pytest.mark.e2e
def test_inventory_search_updates_without_page_reload(
  page,
  live_server,
  add_item,
):
  page.goto(f"{live_server}/")

  add_item("Test Asset")

  initial_url = page.url

  page.locator("#search").fill("Test Asset")

  expect(page.get_by_role("cell", name="Test Asset")).to_be_visible()
  assert page.url == initial_url


@pytest.mark.e2e
def test_inventory_search_preserves_multiple_matching_items(
  page,
  live_server,
  add_item,
):
  page.goto(f"{live_server}/")

  add_item("Test Asset")
  add_item("Test Printer")
  add_item("Other Asset")

  page.locator("#search").fill("Test")

  expect(page.get_by_role("cell", name="Test Asset")).to_be_visible()
  expect(page.get_by_role("cell", name="Test Printer")).to_be_visible()
  expect(page.get_by_role("cell", name="Other Asset")).to_be_hidden()


@pytest.mark.e2e
def test_inventory_search_trims_whitespace(
  page,
  live_server,
  add_item,
):
  page.goto(f"{live_server}/")

  add_item("Test Asset")

  page.locator("#search").fill("  Test Asset  ")

  expect(page.get_by_role("cell", name="Test Asset")).to_be_visible()


@pytest.mark.e2e
def test_inventory_search_with_empty_inventory(
  page,
  live_server,
):
  page.goto(f"{live_server}/")

  page.locator("#search").fill("Test Asset")

  expect(page.get_by_role("heading", name="No inventory items")).to_be_visible()

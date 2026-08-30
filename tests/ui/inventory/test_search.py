import pytest
from playwright.sync_api import expect


@pytest.mark.e2e
def test_inventory_can_create_item(
  page,
  live_server,
  create_item,
):
  create_item("Test Asset")

  page.goto(f"{live_server}/")

  expect(page.get_by_role("cell", name="Test Asset")).to_be_visible()


@pytest.mark.e2e
def test_inventory_search_finds_item(
  page,
  live_server,
  create_item,
):
  create_item("Test Asset")

  page.goto(f"{live_server}/")

  search = page.locator("#search")
  search.fill("Test Asset")

  expect(page.get_by_role("cell", name="Test Asset")).to_be_visible()


@pytest.mark.e2e
def test_inventory_search_hides_non_matching_items(
  page,
  live_server,
  create_item,
):
  create_item("Test Asset")
  create_item("Another Asset")

  page.goto(f"{live_server}/")

  search = page.locator("#search")
  search.fill("Test Asset")

  expect(page.get_by_role("cell", name="Test Asset")).to_be_visible()
  expect(page.get_by_role("cell", name="Another Asset")).to_be_hidden()


@pytest.mark.e2e
def test_inventory_search_shows_no_results(
  page,
  live_server,
  create_item,
):
  create_item("Test Asset")

  page.goto(f"{live_server}/")

  page.locator("#search").fill("Does Not Exist")

  expect(page.get_by_role("heading", name="No inventory items")).to_be_visible()


@pytest.mark.e2e
def test_inventory_search_can_be_cleared(
  page,
  live_server,
  create_item,
):
  create_item("Test Asset")
  create_item("Another Asset")

  page.goto(f"{live_server}/")

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
  create_item,
):
  page.goto(f"{live_server}/")

  create_item("Test Asset")

  page.locator("#search").fill("test asset")

  expect(page.get_by_role("cell", name="Test Asset")).to_be_visible()


@pytest.mark.e2e
def test_inventory_search_matches_partial_name(
  page,
  live_server,
  create_item,
):
  create_item("Test Asset")

  page.goto(f"{live_server}/")

  page.locator("#search").fill("Test")

  expect(page.get_by_role("cell", name="Test Asset")).to_be_visible()


@pytest.mark.e2e
def test_inventory_search_updates_without_page_reload(
  page,
  live_server,
  create_item,
):
  create_item("Test Asset")

  page.goto(f"{live_server}/")

  initial_url = page.url

  page.locator("#search").fill("Test Asset")

  expect(page.get_by_role("cell", name="Test Asset")).to_be_visible()
  assert page.url == initial_url


@pytest.mark.e2e
def test_inventory_search_preserves_multiple_matching_items(
  page,
  live_server,
  create_item,
):
  create_item("Test Asset")
  create_item("Test Printer")
  create_item("Other Asset")

  page.goto(f"{live_server}/")

  page.locator("#search").fill("Test")

  expect(page.get_by_role("cell", name="Test Asset")).to_be_visible()
  expect(page.get_by_role("cell", name="Test Printer")).to_be_visible()
  expect(page.get_by_role("cell", name="Other Asset")).to_be_hidden()


@pytest.mark.e2e
def test_inventory_search_trims_whitespace(
  page,
  live_server,
  create_item,
):
  create_item("Test Asset")

  page.goto(f"{live_server}/")

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

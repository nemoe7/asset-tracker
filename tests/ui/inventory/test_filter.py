import pytest
from playwright.sync_api import expect


@pytest.mark.e2e
def test_filter_modal_opens(page, live_server):
  page.goto(f"{live_server}/")

  page.locator("#filter-item-button").click()

  expect(page.get_by_role("dialog")).to_be_visible()
  expect(page.get_by_role("heading", name="Filter & Sort")).to_be_visible()


@pytest.mark.e2e
def test_filter_modal_has_default_values(page, live_server):
  page.goto(f"{live_server}/")
  page.locator("#filter-item-button").click()

  expect(page.get_by_role("checkbox", name="Include Archived")).not_to_be_checked()

  sort_by = page.get_by_role("combobox", name="Sort by")
  expect(sort_by).to_have_value("name")

  expect(page.get_by_role("radio", name="Ascending")).to_be_checked()
  expect(page.get_by_role("radio", name="Descending")).not_to_be_checked()


@pytest.mark.e2e
def test_filter_modal_can_close(page, live_server):
  page.goto(f"{live_server}/")

  page.locator("#filter-item-button").click()
  page.get_by_role("button", name="Close").click()

  expect(page.get_by_role("dialog")).to_be_hidden()


@pytest.mark.e2e
def test_filter_can_select_location(
  page,
  live_server,
  create_location,
):
  location = create_location("Test Location")

  page.goto(f"{live_server}/")
  page.locator("#filter-item-button").click()

  location_filter = page.get_by_role("combobox").first

  expect(location_filter.locator(f'option[value="{location["id"]}"]')).to_have_count(1)

  location_filter.select_option(str(location["id"]))

  expect(location_filter).to_have_value(str(location["id"]))


@pytest.mark.e2e
def test_filter_can_select_no_location(page, live_server):
  page.goto(f"{live_server}/")
  page.locator("#filter-item-button").click()

  location_filter = page.get_by_role("combobox").first
  location_filter.select_option("__none__")

  expect(location_filter).to_have_value("__none__")


@pytest.mark.e2e
def test_filter_can_select_descending_order(page, live_server):
  page.goto(f"{live_server}/")
  page.locator("#filter-item-button").click()

  page.get_by_role("radio", name="Descending").check()

  expect(page.get_by_role("radio", name="Descending")).to_be_checked()
  expect(page.get_by_role("radio", name="Ascending")).not_to_be_checked()


@pytest.mark.e2e
def test_filter_applies_location(
  page,
  live_server,
  create_location,
  create_item,
):
  location_a = create_location("Location A")
  location_b = create_location("Location B")

  create_item("Asset A", location_a["id"])
  create_item("Asset B", location_b["id"])

  page.goto(f"{live_server}/")
  page.locator("#filter-item-button").click()

  location_filter = page.get_by_role("combobox").first
  location_filter.select_option(str(location_a["id"]))

  page.get_by_role("button", name="Apply").click()

  asset_a = page.get_by_role("row").filter(has_text="Asset A")
  asset_b = page.get_by_role("row").filter(has_text="Asset B")

  expect(asset_a).to_be_visible()
  expect(asset_b).to_be_hidden()


@pytest.mark.e2e
def test_filter_applies_no_location(
  page,
  live_server,
  create_location,
  create_item,
):
  location = create_location("Test Location")

  create_item("Asset With Location", location["id"])
  create_item("Asset Without Location")

  page.goto(f"{live_server}/")
  page.locator("#filter-item-button").click()

  location_filter = page.get_by_role("combobox").first
  location_filter.select_option("__none__")

  page.get_by_role("button", name="Apply").click()

  asset_without_location = page.get_by_role("row").filter(
    has_text="Asset Without Location",
  )

  asset_with_location = page.get_by_role("row").filter(
    has_text="Asset With Location",
  )

  expect(asset_without_location).to_be_visible()
  expect(asset_with_location).to_be_hidden()


@pytest.mark.e2e
def test_filter_applies_descending_sort(
  page,
  live_server,
  create_item,
):
  create_item("Asset A")
  create_item("Asset B")
  create_item("Asset C")

  page.goto(f"{live_server}/")
  page.locator("#filter-item-button").click()

  page.get_by_role("radio", name="Descending").check()
  page.get_by_role("button", name="Apply").click()

  items = page.locator("#inventory-items article")

  expect(items).to_have_count(3)
  expect(items.nth(0)).to_contain_text("Asset C")
  expect(items.nth(1)).to_contain_text("Asset B")
  expect(items.nth(2)).to_contain_text("Asset A")


@pytest.mark.e2e
def test_filter_can_include_archived(page, live_server):
  page.goto(f"{live_server}/")
  page.locator("#filter-item-button").click()

  checkbox = page.get_by_role("checkbox", name="Include Archived")
  checkbox.check()

  expect(checkbox).to_be_checked()


@pytest.mark.e2e
def test_filter_clear_restores_defaults(page, live_server):
  page.goto(f"{live_server}/")
  page.locator("#filter-item-button").click()

  page.get_by_role("radio", name="Descending").check()
  page.get_by_role("checkbox", name="Include Archived").check()

  page.get_by_role("button", name="Clear").click()

  page.locator("#filter-item-button").click()

  expect(page.get_by_role("checkbox", name="Include Archived")).not_to_be_checked()

  expect(page.get_by_role("radio", name="Ascending")).to_be_checked()

  expect(page.get_by_role("radio", name="Descending")).not_to_be_checked()

  expect(page.get_by_role("combobox", name="Sort by")).to_have_value("name")


@pytest.mark.e2e
def test_filter_returns_no_results_when_nothing_matches(
  page,
  live_server,
  create_location,
  create_item,
):
  location = create_location("Test Location")
  create_item("Test Asset", location["id"])

  page.goto(f"{live_server}/")
  page.locator("#filter-item-button").click()

  location_filter = page.get_by_role("combobox").first
  location_filter.select_option("__none__")

  page.get_by_role("button", name="Apply").click()

  expect(page.get_by_role("heading", name="No inventory items")).to_be_visible()

import pytest
from playwright.sync_api import expect


@pytest.fixture(autouse=True)
def mobile_viewport(page):
  # The mobile experience is viewport-driven CSS; 375x667 shows the
  # mobile cards and the scan button the same way qr_scanner tests do.
  page.set_viewport_size({"width": 375, "height": 667})

  yield


def mobile_card(page, item_id):
  # Below md width the desktop table is hidden and assets render as
  # clickable article cards (fragment.jinja).
  return page.locator(f'article.view-item[data-item-id="{item_id}"]')


@pytest.mark.e2e
def test_mobile_inventory_shows_mobile_controls(page, live_server):
  page.goto(f"{live_server}/")

  expect(page.locator("#search-form")).to_be_visible()
  expect(page.locator("#qr-scanner-button")).to_be_visible()
  expect(page.locator("#add-item-button")).to_be_visible()
  expect(page.locator("#inventory-items")).to_be_visible()


@pytest.mark.e2e
def test_mobile_list_shows_asset_card(page, live_server, create_item):
  item = create_item("Mobile Asset")

  page.goto(f"{live_server}/")

  expect(mobile_card(page, item["id"])).to_be_visible()


@pytest.mark.e2e
def test_mobile_asset_card_opens_view_modal(page, live_server, create_item):
  item = create_item("Mobile Modal Asset")

  page.goto(f"{live_server}/")

  mobile_card(page, item["id"]).click()

  expect(page.locator("#view-item-modal")).to_be_visible()
  expect(page.locator("#view-item-name")).to_have_text("Mobile Modal Asset")


@pytest.mark.e2e
def test_mobile_search_finds_asset(page, live_server, create_item):
  item = create_item("Findable Mobile Asset")

  create_item("Other Asset")

  page.goto(f"{live_server}/")

  page.locator("#search").fill("Findable Mobile")

  expect(mobile_card(page, item["id"])).to_be_visible()

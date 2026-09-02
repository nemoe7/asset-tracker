import pytest
from playwright.sync_api import expect


@pytest.mark.e2e
def test_setup_creates_first_admin(
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

  assert page.get_by_role("alert").is_hidden()

  page.wait_for_url("**/")

  assert page.locator("#search-form").is_visible()
  assert page.locator("#filter-item-button").is_visible()
  assert page.locator("#add-item-button").is_visible()
  assert page.locator("#inventory-items").is_visible()

  menu = page.locator("details")
  menu.locator("summary").click()

  expect(page.get_by_role("button", name="Log out")).to_be_visible()

import pytest
from playwright.sync_api import expect


@pytest.fixture(autouse=True)
def e2e_admin(
  page,
  live_server,
  gen_password,
):
  admin = {
    "username": "test_admin",
    "display_name": "Test Admin",
    "password": gen_password("test_admin"),
  }
  page.goto(f"{live_server}/auth/setup")

  page.locator("#username").fill(admin["username"])
  page.locator("#display_name").fill(admin["display_name"])

  page.locator("#password").fill(admin["password"])
  page.locator("#confirm_password").fill(admin["password"])

  page.locator("button[type='submit']").click()

  page.wait_for_url(f"{live_server}/")

  page.locator("details summary").click()
  page.get_by_role("button", name="Log out").click()
  page.wait_for_url(f"{live_server}/auth/login")

  yield admin


@pytest.mark.e2e
def test_login_page_loads(page, live_server):
  page.goto(f"{live_server}/auth/login")

  expect(page.locator("#username")).to_be_visible()
  expect(page.locator("#password")).to_be_visible()
  expect(page.get_by_role("button", name="Log in")).to_be_visible()


@pytest.mark.e2e
def test_login_rejects_empty_username(page, live_server):
  page.goto(f"{live_server}/auth/login")

  page.locator("#username").fill("")
  page.locator("#password").fill("test_password")
  page.get_by_role("button", name="Log in").click()

  expect(page.locator("#username")).to_be_focused()


@pytest.mark.e2e
def test_login_rejects_empty_password(page, live_server):
  page.goto(f"{live_server}/auth/login")

  page.locator("#username").fill("test_admin")
  page.locator("#password").fill("")
  page.get_by_role("button", name="Log in").click()

  expect(page.locator("#password")).to_be_focused()


@pytest.mark.e2e
def test_login_rejects_invalid_username(page, live_server):
  page.goto(f"{live_server}/auth/login")

  page.locator("#username").fill("does_not_exist")
  page.locator("#password").fill("test_password")
  page.get_by_role("button", name="Log in").click()

  expect(page.get_by_role("alert")).to_have_text("Invalid username or password.")


@pytest.mark.e2e
def test_login_rejects_invalid_password(
  page,
  live_server,
):
  page.goto(f"{live_server}/auth/login")

  page.locator("#username").fill("test_admin")
  page.locator("#password").fill("wrong_password")
  page.get_by_role("button", name="Log in").click()

  expect(page.get_by_role("alert")).to_have_text("Invalid username or password.")


@pytest.mark.e2e
def test_login_accepts_valid_credentials(
  page,
  live_server,
  e2e_admin,
):
  page.goto(f"{live_server}/auth/login")

  page.locator("#username").fill(e2e_admin["username"])
  page.locator("#password").fill(e2e_admin["password"])
  page.get_by_role("button", name="Log in").click()

  page.wait_for_url(f"{live_server}/")

  page.locator("details summary").click()
  expect(page.get_by_role("button", name="Log out")).to_be_visible()


@pytest.mark.e2e
def test_login_redirects_authenticated_user(
  page,
  live_server,
  e2e_admin,
):
  page.goto(f"{live_server}/auth/login")

  page.locator("#username").fill(e2e_admin["username"])
  page.locator("#password").fill(e2e_admin["password"])
  page.get_by_role("button", name="Log in").click()

  page.wait_for_url(f"{live_server}/")

  page.goto(f"{live_server}/auth/login")

  page.wait_for_url(f"{live_server}/")

  page.locator("details summary").click()
  expect(page.get_by_role("button", name="Log out")).to_be_visible()

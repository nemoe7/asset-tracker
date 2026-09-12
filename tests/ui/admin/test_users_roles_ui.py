import pytest
from playwright.sync_api import expect


@pytest.mark.e2e
def test_users_tab_is_visible(page, live_server, setup_admin):
  page.goto(f"{live_server}/admin?tab=users")

  expect(page.locator("#tab-users")).to_be_visible()
  expect(page.get_by_role("button", name="Add user", exact=True)).to_be_visible()


@pytest.mark.e2e
def test_roles_tab_is_visible(page, live_server, setup_admin):
  page.goto(f"{live_server}/admin?tab=roles")

  expect(page.locator("#tab-roles")).to_be_visible()
  expect(page.get_by_role("button", name="Add role", exact=True)).to_be_visible()


@pytest.mark.e2e
def test_admin_page_creates_user(page, live_server, setup_admin):
  page.goto(f"{live_server}/admin?tab=users")

  page.locator("#add-user-button").click()

  page.locator("#add-user-username").fill("jsmith")
  page.locator("#add-user-name").fill("John Smith")
  page.locator("#add-user-password").fill("password123")

  page.locator("#add-user-dialog").get_by_role("button", name="Add user").click()

  page.wait_for_url(f"{live_server}/admin?tab=users")

  expect(page.get_by_text("jsmith", exact=True).first).to_be_visible()
  expect(page.get_by_text("John Smith").first).to_be_visible()


@pytest.mark.e2e
def test_admin_page_edits_user(page, live_server, setup_admin):
  response = page.request.post(
    f"{live_server}/admin/users",
    form={
      "username": "jsmith",
      "name": "John Smith",
      "password": "password123",
    },
    max_redirects=0,
  )

  assert response.status == 302

  page.goto(f"{live_server}/admin?tab=users")

  dialog = page.locator("#edit-user-dialog")
  expect(dialog).to_be_hidden()

  page.locator(".edit-user").first.click()

  expect(dialog).to_be_visible()
  expect(page.locator("#edit-user-username")).to_have_value("jsmith")
  expect(page.locator("#edit-user-name")).to_have_value("John Smith")
  expect(page.locator("#edit-user-password")).to_have_value("")

  page.locator("#edit-user-name").fill("Jonathan Smith")

  dialog.get_by_role("button", name="Save changes").click()

  page.wait_for_url(f"{live_server}/admin?tab=users")

  users_table = page.locator("#tab-users table")
  expect(users_table.get_by_text("Jonathan Smith").first).to_be_visible()
  expect(users_table.get_by_text("John Smith")).to_have_count(0)


@pytest.mark.e2e
def test_admin_page_archives_user(page, live_server, setup_admin):
  response = page.request.post(
    f"{live_server}/admin/users",
    form={
      "username": "jsmith",
      "name": "John Smith",
      "password": "password123",
    },
    max_redirects=0,
  )

  assert response.status == 302

  page.goto(f"{live_server}/admin?tab=users")

  row = page.locator("#tab-users tbody tr").filter(has_text="jsmith")
  expect(row).to_be_visible()

  row.locator("[data-archive-user] button[type='submit']").click()

  dialog = page.locator("#archive-user-dialog")
  expect(dialog).to_be_visible()

  dialog.get_by_role("button", name="Archive user").click()

  page.wait_for_url(f"{live_server}/admin?tab=users")

  expect(page.locator("#tab-users tbody tr").filter(has_text="jsmith")).to_have_count(0)


@pytest.mark.e2e
def test_admin_page_creates_role(page, live_server, setup_admin):
  page.goto(f"{live_server}/admin?tab=roles")

  page.locator("#add-role-button").click()

  page.locator("#add-role-name").fill("Viewer")
  page.locator("#add-role-description").fill("Read-only access")

  page.locator("#add-role-dialog").get_by_role("button", name="Add role").click()

  page.wait_for_url(f"{live_server}/admin?tab=roles")

  roles_table = page.locator("#tab-roles table")
  expect(roles_table).to_be_visible()
  expect(roles_table.get_by_text("Viewer", exact=True)).to_be_visible()
  expect(roles_table.get_by_text("Read-only access")).to_be_visible()


@pytest.mark.e2e
def test_admin_page_edits_role(page, live_server, setup_admin):
  response = page.request.post(
    f"{live_server}/admin/roles",
    form={
      "name": "Viewer",
      "description": "Read-only access",
    },
    max_redirects=0,
  )

  assert response.status == 302

  page.goto(f"{live_server}/admin?tab=roles")

  dialog = page.locator("#edit-role-dialog")
  expect(dialog).to_be_hidden()

  row = page.locator("#tab-roles tbody tr").filter(has_text="Viewer")
  row.locator(".edit-role").click()

  expect(dialog).to_be_visible()
  expect(page.locator("#edit-role-name")).to_have_value("Viewer")
  expect(page.locator("#edit-role-description")).to_have_value("Read-only access")

  page.locator("#edit-role-name").fill("Read Only")
  page.locator("#edit-role-description").fill("View only")

  dialog.get_by_role("button", name="Save changes").click()

  page.wait_for_url(f"{live_server}/admin?tab=roles")

  roles_table = page.locator("#tab-roles table")
  expect(roles_table.get_by_text("Read Only", exact=True).first).to_be_visible()
  expect(roles_table.get_by_text("View only").first).to_be_visible()
  expect(roles_table.get_by_text("Read-only access")).to_have_count(0)


@pytest.mark.e2e
def test_admin_page_deletes_unassigned_role(page, live_server, setup_admin):
  response = page.request.post(
    f"{live_server}/admin/roles",
    form={
      "name": "Temp Role",
      "description": "Temporary",
    },
    max_redirects=0,
  )

  assert response.status == 302

  page.goto(f"{live_server}/admin?tab=roles")

  row = page.locator("#tab-roles tbody tr").filter(has_text="Temp Role")
  expect(row).to_be_visible()

  row.locator("[data-delete-role] button[type='submit']").click()

  dialog = page.locator("#delete-role-dialog")
  expect(dialog).to_be_visible()

  dialog.get_by_role("button", name="Delete role").click()

  page.wait_for_url(f"{live_server}/admin?tab=roles")

  expect(
    page.locator("#tab-roles tbody tr").filter(has_text="Temp Role")
  ).to_have_count(0)


@pytest.mark.e2e
def test_admin_page_grants_permission_to_role(page, live_server, setup_admin):
  response = page.request.post(
    f"{live_server}/admin/roles",
    form={
      "name": "Viewer",
      "description": "Read-only access",
    },
    max_redirects=0,
  )

  assert response.status == 302

  page.goto(f"{live_server}/admin?tab=roles")

  row = page.locator("#tab-roles tbody tr").filter(has_text="Viewer")
  expect(row).to_be_visible()

  row.locator(".grant-role-permission").click()

  dialog = page.locator("#grant-role-permission-dialog")
  expect(dialog).to_be_visible()

  page.locator("#grant-role-permission-name").fill("assets.read")
  page.locator("#grant-role-permission-allowed").check()

  dialog.get_by_role("button", name="Grant permission").click()

  page.wait_for_url(f"{live_server}/admin?tab=roles")

  expect(page.get_by_text("assets.read").first).to_be_visible()


@pytest.mark.e2e
def test_admin_page_unknown_permission_warning(page, live_server, setup_admin):
  response = page.request.post(
    f"{live_server}/admin/roles",
    form={
      "name": "Viewer",
      "description": "Read-only access",
    },
    max_redirects=0,
  )

  assert response.status == 302

  page.goto(f"{live_server}/admin?tab=roles")

  row = page.locator("#tab-roles tbody tr").filter(has_text="Viewer")
  expect(row).to_be_visible()

  row.locator(".grant-role-permission").click()

  dialog = page.locator("#grant-role-permission-dialog")
  expect(dialog).to_be_visible()

  page.locator("#grant-role-permission-name").fill("custom.unknown.permission")

  expect(page.locator("#grant-role-permission-warning")).to_be_visible()

  dialog.get_by_role("button", name="Close").click()

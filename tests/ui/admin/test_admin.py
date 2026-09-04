import pytest
from playwright.sync_api import expect


@pytest.fixture
def logged_in(page, live_server, setup_admin):
  # The admin created during /auth/setup is already authenticated,
  # so the session is established by just visiting the page.
  page.goto(f"{live_server}/")


@pytest.mark.e2e
def test_menu_contains_admin_panel_link(page, live_server, logged_in):
  menu = page.locator("details")
  menu.locator("summary").click()

  expect(
    page.get_by_role("link", name="Management", exact=True)
  ).to_be_visible()

  # The individual tab links are no longer in the menu.
  expect(page.get_by_role("link", name="Locations", exact=True)).to_have_count(0)
  expect(page.get_by_role("link", name="Custom fields", exact=True)).to_have_count(0)


@pytest.mark.e2e
def test_menu_admin_panel_opens_admin_page(page, live_server, logged_in):
  menu = page.locator("details")
  menu.locator("summary").click()

  page.get_by_role("link", name="Management", exact=True).click()

  page.wait_for_url(f"{live_server}/admin")

  expect(page.locator("#tab-locations")).to_be_visible()


@pytest.mark.e2e
def test_admin_page_creates_location(page, live_server, logged_in):
  page.goto(f"{live_server}/admin?tab=locations")

  page.locator("#add-location-button").click()

  page.locator("#add-location-name").fill("Warehouse")
  page.locator("#add-location-description").fill("Main storage area")

  page.locator("#add-location-dialog").get_by_role("button", name="Add location").click()

  page.wait_for_url(f"{live_server}/admin?tab=locations")

  expect(page.get_by_text("Warehouse", exact=True).first).to_be_visible()
  expect(page.get_by_text("Main storage area").first).to_be_visible()


@pytest.mark.e2e
def test_admin_page_edits_location(page, live_server, logged_in):
  response = page.request.post(
    f"{live_server}/admin/locations",
    form={
      "name": "Warehouse",
      "description": "Main storage area",
    },
    max_redirects=0,
  )

  assert response.status == 302

  page.goto(f"{live_server}/admin?tab=locations")

  dialog = page.locator("#edit-location-dialog")
  expect(dialog).to_be_hidden()

  page.locator(".edit-location").first.click()

  expect(dialog).to_be_visible()
  expect(page.locator("#edit-location-name")).to_have_value("Warehouse")
  expect(page.locator("#edit-location-description")).to_have_value(
    "Main storage area"
  )

  page.locator("#edit-location-name").fill("Main Warehouse")
  page.locator("#edit-location-description").fill("Updated storage area")

  dialog.get_by_role("button", name="Save changes").click()

  page.wait_for_url(f"{live_server}/admin?tab=locations")

  expect(page.get_by_text("Main Warehouse", exact=True).first).to_be_visible()
  expect(page.get_by_text("Warehouse", exact=True).first).to_be_hidden()


@pytest.mark.e2e
def test_admin_page_edit_location_modal_can_close(
  page,
  live_server,
  logged_in,
  create_location,
):
  create_location("Warehouse")

  page.goto(f"{live_server}/admin?tab=locations")

  dialog = page.locator("#edit-location-dialog")
  expect(dialog).to_be_hidden()

  page.locator(".edit-location").first.click()
  expect(dialog).to_be_visible()

  dialog.get_by_role("button", name="Close").click()

  expect(dialog).to_be_hidden()


@pytest.mark.e2e
def test_admin_page_creates_custom_field(page, live_server, logged_in):
  page.goto(f"{live_server}/admin?tab=custom-fields")

  page.locator("#add-field-button").click()

  dialog = page.locator("#add-field-dialog")
  expect(dialog).to_be_visible()

  page.locator("#add-field-name").fill("Serial Number")
  page.locator("#add-field-type").select_option("text")

  dialog.get_by_role("button", name="Add field").click()

  page.wait_for_url(f"{live_server}/admin?tab=custom-fields")

  row = page.locator("#tab-custom-fields tbody tr").filter(
    has_text="Serial Number"
  )
  expect(row).to_be_visible()
  expect(row.get_by_text("text", exact=True)).to_be_visible()



@pytest.mark.e2e
def test_admin_page_tabs_switch_client_side(page, live_server, logged_in):
  page.goto(f"{live_server}/admin")

  expect(page.locator("#tab-locations")).to_be_visible()
  expect(page.locator("#tab-custom-fields")).to_be_hidden()

  page.locator("[data-tab-button='custom-fields']").click()

  expect(page.locator("#tab-locations")).to_be_hidden()
  expect(page.locator("#tab-custom-fields")).to_be_visible()

  page.locator("[data-tab-button='locations']").click()

  expect(page.locator("#tab-locations")).to_be_visible()
  expect(page.locator("#tab-custom-fields")).to_be_hidden()


@pytest.mark.e2e
def test_admin_page_has_hamburger_menu(page, live_server, logged_in):
  page.goto(f"{live_server}/admin")

  menu = page.locator("details")
  expect(menu).to_be_visible()
  expect(menu.get_by_text("@test_admin", exact=True)).to_be_hidden()

  menu.locator("summary").click()

  expect(menu.get_by_text("@test_admin", exact=True)).to_be_visible()
  expect(page.get_by_role("link", name="Management", exact=True)).to_be_visible()
  expect(page.get_by_role("button", name="Log out")).to_be_visible()


@pytest.mark.e2e
def test_admin_page_data_tab_is_reachable(page, live_server, logged_in):
  page.goto(f"{live_server}/admin?tab=data")

  expect(page.locator("#tab-data")).to_be_visible()
  expect(page.locator("#import-button")).to_be_visible()
  expect(page.locator("#export-button")).to_be_visible()


@pytest.mark.e2e
def test_admin_page_required_column_shows_x_icon(page, live_server, logged_in):
  response = page.request.post(
    f"{live_server}/admin/custom-fields",
    form={
      "name": "Condition",
      "field_type": "text",
    },
    max_redirects=0,
  )

  assert response.status == 302

  page.goto(f"{live_server}/admin?tab=custom-fields")

  row = page.locator("#tab-custom-fields tbody tr").filter(has_text="Condition")

  expect(row).to_be_visible()
  expect(row.locator(".bi-x-lg")).to_be_visible()
  expect(row.locator(".bi-check-lg")).to_have_count(0)


@pytest.mark.e2e
def test_admin_page_delete_location_requires_confirmation(
  page,
  live_server,
  logged_in,
  create_location,
):
  create_location("Warehouse")

  page.goto(f"{live_server}/admin?tab=locations")

  page.locator("[data-delete-location] button[type='submit']").first.click()

  dialog = page.locator("#delete-location-dialog")
  expect(dialog).to_be_visible()

  page.locator("#cancel-delete-location").click()

  expect(dialog).to_be_hidden()
  expect(page.get_by_text("Warehouse", exact=True).first).to_be_visible()

  page.locator("[data-delete-location] button[type='submit']").first.click()

  expect(dialog).to_be_visible()
  page.locator("#confirm-delete-location").click()

  expect(page.get_by_text("Warehouse", exact=True).first).to_be_hidden()


@pytest.mark.e2e
def test_admin_page_add_location_modal_closes_on_outside_click(
  page,
  live_server,
  logged_in,
):
  page.goto(f"{live_server}/admin?tab=locations")

  page.locator("#add-location-button").click()

  dialog = page.locator("#add-location-dialog")
  expect(dialog).to_be_visible()

  page.mouse.click(10, 200)

  expect(dialog).to_be_hidden()


@pytest.mark.e2e
def test_admin_page_delete_location_cancel_on_outside_click(
  page,
  live_server,
  logged_in,
  create_location,
):
  create_location("Warehouse")

  page.goto(f"{live_server}/admin?tab=locations")

  page.locator("[data-delete-location] button[type='submit']").first.click()

  dialog = page.locator("#delete-location-dialog")
  expect(dialog).to_be_visible()

  page.mouse.click(10, 200)

  expect(dialog).to_be_hidden()
  expect(page.get_by_text("Warehouse", exact=True).first).to_be_visible()


@pytest.mark.e2e
def test_admin_page_delete_location_cancel_on_escape(
  page,
  live_server,
  logged_in,
  create_location,
):
  create_location("Warehouse")

  page.goto(f"{live_server}/admin?tab=locations")

  page.locator("[data-delete-location] button[type='submit']").first.click()

  dialog = page.locator("#delete-location-dialog")
  expect(dialog).to_be_visible()

  page.keyboard.press("Escape")

  expect(dialog).to_be_hidden()
  expect(page.get_by_text("Warehouse", exact=True).first).to_be_visible()


@pytest.mark.e2e
def test_admin_page_creates_enum_custom_field(page, live_server, logged_in):
  page.goto(f"{live_server}/admin?tab=custom-fields")

  page.locator("#add-field-button").click()

  page.locator("#add-field-name").fill("Category")
  page.locator("#add-field-type").select_option("enum")

  enumValues = page.locator("#add-field-enum-values")
  expect(enumValues).to_be_visible()
  enumValues.fill("IT\nHR\nFinance")

  page.locator("#add-field-dialog").get_by_role("button", name="Add field").click()

  page.wait_for_url(f"{live_server}/admin?tab=custom-fields")

  row = page.locator("#tab-custom-fields tbody tr").filter(
    has_text="Category"
  )
  expect(row).to_be_visible()
  expect(row.get_by_text("enum", exact=True)).to_be_visible()

  row.locator(".edit-field").click()

  expect(page.locator("#edit-field-dialog")).to_be_visible()
  expect(page.locator("#edit-field-enum-values")).to_have_value("IT\nHR\nFinance")


@pytest.mark.e2e
def test_admin_page_edits_enum_custom_field_values(
  page,
  live_server,
  logged_in,
):
  response = page.request.post(
    f"{live_server}/admin/custom-fields",
    form={
      "name": "Category",
      "field_type": "enum",
      "enum_values": "IT\nHR",
    },
    max_redirects=0,
  )

  assert response.status == 302

  page.goto(f"{live_server}/admin?tab=custom-fields")

  row = page.locator("#tab-custom-fields tbody tr").filter(has_text="Category")
  expect(row).to_be_visible()

  row.locator(".edit-field").click()

  dialog = page.locator("#edit-field-dialog")
  expect(dialog).to_be_visible()
  expect(page.locator("#edit-field-enum-values")).to_have_value("IT\nHR")

  page.locator("#edit-field-enum-values").fill("IT\nFinance")

  dialog.get_by_role("button", name="Save changes").click()

  page.wait_for_url(f"{live_server}/admin?tab=custom-fields")

  row.locator(".edit-field").click()

  expect(page.locator("#edit-field-enum-values")).to_have_value("IT\nFinance")


@pytest.mark.e2e
def test_admin_page_archives_and_restores_custom_field(
  page,
  live_server,
  logged_in,
):
  response = page.request.post(
    f"{live_server}/admin/custom-fields",
    form={
      "name": "Condition",
      "field_type": "text",
    },
    max_redirects=0,
  )

  assert response.status == 302

  page.goto(f"{live_server}/admin?tab=custom-fields")

  row = page.locator("#tab-custom-fields tbody tr").filter(has_text="Condition")
  expect(row).to_be_visible()

  row.locator("[data-archive-field] button[type='submit']").click()

  dialog = page.locator("#archive-field-dialog")
  expect(dialog).to_be_visible()

  dialog.get_by_role("button", name="Archive field").click()

  page.wait_for_url(f"{live_server}/admin?tab=custom-fields")

  expect(
    page.locator("#tab-custom-fields tbody tr").filter(has_text="Condition")
  ).to_have_count(0)

  archived_section = page.locator("details.group")
  expect(archived_section).to_be_visible()
  archived_section.locator("summary").click()

  expect(archived_section.get_by_text("Condition")).to_be_visible()
  archived_section.get_by_role("button", name="Restore").click()

  page.wait_for_url(f"{live_server}/admin?tab=custom-fields")

  restored = page.locator("#tab-custom-fields tbody tr").filter(
    has_text="Condition"
  )
  expect(restored).to_be_visible()


@pytest.mark.e2e
def test_admin_page_edits_custom_field(page, live_server, logged_in):
  response = page.request.post(
    f"{live_server}/admin/custom-fields",
    form={
      "name": "Serial Number",
      "field_type": "text",
    },
    max_redirects=0,
  )

  assert response.status == 302

  page.goto(f"{live_server}/admin?tab=custom-fields")

  dialog = page.locator("#edit-field-dialog")
  expect(dialog).to_be_hidden()

  row = page.locator("#tab-custom-fields tbody tr").filter(
    has_text="Serial Number"
  )
  row.locator(".edit-field").click()

  expect(dialog).to_be_visible()
  expect(page.locator("#edit-field-name")).to_have_value("Serial Number")
  expect(page.locator("#edit-field-type")).to_have_value("text")

  page.locator("#edit-field-name").fill("Asset Serial Number")
  page.locator("#edit-field-description").fill("Manufacturer serial")

  dialog.get_by_role("button", name="Save changes").click()

  page.wait_for_url(f"{live_server}/admin?tab=custom-fields")

  expect(page.get_by_text("Asset Serial Number", exact=True).first).to_be_visible()
  expect(page.get_by_text("Serial Number", exact=True)).to_have_count(0)


@pytest.mark.e2e
def test_admin_page_edit_field_modal_can_close(page, live_server, logged_in):
  response = page.request.post(
    f"{live_server}/admin/custom-fields",
    form={
      "name": "Serial Number",
      "field_type": "text",
    },
    max_redirects=0,
  )

  assert response.status == 302

  page.goto(f"{live_server}/admin?tab=custom-fields")

  dialog = page.locator("#edit-field-dialog")
  expect(dialog).to_be_hidden()

  page.locator(".edit-field").first.click()
  expect(dialog).to_be_visible()

  dialog.get_by_role("button", name="Close").click()

  expect(dialog).to_be_hidden()


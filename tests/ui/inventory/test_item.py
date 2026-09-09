import re

import pytest
from playwright.sync_api import expect


@pytest.mark.e2e
def test_item_can_be_viewed(
  page,
  live_server,
  create_item,
):
  item = create_item("Test Asset")

  page.goto(f"{live_server}/")

  page.locator(f'tr.view-item[data-item-id="{item["id"]}"]').click()

  modal = page.locator("#view-item-modal")

  expect(modal).to_be_visible()
  expect(page.locator("#view-item-id")).to_have_text(item["id"])
  expect(page.locator("#view-item-name")).to_have_text("Test Asset")


@pytest.mark.e2e
def test_view_modal_edit_opens_edit_modal(
  page,
  live_server,
  create_item,
):
  item = create_item("Test Asset")

  page.goto(f"{live_server}/")

  page.locator(f'tr.view-item[data-item-id="{item["id"]}"]').click()

  expect(page.locator("#view-item-modal")).to_be_visible()

  page.locator("#view-item-edit").click()

  expect(page.locator("#edit-item-modal")).to_be_visible()
  expect(page.locator("#view-item-modal")).not_to_be_visible()
  expect(page.locator("#edit-item-id")).to_have_text(item["id"])
  expect(page.locator("#edit-item-name")).to_have_value("Test Asset")


@pytest.mark.e2e
def test_item_edit_modal_loads_existing_values(
  page,
  live_server,
  create_item,
):
  item = create_item("Test Asset")

  page.goto(f"{live_server}/")

  page.locator(f'tr .edit-item[data-item-id="{item["id"]}"]').click()

  modal = page.locator("#edit-item-modal")

  expect(modal).to_be_visible()
  expect(page.locator("#edit-item-id")).to_have_text(item["id"])
  expect(page.locator("#edit-item-name")).to_have_value("Test Asset")


@pytest.mark.e2e
def test_item_can_be_edited(
  page,
  live_server,
  create_item,
):
  item = create_item("Test Asset")

  page.goto(f"{live_server}/")

  page.locator(f'tr .edit-item[data-item-id="{item["id"]}"]').click()

  page.locator("#edit-item-name").fill("Renamed Asset")

  page.get_by_role(
    "button",
    name="Save changes",
  ).click()

  expect(page.locator(f'tr.view-item[data-item-id="{item["id"]}"]')).to_contain_text(
    "Renamed Asset"
  )


@pytest.mark.e2e
def test_edit_item_description(page, live_server, create_item):
  item = create_item("Test Asset")

  page.goto(f"{live_server}/")

  page.locator(f'tr .edit-item[data-item-id="{item["id"]}"]').click()

  description = page.locator("#edit-item-description")
  expect(description).to_be_visible()

  description.fill("Updated description")

  page.get_by_role(
    "button",
    name="Save changes",
  ).click()

  page.wait_for_url(f"{live_server}/")

  page.get_by_title("Test Asset").click()

  expect(page.locator("#view-item-description")).to_have_text("Updated description")


@pytest.mark.e2e
def test_edit_item_description_can_be_cleared(page, live_server, create_item):
  item = create_item("Test Asset")

  page.goto(f"{live_server}/")

  page.locator(f'tr .edit-item[data-item-id="{item["id"]}"]').click()

  page.locator("#edit-item-description").fill("Temporary description")
  page.get_by_role(
    "button",
    name="Save changes",
  ).click()

  page.wait_for_url(f"{live_server}/")

  page.locator(f'tr .edit-item[data-item-id="{item["id"]}"]').click()

  page.locator("#edit-item-description").fill("")
  page.get_by_role(
    "button",
    name="Save changes",
  ).click()

  page.wait_for_url(f"{live_server}/")

  page.locator("#inventory-content").get_by_role("cell", name="Test Asset").click()

  expect(page.locator("#view-item-description")).to_have_text("—")


@pytest.mark.e2e
def test_item_can_open_archive_confirmation(
  page,
  live_server,
  create_item,
):
  item = create_item("Test Asset")

  page.goto(f"{live_server}/")

  page.locator(f'tr .edit-item[data-item-id="{item["id"]}"]').click()

  page.locator("#archive-item-button").click()

  expect(page.locator("#archive-item-modal")).to_be_visible()


@pytest.mark.e2e
def test_item_can_be_archived(
  page,
  live_server,
  create_item,
):
  item = create_item("Test Asset")

  page.goto(f"{live_server}/")

  page.locator(f'tr .edit-item[data-item-id="{item["id"]}"]').click()

  page.locator("#archive-item-button").click()

  page.get_by_role(
    "button",
    name="Archive asset",
  ).last.click()

  expect(page.locator(f'tr.view-item[data-item-id="{item["id"]}"]')).not_to_be_visible()


@pytest.mark.e2e
def test_archived_item_can_be_restored(
  page,
  live_server,
  create_item,
):
  item = create_item("Test Asset")

  page.goto(f"{live_server}/")

  page.locator(f'tr .edit-item[data-item-id="{item["id"]}"]').click()

  page.locator("#archive-item-button").click()

  page.get_by_role(
    "button",
    name="Archive asset",
  ).last.click()

  page.locator("#filter-item-button").click()

  page.get_by_role(
    "checkbox",
    name="Include Archived",
  ).check()

  page.get_by_role(
    "button",
    name="Apply",
  ).click()

  page.locator(f'.restore-item[data-item-id="{item["id"]}"]').click()

  expect(page.locator("#restore-item-modal")).to_be_visible()

  page.get_by_role(
    "button",
    name="Restore asset",
  ).last.click()

  expect(page.locator(f'tr.view-item[data-item-id="{item["id"]}"]')).to_be_visible()


@pytest.mark.e2e
def test_item_id_is_uuid(
  page,
  live_server,
  create_item,
):
  item = create_item("Test Asset")

  page.goto(f"{live_server}/")

  page.locator(f'tr.view-item[data-item-id="{item["id"]}"]').click()

  expect(page.locator("#view-item-id")).to_have_text(
    re.compile(
      r"^[0-9a-f]{8}-[0-9a-f]{4}-"
      r"[0-9a-f]{4}-[0-9a-f]{4}-"
      r"[0-9a-f]{12}$",
      re.IGNORECASE,
    )
  )


@pytest.mark.e2e
def test_item_ids_are_unique(
  page,
  live_server,
  create_item,
):
  item_a = create_item("Asset A")
  item_b = create_item("Asset B")

  assert item_a["id"] != item_b["id"]


@pytest.mark.e2e
def test_edit_item_shows_inline_error_on_validation_failure(
  page,
  live_server,
  create_item,
  create_custom_field,
):
  item = create_item("Test Asset")

  create_custom_field("Serial Number", "text", required=True)

  page.goto(f"{live_server}/")

  page.evaluate("""() => {
    window._originalFetch = window.fetch;
    window.fetch = function(url, options) {
      if (options && options.method === 'POST' && url.includes('/inventory/')) {
        return Promise.resolve(new Response(JSON.stringify({error: 'Required custom field cannot be unset'}), {
          status: 400,
          headers: { 'Content-Type': 'application/json' }
        }));
      }
      return window._originalFetch(url, options);
    };
  }""")

  page.locator(f'tr .edit-item[data-item-id="{item["id"]}"]').click()

  expect(page.locator("#edit-item-modal")).to_be_visible()

  page.locator("#edit-item-name").fill("Updated")

  page.evaluate("""() => {
    const serialInput = document.querySelector('input[name="f_Serial Number"], textarea[name="f_Serial Number"], select[name="f_Serial Number"]');
    if (serialInput) {
      serialInput.required = false;
    }
  }""")

  page.get_by_role(
    "button",
    name="Save changes",
  ).click()

  expect(page.locator("#edit-item-error")).to_be_visible()
  expect(page.locator("#edit-item-modal")).to_be_visible()


@pytest.mark.e2e
def test_archive_item_shows_inline_error_on_failure(
  page,
  live_server,
  create_item,
):
  item = create_item("Test Asset")

  page.goto(f"{live_server}/")

  page.locator(f'tr .edit-item[data-item-id="{item["id"]}"]').click()

  page.locator("#archive-item-button").click()

  page.evaluate("""() => {
    window._originalFetch = window.fetch;
    window.fetch = function(url, options) {
      if (options && options.method === 'POST' && url.includes('/archive')) {
        return Promise.resolve(new Response(JSON.stringify({error: 'Item is already archived'}), {
          status: 400,
          headers: { 'Content-Type': 'application/json' }
        }));
      }
      return window._originalFetch(url, options);
    };
  }""")

  page.get_by_role(
    "button",
    name="Archive asset",
  ).last.click()

  expect(page.locator("#archive-item-error")).to_be_visible()
  expect(page.locator("#archive-item-modal")).to_be_visible()


@pytest.mark.e2e
def test_asset_name_link_opens_view_modal(
  page,
  live_server,
  create_item,
):
  item = create_item("Test Asset")

  page.goto(f"{live_server}/")

  page.locator(f"a.view-item-link[data-item-id='{item["id"]}']").first.click()

  expect(page.locator("#view-item-modal")).to_be_visible()
  expect(page.locator("#view-item-name")).to_have_text("Test Asset")


@pytest.mark.e2e
def test_asset_name_link_is_keyboard_accessible(
  page,
  live_server,
  create_item,
):
  item = create_item("Test Asset")

  page.goto(f"{live_server}/")

  page.locator(f"a.view-item-link[data-item-id='{item["id"]}']").first.focus()

  page.locator(f"a.view-item-link[data-item-id='{item["id"]}']").first.press("Enter")

  expect(page.locator("#view-item-modal")).to_be_visible()
  expect(page.locator("#view-item-name")).to_have_text("Test Asset")

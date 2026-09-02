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

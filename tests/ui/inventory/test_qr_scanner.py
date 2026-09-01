import pytest
from playwright.sync_api import expect


@pytest.mark.e2e
def test_qr_scanner_button_opens_modal(page, live_server):
  page.add_init_script("""
    window.Html5Qrcode = class {
      async start() {
        return;
      }

      async stop() {
        return;
      }

      clear() {}
    };
  """)

  page.goto(f"{live_server}/")

  page.locator("#qr-scanner-button").click()

  modal = page.locator("#qr-scanner-modal")

  expect(modal).to_be_visible()
  expect(modal.get_by_role("heading", name="Scan QR code")).to_be_visible()

  expect(modal.get_by_text("Scan an inventory item QR code.")).to_be_visible()

  expect(page.locator("#qr-reader")).to_be_visible()


@pytest.mark.e2e
def test_qr_scanner_shows_loading_while_starting(page, live_server):
  page.add_init_script("""
    window.Html5Qrcode = class {
      async start() {
        await new Promise(() => {});
      }

      async stop() {
        return;
      }

      clear() {}
    };
  """)

  page.goto(f"{live_server}/")

  page.locator("#qr-scanner-button").click()

  expect(page.locator("#modal-manager")).to_be_visible()
  expect(page.locator("#modal-manager-loading")).to_be_visible()
  expect(page.locator("#qr-scanner-modal")).to_be_hidden()


@pytest.mark.e2e
def test_qr_scanner_hides_loading_after_starting(page, live_server):
  page.add_init_script("""
    window.Html5Qrcode = class {
      async start() {
        return;
      }

      async stop() {
        return;
      }

      clear() {}
    };
  """)

  page.goto(f"{live_server}/")

  page.locator("#qr-scanner-button").click()

  expect(page.locator("#qr-scanner-modal")).to_be_visible()
  expect(page.locator("#modal-manager-loading")).to_be_hidden()
  expect(page.locator("#qr-reader")).to_be_visible()


@pytest.mark.e2e
def test_qr_scanner_closes_and_stops(page, live_server):
  page.add_init_script("""
    window.qrScannerStopCalled = false;

    window.Html5Qrcode = class {
      async start() {
        return;
      }

      async stop() {
        window.qrScannerStopCalled = true;
      }

      clear() {}
    };
  """)

  page.goto(f"{live_server}/")

  page.locator("#qr-scanner-button").click()

  modal = page.locator("#qr-scanner-modal")

  expect(modal).to_be_visible()

  modal.locator(".modal-close").click()

  expect(modal).to_be_hidden()

  page.wait_for_function("window.qrScannerStopCalled === true")

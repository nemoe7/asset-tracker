import pytest
from playwright.sync_api import expect


@pytest.fixture(autouse=True)
def qr_scanner_mobile_viewport(page):
  # The Scan button is hidden on desktop (md:hidden); QR tests run on a
  # mobile-sized viewport where it is visible.
  page.set_viewport_size({"width": 375, "height": 667})

  yield


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

  expect(modal.get_by_text("Scan an asset QR code.")).to_be_visible()

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


@pytest.mark.e2e
def test_qr_scanner_checks_and_opens_item(page, live_server, create_item):
  item = create_item("Scanned Asset")

  page.add_init_script(
    f"""
      window.qrScannerStopCalled = false;

      window.Html5Qrcode = class {{
        async start(config, options, onScan) {{
          onScan("{item["id"]}");
        }}

        async stop() {{
          window.qrScannerStopCalled = true;
        }}

        clear() {{}}
      }};
    """
  )

  page.goto(f"{live_server}/")

  page.locator("#qr-scanner-button").click()

  page.wait_for_function("window.qrScannerStopCalled === true")

  expect(page.locator("#qr-scanner-modal")).to_be_hidden()
  expect(page.locator("#view-item-modal")).to_be_visible()
  expect(page.locator("#view-item-name")).to_have_text("Scanned Asset")
  expect(page.locator("#view-item-id")).to_have_text(item["id"])


@pytest.mark.e2e
def test_qr_scanner_reports_unknown_item(page, live_server):
  unknown_id = "nonexistent-item-id"

  page.add_init_script(
    f"""
      window.qrScannerStopCalled = false;

      window.Html5Qrcode = class {{
        async start(config, options, onScan) {{
          onScan("{unknown_id}");
        }}

        async stop() {{
          window.qrScannerStopCalled = true;
        }}

        clear() {{}}
      }};
    """
  )
  page.goto(f"{live_server}/")

  page.locator("#qr-scanner-button").click()

  expect(page.locator("#qr-scanner-error")).to_have_text("Item does not exist")
  expect(page.locator("#qr-scanner-modal")).to_be_visible()
  expect(page.locator("#view-item-modal")).to_be_hidden()
  assert page.evaluate("window.qrScannerStopCalled") is False


@pytest.mark.e2e
def test_qr_scanner_reports_archived_item(page, live_server, create_item):
  item = create_item("Archived Asset")

  response = page.request.post(
    f"{live_server}/inventory/{item['id']}/archive",
    headers={"Accept": "application/json"},
  )
  assert response.ok

  page.add_init_script(
    f"""
      window.qrScannerStopCalled = false;

      window.Html5Qrcode = class {{
        async start(config, options, onScan) {{
          onScan("{item["id"]}");
        }}

        async stop() {{
          window.qrScannerStopCalled = true;
        }}

        clear() {{}}
      }};
    """
  )
  page.goto(f"{live_server}/")

  page.locator("#qr-scanner-button").click()

  expect(page.locator("#qr-scanner-error")).to_have_text("Item is archived")
  expect(page.locator("#qr-scanner-modal")).to_be_visible()
  expect(page.locator("#view-item-modal")).to_be_hidden()
  assert page.evaluate("window.qrScannerStopCalled") is False


@pytest.mark.e2e
def test_qr_scanner_error_hides_after_scan(page, live_server, create_item):
  item = create_item("Scanned Asset")

  page.add_init_script(
    """
      window.qrScannerStopCalled = false;
      window.qrScanCallback = null;

      window.Html5Qrcode = class {
        async start(config, options, onScan) {
          window.qrScanCallback = onScan;
        }

        async stop() {
          window.qrScannerStopCalled = true;
        }

        clear() {{}}
      };
    """
  )

  page.goto(f"{live_server}/")

  page.locator("#qr-scanner-button").click()

  page.wait_for_function("typeof window.qrScanCallback === 'function'")

  page.evaluate(
    """
      window.qrScanCallback("nonexistent-item-id");
    """
  )

  expect(page.locator("#qr-scanner-error")).to_have_text("Item does not exist")

  page.evaluate(
    f"""
      window.qrScanCallback("{item["id"]}");
    """
  )

  expect(page.locator("#qr-scanner-error")).to_be_hidden()
  expect(page.locator("#view-item-modal")).to_be_visible()
  expect(page.locator("#view-item-name")).to_have_text("Scanned Asset")

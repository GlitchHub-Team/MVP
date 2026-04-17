import os

from playwright.sync_api import expect, sync_playwright


def test_login_page_shows_expected_content() -> None:
    base_url = os.getenv("APP_URL")

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto(f"{base_url}/login", wait_until="domcontentloaded", timeout=60000)

        expect(page.get_by_role("heading", name="Accedi")).to_be_visible(timeout=60000)
        expect(page.get_by_text("Email", exact=True)).to_be_visible()
        expect(page.get_by_text("Password", exact=True)).to_be_visible()
        expect(page.get_by_text("Tenant", exact=True)).to_be_visible()
        expect(page.get_by_role("button", name="Continua")).to_be_visible()
        expect(page.get_by_role("button", name="Password Dimenticata?")).to_be_visible()

        browser.close()

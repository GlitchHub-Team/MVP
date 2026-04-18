from playwright.sync_api import Page


DEFAULT_LOGIN_EMAIL = "super@admin.com"
DEFAULT_LOGIN_PASSWORD = "12345678"


def login_as_superadmin(
    page: Page,
    base_url: str,
    email: str = DEFAULT_LOGIN_EMAIL,
    password: str = DEFAULT_LOGIN_PASSWORD,
) -> None:
    page.goto(f"{base_url}/login", wait_until="domcontentloaded", timeout=60000)
    page.get_by_label("Email").fill(email)
    page.get_by_label("Password").fill(password)
    page.get_by_role("button", name="Continua").click()
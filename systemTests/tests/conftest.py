from collections.abc import Iterator

import pytest
from playwright.sync_api import APIRequestContext, sync_playwright

from test_support.api import login_super_admin, new_api_context, require_env


@pytest.fixture()
def api_context() -> Iterator[APIRequestContext]:
    require_env("APP_URL")
    with sync_playwright() as playwright:
        api = new_api_context(playwright)
        try:
            yield api
        finally:
            api.dispose()


@pytest.fixture()
def super_admin_jwt(api_context: APIRequestContext) -> str:
    return login_super_admin(api_context)

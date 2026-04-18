import os
import time

import pytest
from playwright.sync_api import APIRequestContext, APIResponse, Playwright

from test_support.login import DEFAULT_LOGIN_EMAIL, DEFAULT_LOGIN_PASSWORD


def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        pytest.skip(f"Missing env var: {name}")
    return value


def new_api_context(playwright: Playwright, base_url: str | None = None) -> APIRequestContext:
    resolved_base_url = base_url or require_env("APP_URL")
    return playwright.request.new_context(base_url=resolved_base_url)


def login_super_admin(
    api: APIRequestContext,
    email: str = DEFAULT_LOGIN_EMAIL,
    password: str = DEFAULT_LOGIN_PASSWORD,
) -> str:
    response = api.post(
        "/api/v1/auth/login",
        data={
            "email": email,
            "password": password,
        },
    )
    assert response.ok, f"Login failed. status={response.status} body={response.text()}"

    payload = response.json()
    jwt = payload.get("jwt")
    assert isinstance(jwt, str) and jwt, f"Missing jwt in login response: {payload}"
    return jwt


def bearer_headers(jwt: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {jwt}"}


def unique_name(prefix: str) -> str:
    return f"{prefix}-{int(time.time() * 1000)}"


def assert_expected_failure(response: APIResponse, expected_statuses: tuple[int, ...]) -> None:
    assert not response.ok, (
        "Request unexpectedly succeeded. "
        f"status={response.status} body={response.text()}"
    )
    assert response.status in expected_statuses, (
        f"Unexpected status={response.status}, expected one of={expected_statuses}. "
        f"body={response.text()}"
    )


def safe_delete(
    api: APIRequestContext,
    url: str,
    headers: dict[str, str] | None = None,
    allowed_statuses: tuple[int, ...] = (200, 204, 404),
) -> None:
    response = api.delete(url, headers=headers)
    assert response.status in allowed_statuses, (
        f"Cleanup request failed. url={url} status={response.status} body={response.text()}"
    )

from playwright.sync_api import APIRequestContext

from test_support.api import (
    assert_expected_failure,
    bearer_headers,
    login_super_admin,
    unique_name,
)
from test_support.login import DEFAULT_LOGIN_EMAIL


def test_super_admin_login_returns_jwt_and_allows_protected_endpoint(
    api_context: APIRequestContext,
) -> None:
    jwt = login_super_admin(api_context)

    response = api_context.get(
        "/api/v1/tenants?page=1&limit=25",
        headers=bearer_headers(jwt),
    )
    assert response.ok, (
        "Authenticated request failed. "
        f"status={response.status} body={response.text()}"
    )

    payload = response.json()
    assert isinstance(payload.get("tenants"), list), f"Unexpected payload: {payload}"


def test_protected_endpoint_rejects_request_without_jwt(api_context: APIRequestContext) -> None:
    response = api_context.get("/api/v1/tenants?page=1&limit=25")
    assert_expected_failure(response, expected_statuses=(401, 403))


def test_login_with_wrong_password_is_rejected(api_context: APIRequestContext) -> None:
    response = api_context.post(
        "/api/v1/auth/login",
        data={
            "email": DEFAULT_LOGIN_EMAIL,
            "password": "wrongpass123",
        },
    )
    assert_expected_failure(response, expected_statuses=(400, 401, 404))


def test_authenticated_user_can_logout(api_context: APIRequestContext) -> None:
    jwt = login_super_admin(api_context)

    logout_response = api_context.post(
        "/api/v1/auth/logout",
        headers=bearer_headers(jwt),
        data={},
    )
    assert logout_response.ok, (
        "Logout failed. "
        f"status={logout_response.status} body={logout_response.text()}"
    )

    payload = logout_response.json()
    assert payload.get("result") == "ok", f"Unexpected logout payload: {payload}"


def test_change_password_requires_authentication(api_context: APIRequestContext) -> None:
    response = api_context.post(
        "/api/v1/auth/change_password",
        data={
            "old_password": "old-password-123",
            "new_password": "new-password-123",
        },
    )
    assert_expected_failure(response, expected_statuses=(401, 403))


def test_change_password_with_wrong_old_password_is_rejected(
    api_context: APIRequestContext,
    super_admin_jwt: str,
) -> None:
    response = api_context.post(
        "/api/v1/auth/change_password",
        headers=bearer_headers(super_admin_jwt),
        data={
            "old_password": "definitely-wrong-old-password",
            "new_password": "new-password-123",
        },
    )
    assert_expected_failure(response, expected_statuses=(400, 404))


def test_forgot_password_unknown_email_is_rejected(api_context: APIRequestContext) -> None:
    response = api_context.post(
        "/api/v1/auth/forgot_password/request",
        data={
            "email": f"{unique_name('unknown-auth-user')}@example.com",
        },
    )
    assert_expected_failure(response, expected_statuses=(400, 404))


def test_verify_forgot_password_with_invalid_token_is_rejected(
    api_context: APIRequestContext,
) -> None:
    response = api_context.post(
        "/api/v1/auth/forgot_password/verify_token",
        data={
            "token": "invalid-or-expired-token",
        },
    )
    assert_expected_failure(response, expected_statuses=(400, 404))

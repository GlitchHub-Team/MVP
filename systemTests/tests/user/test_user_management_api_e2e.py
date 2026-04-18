from uuid import uuid4

from playwright.sync_api import APIRequestContext

from test_support.api import (
    assert_expected_failure,
    bearer_headers,
    safe_delete,
    unique_name,
)


def test_super_admin_can_manage_tenant_user_lifecycle(
    api_context: APIRequestContext,
    super_admin_jwt: str,
) -> None:
    headers = bearer_headers(super_admin_jwt)
    tenant_id: str | None = None
    user_id: int | None = None

    try:
        tenant_name = unique_name("e2e-tenant-user")
        create_tenant_response = api_context.post(
            "/api/v1/tenant",
            headers=headers,
            data={
                "tenant_name": tenant_name,
                "can_impersonate": True,
            },
        )
        assert create_tenant_response.ok, (
            "Tenant creation failed. "
            f"status={create_tenant_response.status} body={create_tenant_response.text()}"
        )

        tenant_id = create_tenant_response.json().get("tenant_id")
        assert isinstance(tenant_id, str) and tenant_id

        user_email = f"{unique_name('tenant-user')}@example.com"
        user_name = "E2E Tenant User"
        create_user_response = api_context.post(
            f"/api/v1/tenant/{tenant_id}/tenant_user",
            headers=headers,
            data={
                "email": user_email,
                "username": user_name,
            },
        )
        assert create_user_response.ok, (
            "Tenant user creation failed. "
            f"status={create_user_response.status} body={create_user_response.text()}"
        )

        created_user_payload = create_user_response.json()
        user_id = created_user_payload.get("user_id")
        assert isinstance(user_id, int), f"Unexpected create user payload: {created_user_payload}"
        assert created_user_payload.get("tenant_id") == tenant_id
        assert created_user_payload.get("email") == user_email
        assert created_user_payload.get("username") == user_name
        assert created_user_payload.get("user_role") == "tenant_user"

        get_user_response = api_context.get(
            f"/api/v1/tenant/{tenant_id}/tenant_user/{user_id}",
            headers=headers,
        )
        assert get_user_response.ok, (
            "Get tenant user failed. "
            f"status={get_user_response.status} body={get_user_response.text()}"
        )
        get_user_payload = get_user_response.json()
        assert get_user_payload.get("user_id") == user_id
        assert get_user_payload.get("email") == user_email

        list_users_response = api_context.get(
            f"/api/v1/tenant/{tenant_id}/tenant_users?page=1&limit=200",
            headers=headers,
        )
        assert list_users_response.ok, (
            "Get tenant users list failed. "
            f"status={list_users_response.status} body={list_users_response.text()}"
        )
        list_users_payload = list_users_response.json()
        user_ids = {user.get("user_id") for user in list_users_payload.get("users", [])}
        assert user_id in user_ids

        delete_user_response = api_context.delete(
            f"/api/v1/tenant/{tenant_id}/tenant_user/{user_id}",
            headers=headers,
        )
        assert delete_user_response.ok, (
            "Delete tenant user failed. "
            f"status={delete_user_response.status} body={delete_user_response.text()}"
        )
        user_id = None

        get_deleted_user_response = api_context.get(
            f"/api/v1/tenant/{tenant_id}/tenant_user/{created_user_payload['user_id']}",
            headers=headers,
        )
        assert_expected_failure(get_deleted_user_response, expected_statuses=(400, 404))

    finally:
        if user_id is not None and tenant_id is not None:
            safe_delete(
                api_context,
                f"/api/v1/tenant/{tenant_id}/tenant_user/{user_id}",
                headers=headers,
            )
        if tenant_id is not None:
            safe_delete(api_context, f"/api/v1/tenant/{tenant_id}", headers=headers)



def test_create_tenant_admin_requires_authentication(api_context: APIRequestContext) -> None:
    response = api_context.post(
        f"/api/v1/tenant/{uuid4()}/tenant_admin",
        data={
            "email": f"{unique_name('no-auth-tenant-admin')}@example.com",
            "username": "No Auth Admin",
        },
    )
    assert_expected_failure(response, expected_statuses=(401, 403))

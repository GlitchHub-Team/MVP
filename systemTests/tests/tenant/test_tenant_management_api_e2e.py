from playwright.sync_api import APIRequestContext

from test_support.api import (
    assert_expected_failure,
    bearer_headers,
    safe_delete,
    unique_name,
)


def test_super_admin_can_manage_tenant_lifecycle(
    api_context: APIRequestContext,
    super_admin_jwt: str,
) -> None:
    headers = bearer_headers(super_admin_jwt)
    tenant_id: str | None = None

    try:
        tenant_name = unique_name("e2e-tenant")

        create_response = api_context.post(
            "/api/v1/tenant",
            headers=headers,
            data={
                "tenant_name": tenant_name,
                "can_impersonate": True,
            },
        )
        assert create_response.ok, (
            "Tenant creation failed. "
            f"status={create_response.status} body={create_response.text()}"
        )

        created_payload = create_response.json()
        tenant_id = created_payload.get("tenant_id")
        assert isinstance(tenant_id, str) and tenant_id, f"Unexpected payload: {created_payload}"
        assert created_payload.get("tenant_name") == tenant_name
        assert created_payload.get("can_impersonate") is True

        get_response = api_context.get(f"/api/v1/tenant/{tenant_id}", headers=headers)
        assert get_response.ok, (
            "Get tenant failed. "
            f"status={get_response.status} body={get_response.text()}"
        )
        get_payload = get_response.json()
        assert get_payload.get("tenant_id") == tenant_id
        assert get_payload.get("tenant_name") == tenant_name

        list_response = api_context.get("/api/v1/tenants?page=1&limit=200", headers=headers)
        assert list_response.ok, (
            "Get tenants list failed. "
            f"status={list_response.status} body={list_response.text()}"
        )
        list_payload = list_response.json()
        tenant_ids = {tenant.get("tenant_id") for tenant in list_payload.get("tenants", [])}
        assert tenant_id in tenant_ids

        delete_response = api_context.delete(f"/api/v1/tenant/{tenant_id}", headers=headers)
        assert delete_response.ok, (
            "Delete tenant failed. "
            f"status={delete_response.status} body={delete_response.text()}"
        )
        tenant_id = None

    finally:
        if tenant_id is not None:
            safe_delete(api_context, f"/api/v1/tenant/{tenant_id}", headers=headers)


def test_duplicate_tenant_name_is_rejected(
    api_context: APIRequestContext,
    super_admin_jwt: str,
) -> None:
    headers = bearer_headers(super_admin_jwt)
    tenant_id: str | None = None

    try:
        tenant_name = unique_name("e2e-tenant-dup")

        first_create = api_context.post(
            "/api/v1/tenant",
            headers=headers,
            data={
                "tenant_name": tenant_name,
                "can_impersonate": False,
            },
        )
        assert first_create.ok, (
            "First tenant creation failed. "
            f"status={first_create.status} body={first_create.text()}"
        )
        tenant_id = first_create.json().get("tenant_id")
        assert isinstance(tenant_id, str) and tenant_id

        duplicate_create = api_context.post(
            "/api/v1/tenant",
            headers=headers,
            data={
                "tenant_name": tenant_name,
                "can_impersonate": True,
            },
        )
        assert_expected_failure(duplicate_create, expected_statuses=(400, 409))

    finally:
        if tenant_id is not None:
            safe_delete(api_context, f"/api/v1/tenant/{tenant_id}", headers=headers)

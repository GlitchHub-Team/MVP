from uuid import uuid4

from playwright.sync_api import APIRequestContext

from test_support.api import (
    assert_expected_failure,
    bearer_headers,
    safe_delete,
    unique_name,
)


def _create_tenant(
    api_context: APIRequestContext,
    headers: dict[str, str],
    tenant_name: str,
    can_impersonate: bool,
) -> dict:
    response = api_context.post(
        "/api/v1/tenant",
        headers=headers,
        data={
            "tenant_name": tenant_name,
            "can_impersonate": can_impersonate,
        },
    )
    assert response.ok, (
        "Tenant creation failed. "
        f"status={response.status} body={response.text()}"
    )
    payload = response.json()
    tenant_id = payload.get("tenant_id")
    assert isinstance(tenant_id, str) and tenant_id, f"Unexpected create payload: {payload}"
    return payload


def test_super_admin_can_create_many_tenants_and_read_them_back(
    api_context: APIRequestContext,
    super_admin_jwt: str,
) -> None:
    headers = bearer_headers(super_admin_jwt)
    created_tenants: list[str] = []

    try:
        expected_by_id: dict[str, tuple[str, bool]] = {}
        for index in range(8):
            tenant_name = unique_name(f"e2e-bulk-tenant-{index}")
            can_impersonate = index % 2 == 0
            created = _create_tenant(api_context, headers, tenant_name, can_impersonate)
            tenant_id = created["tenant_id"]

            created_tenants.append(tenant_id)
            expected_by_id[tenant_id] = (tenant_name, can_impersonate)

        for tenant_id, (expected_name, expected_impersonate) in expected_by_id.items():
            get_response = api_context.get(f"/api/v1/tenant/{tenant_id}", headers=headers)
            assert get_response.ok, (
                "Get tenant failed. "
                f"tenant_id={tenant_id} status={get_response.status} body={get_response.text()}"
            )
            payload = get_response.json()
            assert payload.get("tenant_id") == tenant_id
            assert payload.get("tenant_name") == expected_name
            assert payload.get("can_impersonate") is expected_impersonate

    finally:
        for tenant_id in reversed(created_tenants):
            safe_delete(api_context, f"/api/v1/tenant/{tenant_id}", headers=headers)


def test_public_all_tenants_lists_newly_created_tenants(
    api_context: APIRequestContext,
    super_admin_jwt: str,
) -> None:
    headers = bearer_headers(super_admin_jwt)
    created_tenants: list[tuple[str, str]] = []

    try:
        for index in range(3):
            tenant_name = unique_name(f"e2e-public-tenant-{index}")
            created = _create_tenant(api_context, headers, tenant_name, can_impersonate=False)
            created_tenants.append((created["tenant_id"], tenant_name))

        all_tenants_response = api_context.get("/api/v1/all_tenants")
        assert all_tenants_response.ok, (
            "Get all tenants failed. "
            f"status={all_tenants_response.status} body={all_tenants_response.text()}"
        )
        payload = all_tenants_response.json()
        tenants = payload.get("tenants", [])
        assert isinstance(tenants, list), f"Unexpected all_tenants payload: {payload}"

        by_id = {tenant.get("tenant_id"): tenant.get("tenant_name") for tenant in tenants}
        for tenant_id, tenant_name in created_tenants:
            assert by_id.get(tenant_id) == tenant_name

    finally:
        for tenant_id, _ in reversed(created_tenants):
            safe_delete(api_context, f"/api/v1/tenant/{tenant_id}", headers=headers)


def test_deleted_tenant_disappears_from_public_all_tenants(
    api_context: APIRequestContext,
    super_admin_jwt: str,
) -> None:
    headers = bearer_headers(super_admin_jwt)

    tenant_name = unique_name("e2e-public-delete")
    created = _create_tenant(api_context, headers, tenant_name, can_impersonate=True)
    tenant_id = created["tenant_id"]

    before_delete_response = api_context.get("/api/v1/all_tenants")
    assert before_delete_response.ok
    before_ids = {tenant.get("tenant_id") for tenant in before_delete_response.json().get("tenants", [])}
    assert tenant_id in before_ids

    delete_response = api_context.delete(f"/api/v1/tenant/{tenant_id}", headers=headers)
    assert delete_response.ok, (
        "Delete tenant failed. "
        f"status={delete_response.status} body={delete_response.text()}"
    )

    after_delete_response = api_context.get("/api/v1/all_tenants")
    assert after_delete_response.ok
    after_ids = {tenant.get("tenant_id") for tenant in after_delete_response.json().get("tenants", [])}
    assert tenant_id not in after_ids


def test_tenant_list_endpoint_has_valid_pagination_contract(
    api_context: APIRequestContext,
    super_admin_jwt: str,
) -> None:
    headers = bearer_headers(super_admin_jwt)

    page_one = api_context.get("/api/v1/tenants?page=1&limit=5", headers=headers)
    assert page_one.ok, f"List page 1 failed. status={page_one.status} body={page_one.text()}"
    payload_one = page_one.json()
    tenants_one = payload_one.get("tenants")
    count_one = payload_one.get("count")
    total_one = payload_one.get("total")

    assert isinstance(tenants_one, list), f"Unexpected payload: {payload_one}"
    assert isinstance(count_one, int)
    assert isinstance(total_one, int)
    assert 0 <= count_one <= 5
    assert total_one >= count_one

    page_two = api_context.get("/api/v1/tenants?page=2&limit=5", headers=headers)
    assert page_two.ok, f"List page 2 failed. status={page_two.status} body={page_two.text()}"
    payload_two = page_two.json()
    tenants_two = payload_two.get("tenants")
    count_two = payload_two.get("count")
    total_two = payload_two.get("total")

    assert isinstance(count_two, int), f"Unexpected payload: {payload_two}"
    assert isinstance(total_two, int), f"Unexpected payload: {payload_two}"
    if count_two == 0:
        assert tenants_two in (None, []), f"Unexpected payload for empty page: {payload_two}"
    else:
        assert isinstance(tenants_two, list), f"Unexpected payload: {payload_two}"


def test_create_tenant_requires_authentication(api_context: APIRequestContext) -> None:
    response = api_context.post(
        "/api/v1/tenant",
        data={
            "tenant_name": unique_name("e2e-no-auth-tenant"),
            "can_impersonate": True,
        },
    )
    assert_expected_failure(response, expected_statuses=(401, 403))


def test_create_tenant_rejects_invalid_payload(
    api_context: APIRequestContext,
    super_admin_jwt: str,
) -> None:
    headers = bearer_headers(super_admin_jwt)

    missing_name = api_context.post(
        "/api/v1/tenant",
        headers=headers,
        data={
            "can_impersonate": True,
        },
    )
    assert_expected_failure(missing_name, expected_statuses=(400, 422))

    invalid_flag_type = api_context.post(
        "/api/v1/tenant",
        headers=headers,
        data={
            "tenant_name": unique_name("e2e-invalid-tenant"),
            "can_impersonate": "yes",
        },
    )
    assert_expected_failure(invalid_flag_type, expected_statuses=(400, 422))


def test_get_unknown_tenant_returns_not_found(
    api_context: APIRequestContext,
    super_admin_jwt: str,
) -> None:
    headers = bearer_headers(super_admin_jwt)
    unknown_tenant_id = str(uuid4())

    response = api_context.get(f"/api/v1/tenant/{unknown_tenant_id}", headers=headers)
    assert_expected_failure(response, expected_statuses=(400, 404))


def test_delete_unknown_tenant_returns_not_found(
    api_context: APIRequestContext,
    super_admin_jwt: str,
) -> None:
    headers = bearer_headers(super_admin_jwt)
    unknown_tenant_id = str(uuid4())

    response = api_context.delete(f"/api/v1/tenant/{unknown_tenant_id}", headers=headers)
    assert_expected_failure(response, expected_statuses=(400, 404))

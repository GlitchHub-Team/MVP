from playwright.sync_api import APIRequestContext

from test_support.api import (
    assert_expected_failure,
    bearer_headers,
    safe_delete,
    unique_name,
)


def test_super_admin_can_manage_sensor_lifecycle(
    api_context: APIRequestContext,
    super_admin_jwt: str,
) -> None:
    headers = bearer_headers(super_admin_jwt)
    gateway_id: str | None = None
    sensor_id: str | None = None

    try:
        gateway_name = unique_name("e2e-gw-for-sensor")
        create_gateway_response = api_context.post(
            "/api/v1/gateway",
            headers=headers,
            data={
                "name": gateway_name,
                "interval": 2000,
            },
        )
        assert create_gateway_response.ok, (
            "Gateway bootstrap for sensor test failed. "
            f"status={create_gateway_response.status} body={create_gateway_response.text()}"
        )

        gateway_id = create_gateway_response.json().get("gateway_id")
        assert isinstance(gateway_id, str) and gateway_id

        sensor_name = unique_name("e2e-sensor")
        create_sensor_response = api_context.post(
            "/api/v1/sensor",
            headers=headers,
            data={
                "sensor_name": sensor_name,
                "data_interval": 1200,
                "profile": "heart_rate",
                "gateway_id": gateway_id,
            },
        )
        assert create_sensor_response.ok, (
            "Sensor creation failed. "
            f"status={create_sensor_response.status} body={create_sensor_response.text()}"
        )

        created_sensor_payload = create_sensor_response.json()
        sensor_id = created_sensor_payload.get("sensor_id")
        assert isinstance(sensor_id, str) and sensor_id, (
            f"Unexpected sensor payload: {created_sensor_payload}"
        )
        assert created_sensor_payload.get("sensor_name") == sensor_name
        assert created_sensor_payload.get("gateway_id") == gateway_id
        assert created_sensor_payload.get("status") == "active"

        get_sensor_response = api_context.get(f"/api/v1/sensor/{sensor_id}", headers=headers)
        assert get_sensor_response.ok, (
            "Get sensor failed. "
            f"status={get_sensor_response.status} body={get_sensor_response.text()}"
        )
        assert get_sensor_response.json().get("sensor_id") == sensor_id

        list_sensors_response = api_context.get(
            f"/api/v1/gateway/{gateway_id}/sensors?page=1&limit=200",
            headers=headers,
        )
        assert list_sensors_response.ok, (
            "List sensors by gateway failed. "
            f"status={list_sensors_response.status} body={list_sensors_response.text()}"
        )
        list_sensors_payload = list_sensors_response.json()
        sensor_ids = {sensor.get("sensor_id") for sensor in list_sensors_payload.get("sensors", [])}
        assert sensor_id in sensor_ids

        interrupt_response = api_context.post(
            f"/api/v1/sensor/{sensor_id}/interrupt",
            headers=headers,
            data={},
        )
        assert interrupt_response.ok, (
            "Interrupt sensor failed. "
            f"status={interrupt_response.status} body={interrupt_response.text()}"
        )

        after_interrupt = api_context.get(f"/api/v1/sensor/{sensor_id}", headers=headers)
        assert after_interrupt.ok
        assert after_interrupt.json().get("status") == "inactive"

        resume_response = api_context.post(
            f"/api/v1/sensor/{sensor_id}/resume",
            headers=headers,
            data={},
        )
        assert resume_response.ok, (
            "Resume sensor failed. "
            f"status={resume_response.status} body={resume_response.text()}"
        )

        after_resume = api_context.get(f"/api/v1/sensor/{sensor_id}", headers=headers)
        assert after_resume.ok
        assert after_resume.json().get("status") == "active"

        delete_sensor_response = api_context.delete(f"/api/v1/sensor/{sensor_id}", headers=headers)
        assert delete_sensor_response.ok, (
            "Delete sensor failed. "
            f"status={delete_sensor_response.status} body={delete_sensor_response.text()}"
        )
        sensor_id = None

        get_deleted_sensor_response = api_context.get(
            f"/api/v1/sensor/{created_sensor_payload['sensor_id']}",
            headers=headers,
        )
        assert_expected_failure(get_deleted_sensor_response, expected_statuses=(400, 404))

    finally:
        if sensor_id is not None:
            safe_delete(api_context, f"/api/v1/sensor/{sensor_id}", headers=headers)
        if gateway_id is not None:
            safe_delete(api_context, f"/api/v1/gateway/{gateway_id}", headers=headers)

import pytest

from test_support.connections import cloud_db_connection, nats_connection, sensor_db_connection


def test_can_connect_to_nats() -> None:
    try:
        with nats_connection() as client:
            assert client.is_connected
    except RuntimeError as err:
        pytest.skip(str(err))


def test_can_connect_to_sensor_db() -> None:
    try:
        with sensor_db_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                assert cursor.fetchone() == (1,)
    except RuntimeError as err:
        pytest.skip(str(err))


def test_can_connect_to_cloud_db() -> None:
    try:
        with cloud_db_connection() as connection:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                assert cursor.fetchone() == (1,)
    except RuntimeError as err:
        pytest.skip(str(err))

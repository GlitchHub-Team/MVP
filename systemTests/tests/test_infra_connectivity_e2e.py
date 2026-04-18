from test_support.connections import cloud_db_connection, nats_connection, sensor_db_connection


def test_can_connect_to_nats() -> None:
    with nats_connection() as client:
        assert client.is_connected


def test_can_connect_to_sensor_db() -> None:
    with sensor_db_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            assert cursor.fetchone() == (1,)


def test_can_connect_to_cloud_db() -> None:
    with cloud_db_connection() as connection:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            assert cursor.fetchone() == (1,)

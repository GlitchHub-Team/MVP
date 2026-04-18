import asyncio
import os
import ssl
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

try:
    import psycopg
except ModuleNotFoundError:  # pragma: no cover - depends on environment setup
    psycopg = None  # type: ignore[assignment]

PsycopgConnection = Any
if psycopg is not None:
    PsycopgConnection = psycopg.Connection  # type: ignore[attr-defined]

try:
    from nats.aio.client import Client as NATS
except ModuleNotFoundError:  # pragma: no cover - depends on environment setup
    NATS = Any  # type: ignore[misc,assignment]


def _require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def _require_psycopg() -> None:
    if psycopg is None:
        raise RuntimeError(
            "Missing Python dependency: psycopg. Install system test dependencies first."
        )


def _require_nats_client() -> None:
    if NATS is Any:
        raise RuntimeError(
            "Missing Python dependency: nats-py. Install system test dependencies first."
        )


def _resolve_file(path_value: str) -> str:
    path = Path(path_value)
    if path.exists():
        return str(path)

    app_path = Path("/app") / path_value
    if app_path.exists():
        return str(app_path)

    raise RuntimeError(f"File not found: {path_value}")


def nats_url() -> str:
    host = _require_env("NATS_HOST")
    port = _require_env("NATS_PORT")
    return f"nats://{host}:{port}"


def _nats_ssl_context(ca_path: str) -> ssl.SSLContext:
    context = ssl.create_default_context(cafile=ca_path)
    context.check_hostname = False
    return context


async def connect_nats(
    creds_path: str = "admin_test.creds",
    ca_path: str = "ca.pem",
    timeout_seconds: float = 5.0,
) -> NATS:
    _require_nats_client()
    resolved_creds = _resolve_file(creds_path)
    resolved_ca = _resolve_file(ca_path)

    client = NATS()
    await client.connect(
        servers=[nats_url()],
        user_credentials=resolved_creds,
        tls=_nats_ssl_context(resolved_ca),
        connect_timeout=timeout_seconds,
        allow_reconnect=False,
        max_reconnect_attempts=0,
        name="system-tests",
    )
    return client


@contextmanager
def sensor_db_connection() -> Iterator[PsycopgConnection]:
    _require_psycopg()
    connection = psycopg.connect(
        host=_require_env("POSTGRES_HOST"),
        port=int(_require_env("POSTGRES_PORT")),
        dbname=_require_env("POSTGRES_DB"),
        user=_require_env("POSTGRES_USER"),
        password=_require_env("POSTGRES_PASSWORD"),
        connect_timeout=5,
    )
    try:
        yield connection
    finally:
        connection.close()


@contextmanager
def cloud_db_connection() -> Iterator[PsycopgConnection]:
    _require_psycopg()
    connection = psycopg.connect(
        host=_require_env("CLOUD_POSTGRES_HOST"),
        port=int(_require_env("CLOUD_POSTGRES_PORT")),
        dbname=_require_env("CLOUD_POSTGRES_DB"),
        user=_require_env("CLOUD_POSTGRES_USER"),
        password=_require_env("CLOUD_POSTGRES_PASSWORD"),
        connect_timeout=5,
    )
    try:
        yield connection
    finally:
        connection.close()


@contextmanager
def nats_connection(
    creds_path: str = "admin_test.creds",
    ca_path: str = "ca.pem",
    timeout_seconds: float = 5.0,
) -> Iterator[NATS]:
    loop = asyncio.new_event_loop()
    client = loop.run_until_complete(
        connect_nats(
            creds_path=creds_path,
            ca_path=ca_path,
            timeout_seconds=timeout_seconds,
        )
    )
    try:
        yield client
    finally:
        loop.run_until_complete(client.close())
        loop.close()

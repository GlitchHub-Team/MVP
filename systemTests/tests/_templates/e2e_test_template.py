"""Template for new E2E system tests.

Copy this file into a domain folder and rename it as `test_<feature>_e2e.py`.
"""

import os

import pytest


def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        pytest.skip(f"Missing env var: {name}")
    return value


def test_template_placeholder() -> None:
    # Replace with real steps and assertions.
    app_url = require_env("APP_URL")
    assert app_url

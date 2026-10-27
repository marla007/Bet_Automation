"""Fixtures shared by UI and API tests."""

import pytest

import config


@pytest.fixture(scope="session", autouse=True)
def require_user_id():
    """Every endpoint needs a user id, so skip clearly instead of failing with 401."""
    if not config.USER_ID:
        pytest.skip("USER_ID is not set. Copy .env to .env and fill it in.")

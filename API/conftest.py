"""API fixtures: client, clean balance and test data."""

import pytest

import config
from API.clients.betting_api_client import BettingApiClient
from common.test_data import pick_past_match, pick_upcoming_match


@pytest.fixture(scope="session")
def api():
    client = BettingApiClient(config.BASE_URL, config.USER_ID)
    yield client
    client.close()


@pytest.fixture
def start_balance(api):
    """Reset the balance before the test and return the STORED value (GET /api/balance).

    The reset response is not used as the baseline because it does not match the
    stored balance (BUG-02). The balance is reset again after the test, so no test
    leaves money spent for the next one.
    """
    api.reset_balance().raise_for_status()
    yield api.get_balance().json()["balance"]
    api.reset_balance()


@pytest.fixture(scope="session")
def match(api):
    """First upcoming match from the live catalog (see common/test_data.py)."""
    return pick_upcoming_match(api.get_matches().json())


@pytest.fixture(scope="session")
def past_match(api):
    """A match whose kickoff date is before today; the test is skipped if there is none."""
    past = pick_past_match(api.get_matches().json())
    if past is None:
        pytest.skip("No past matches in the catalog")
    return past

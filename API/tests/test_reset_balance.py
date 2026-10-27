"""API test: resetting the balance restores the documented starting balance.

Why this test:
    Every other test depends on a reliable reset. The spec (§5.3) says the reset response
    and the stored balance must be consistent, and both must equal €125.50. If the reset
    lies, every test that trusts it starts from the wrong data.
"""

import pytest

from common.soft_assert import KnownBugFailure, SoftAssert

INITIAL_BALANCE = 125.50


@pytest.mark.xfail(
    reason="BUG-02: reset response says 125.5 but the stored balance is 120",
    raises=KnownBugFailure,
    strict=True,
)
def test_reset_restores_initial_balance(api):
    check = SoftAssert()

    response = api.reset_balance()
    stored_balance = api.get_balance().json()["balance"]

    check.equal(response.status_code, 200, "Reset: status code")
    check.equal(response.json().get("balance"), INITIAL_BALANCE, "Reset: balance in response")
    check.equal(stored_balance, INITIAL_BALANCE, "BUG-02 Reset: stored balance")
    check.assert_all(known_bugs=("BUG-02",))

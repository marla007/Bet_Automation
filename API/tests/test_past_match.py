"""API test: the server rejects bets on matches that have already been played.

Why this test:
    The product is for pre-match bets on upcoming matches only. Accepting a bet on a match
    whose result is already known is a direct financial loss and a fraud risk, so this is a
    Critical rule. The API is the real gatekeeper: even if the UI hid past matches, anyone
    could still send the request directly.
"""

import pytest

from common.soft_assert import KnownBugFailure, SoftAssert

STAKE = 1.00


@pytest.mark.xfail(
    reason="BUG-06: a bet on a past match is accepted (200)",
    raises=KnownBugFailure,
    strict=True,
)
def test_bet_on_past_match_is_rejected(api, past_match, start_balance):
    check = SoftAssert()
    label = f"BUG-06 Bet on past match {past_match['id']} ({past_match['kickoffDate']})"

    response = api.place_bet({"matchId": past_match["id"], "selection": "HOME", "stake": STAKE})
    balance_after = api.get_balance().json()["balance"]

    check.equal(response.status_code, 422, f"{label}: status code")
    check.equal(balance_after, start_balance, f"{label}: balance must not change")
    check.assert_all(known_bugs=("BUG-06",))

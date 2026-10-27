"""API test: stake limits are enforced by the server.

Why this test:
    The stake must be between €1.00 and €100.00 with at most 2 decimals. This is a money
    and regulatory rule, and the API is where it really has to be enforced: anyone can
    call the API directly and skip the UI checks. Boundary values are where bugs usually
    hide, and these checks are fast and stable at the API level.
"""

import pytest

from common.soft_assert import KnownBugFailure, SoftAssert

MIN_STAKE = 1.00
KNOWN_BUGS = ("BUG-01",)


@pytest.mark.parametrize(
    "stake, error, label",
    [
        pytest.param(0.99, "invalid_stake_min", "Just below minimum", id="just-below-min"),
        pytest.param(0.10, "invalid_stake_min", "Far below minimum", id="far-below-min"),
        pytest.param(
            -10,
            "invalid_stake_min",
            "BUG-01 Negative stake",
            id="negative",
            marks=pytest.mark.xfail(
                reason="BUG-01: negative stake is accepted (200) and increases the balance",
                raises=KnownBugFailure,
                strict=True,
            ),
        ),
        pytest.param(100.01, "invalid_stake_max", "Just above maximum", id="just-above-max"),
        pytest.param(5.555, "invalid_stake_precision", "Three decimals", id="three-decimals"),
        pytest.param("abc", "invalid_stake_type", "Text stake", id="text"),
        pytest.param("", "invalid_stake_type", "Empty stake", id="empty-string"),
    ],
)
def test_invalid_stake_is_rejected(api, match, start_balance, stake, error, label):
    check = SoftAssert()

    response = api.place_bet({"matchId": match["id"], "selection": "HOME", "stake": stake})
    balance_after = api.get_balance().json()["balance"]

    check.equal(response.status_code, 422, f"{label}: status code")
    check.equal(response.json().get("error"), error, f"{label}: error code")
    check.equal(balance_after, start_balance, f"{label}: balance must not change")
    check.assert_all(known_bugs=KNOWN_BUGS)


def test_minimum_stake_is_accepted(api, match, start_balance):
    """€1.00 is the lowest allowed stake: it must be accepted and deducted exactly once."""
    check = SoftAssert()
    expected_payout = round(MIN_STAKE * match["odds"]["home"], 2)
    expected_balance = round(start_balance - MIN_STAKE, 2)

    response = api.place_bet({"matchId": match["id"], "selection": "HOME", "stake": MIN_STAKE})
    body = response.json()

    check.equal(response.status_code, 200, "Minimum stake: status code")
    check.equal(body.get("payout"), expected_payout, "Minimum stake: payout")
    check.equal(body.get("balance"), expected_balance, "Minimum stake: balance in response")
    check.equal(
        api.get_balance().json()["balance"], expected_balance, "Minimum stake: stored balance"
    )
    check.assert_all()

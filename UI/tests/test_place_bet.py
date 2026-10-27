"""E2E UI test: place a single bet and verify the receipt and balance.

Why this test:
    Placing a bet is the most critical user journey: it is where the company makes money,
    and it goes through every part of the app (match list → bet slip → API → receipt →
    balance). A wrong payout, wrong teams or a wrong balance on the receipt directly
    misleads the customer and causes disputes, so this flow must be checked on every release.

Soft assertions are used after placement, so one run reports every receipt and balance
problem at once instead of stopping at the first one.
"""

import pytest

import config
from common.soft_assert import KnownBugFailure, SoftAssert

STAKE = 10.00
KNOWN_BUGS = ("BUG-03", "BUG-04", "BUG-05")


@pytest.mark.xfail(
    reason=(
        "Known bugs: BUG-03 receipt shows teams reversed, "
        "BUG-04 receipt payout is stake x 2, "
        "BUG-05 balance not updated after a bet"
    ),
    raises=KnownBugFailure,  # any other failure is reported as FAILED
    strict=True,
)
def test_place_single_bet(betting_page, api_session, match):
    # Every failed check takes its own screenshot, named after the check (e.g. BUG-03_...)
    check = SoftAssert(on_fail=betting_page.take_screenshot)
    odds = match["odds"]["home"]
    teams = f"{match['homeTeam']} vs {match['awayTeam']}"
    expected_payout = round(STAKE * odds, 2)

    # Open the app and note the starting balance
    betting_page.open(config.USER_ID)
    start_balance = betting_page.get_header_balance()
    expected_balance = round(start_balance - STAKE, 2)
    assert betting_page.get_odds(match["id"], "home") == odds

    # Select the home win and enter a stake (hard asserts: the rest is meaningless if these fail)
    bet_slip = betting_page.select_odds(match["id"], "home")
    assert bet_slip.get_selection_teams() == teams
    bet_slip.enter_stake(f"{STAKE:.2f}")
    assert bet_slip.get_total_stake() == STAKE
    assert bet_slip.get_potential_payout() == expected_payout

    # Place the bet and wait for the result
    bet_slip.place_bet()
    assert betting_page.wait_for_bet_result() == "success", "Error modal was shown"

    # The receipt must match what the user saw before placing (soft: collect every mismatch)
    receipt = betting_page.receipt
    check.true(receipt.get_bet_id(), "Receipt: bet ID is missing")
    check.equal(receipt.get_match(), teams, "BUG-03 Receipt teams (home first)")
    check.equal(receipt.get_stake(), STAKE, "Receipt stake")
    check.equal(receipt.get_odds(), odds, "Receipt odds")
    check.equal(receipt.get_payout(), expected_payout, "BUG-04 Receipt potential payout")
    check.true(receipt.get_placed_at(), "Receipt: placement time is missing")

    # After closing, the slip is empty and the balance is deducted everywhere
    receipt.close()
    bet_slip.wait_until_empty()
    check.equal(
        betting_page.wait_for_header_balance(expected_balance),
        expected_balance,
        "BUG-05 Header balance after bet",
    )
    check.equal(bet_slip.get_balance(), expected_balance, "BUG-05 Bet slip balance after bet")

    check.assert_all(known_bugs=KNOWN_BUGS)

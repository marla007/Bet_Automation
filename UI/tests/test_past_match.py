"""UI test: matches that have already been played cannot be bet on.

Why this test:
    The product is for pre-match bets only. If a past match shows active odds, the user can
    bet on a result that is already known, which is a direct financial loss. The check is
    cheap: it only looks at the match list and places no bet.
"""

import pytest

import config
from common.soft_assert import KnownBugFailure, SoftAssert

SELECTIONS = ("home", "draw", "away")


@pytest.mark.xfail(
    reason="BUG-06: past matches are listed with active odds and accept bets",
    raises=KnownBugFailure,
    strict=True,
)
def test_past_match_cannot_be_bet_on(betting_page, past_match):
    check = SoftAssert(on_fail=betting_page.take_screenshot)
    match_id = past_match["id"]

    betting_page.open(config.USER_ID)

    # Expected: a past match is hidden, or shown without clickable odds
    if betting_page.is_match_shown(match_id):
        clickable = [s for s in SELECTIONS if betting_page.is_odds_enabled(match_id, s)]
        check.equal(
            clickable,
            [],
            f"BUG-06 Past match {match_id} ({past_match['kickoffDate']}): clickable odds",
        )

    check.assert_all(known_bugs=("BUG-06",))

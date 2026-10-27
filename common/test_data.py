"""Test data helpers shared by UI and API tests."""

from datetime import date


def pick_upcoming_match(matches):
    """Return the first match with a kickoff date of today or later.

    The product is for pre-match bets on upcoming matches only. The catalog currently also
    lists past matches as bettable (BUG-06), so if no upcoming match exists the first match
    is used, to keep the other checks running.
    """
    if not matches:
        raise RuntimeError("Match catalog is empty; cannot run bet tests.")
    today = date.today().isoformat()
    upcoming = [match for match in matches if match["kickoffDate"] >= today]
    return (upcoming or matches)[0]


def pick_past_match(matches):
    """Return the first match with a kickoff date before today, or None if there is none."""
    today = date.today().isoformat()
    return next((match for match in matches if match["kickoffDate"] < today), None)

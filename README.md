# Bet_Automation

UI and API test automation for the Sports Betting app, written in Python with Selenium, Pytest and requests. The UI tests use the **Page Object Model (POM)**.

## Project structure

```
Bet_Automation/
├── UI/
│   ├── pages/
│   │   ├── base_page.py           # Common actions: click, type, get_text, get_amount
│   │   ├── betting_page.py        # Main page: balance, odds buttons, bet result
│   │   ├── bet_slip.py            # Bet slip: stake, totals, Place Bet
│   │   └── receipt_modal.py       # Success receipt
│   ├── utils/
│   │   └── waits.py               # General explicit waits (no sleep)
│   ├── tests/
│   │   ├── test_place_bet.py      # E2E test: place a bet, check receipt and balance
│   │   └── test_past_match.py     # Past matches must not offer clickable odds
│   └── conftest.py                # Browser, page fixtures, screenshots on failure
├── API/
│   ├── clients/
│   │   └── betting_api_client.py  # One method per API endpoint
│   ├── tests/
│   │   ├── test_stake_validation.py  # Stake limits (min, max, decimals, type)
│   │   ├── test_reset_balance.py     # Reset restores the starting balance
│   │   └── test_past_match.py        # Bets on past matches must be rejected
│   └── conftest.py                # API client, balance reset, test data
├── common/
│   ├── soft_assert.py             # Soft assertions + known-bug check, shared by UI and API
│   └── test_data.py               # Picks the first upcoming match for the tests
├── docs/
│   ├── TEST_PLAN.md               # Part A: 11 prioritized test scenarios
│   ├── BUG_REPORTS.md             # Execution results: 6 bugs found
│   ├── STRATEGY.md                # Part C: strategy and recommendations
│   └── screenshots/               # Evidence for the bug reports
├── .github/workflows/tests.yml    # CI: runs all tests on GitHub Actions
├── config.py                      # Settings from .env / environment variables
├── conftest.py                    # Skips tests if USER_ID is missing
├── pytest.ini
├── requirements.txt
└── .env.example
```

## How it is organised

- **Page Object Model.** Each page or part of a page is a class that holds its own locators and actions. Tests call methods like `select_odds()` or `enter_stake()` and never touch locators directly.
- **General waits.** `UI/utils/waits.py` holds reusable explicit waits: `visible`, `clickable`, `invisible`, `enabled`, `text_contains`, `attribute_contains`, `any_visible` and `until`.
  - Every page uses them through `self.wait`.
  - Tests can also use them through the `waits` fixture.
  - There is no `time.sleep()`.
- **API client.** `BettingApiClient` wraps each endpoint and returns the raw response, so tests can check status codes and error messages.
- **One assertion standard.** Every test uses `SoftAssert` from `common/`: it checks everything, then reports all failures together. Each check has a label, and checks that hit a known bug start with its ID (`BUG-01 …`), so the report shows exactly which bugs were found.
- **Clean state.** Fixtures reset the balance before and after every test, so tests don't affect each other.
- **Screenshots on failure.** In UI tests, every failed check saves its own screenshot, named after the check (e.g. `BUG-03_Receipt_teams_….png`). A final screenshot of the failed test is also embedded in the HTML report. All are saved to `screenshots/`.

## Known bugs (xfail)

The tests found real bugs in the app ([docs/BUG_REPORTS.md](docs/BUG_REPORTS.md)). Tests that hit a known bug are marked `@pytest.mark.xfail(reason="BUG-xx ...", strict=True)`:

| Test | Bug |
|---|---|
| `test_invalid_stake_is_rejected[negative]` | BUG-01: negative stake accepted and increases the balance |
| `test_reset_restores_initial_balance` | BUG-02: reset says 125.5 but stores 120 |
| `test_place_single_bet` | BUG-03 teams reversed, BUG-04 wrong payout, BUG-05 balance not updated |
| `API: test_bet_on_past_match_is_rejected` | BUG-06: bet on a past match is accepted |
| `UI: test_past_match_cannot_be_bet_on` | BUG-06: past matches have clickable odds |

The mark uses `raises=KnownBugFailure`, and each test passes its bug IDs to `check.assert_all(known_bugs=...)`. So a test counts as an expected failure **only if every failed check belongs to a known bug**.

This means:
- **Known bugs** show as `XFAIL`, and the run stays green.
- **A new bug** shows as `FAILED`, and the run goes red, even inside a test that also has known bugs.
- **A fixed bug** shows as `XPASS`. Because of `strict=True` the run goes red, so the `xfail` mark can be removed.

## Setup

You need Python 3.9+ and Google Chrome.

```bash
cd Bet_Automation
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env             # then put your assigned USER_ID in .env
```

`.env` is in `.gitignore` and is never committed. If `USER_ID` is missing, the tests are skipped with a message.

## Run the tests

```bash
pytest                           # all tests + HTML report
pytest API                       # API tests only
pytest UI                        # UI test only
HEADLESS=false pytest UI         # watch the browser
open reports/report.html         # open the report (macOS)
```

Every run creates `reports/report.html` (one self-contained file, with screenshots).
Expected result on the current app version: **7 passed, 5 xfailed** (the xfails cover the 6 known bugs).

## CI (GitHub Actions)

`.github/workflows/tests.yml` runs on every push to `main`, on every pull request, and manually from the **Actions** tab ("Run workflow").

1. Add your user id as a secret: **Settings → Secrets and variables → Actions → New repository secret**, name `USER_ID`.
2. Push to `main`. The workflow runs the API tests, then the UI tests in headless Chrome.
3. HTML reports and failure screenshots are uploaded as the **`test-results`** artifact of each run.
4. Optional status badge for the top of this README (replace `<your-username>`):
   `![Tests](https://github.com/<your-username>/Bet_Automation/actions/workflows/tests.yml/badge.svg)`

Runs never overlap (`concurrency`), because all tests share one test user and balance.

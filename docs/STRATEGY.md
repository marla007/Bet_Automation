# Strategy & Recommendations

## 1. Why these tests were automated

The test plan has 11 scenarios. The assignment asks for **2 automated tests**, one E2E UI and one API. I chose the two with the **highest money risk** that are also **stable and repeatable** to run, one per layer:

| Role | Test | Scenario |
|---|---|---|
| **Main: E2E UI** | `UI/tests/test_place_bet.py` | TC-01 |
| **Main: API** | `API/tests/test_stake_validation.py` | TC-02 |
| Supporting | `API/tests/test_past_match.py`, `UI/tests/test_past_match.py` | TC-04 |
| Supporting | `API/tests/test_reset_balance.py` | TC-09 |

The supporting tests are small and fast. They cover a Critical rule (no bets on past matches) and the test setup that every other test depends on.

### E2E UI test: place a single bet (TC-01)
`UI/tests/test_place_bet.py`

- **Most critical journey.** Placing a bet is where the business makes money, and it touches every part of the app: match list → bet slip → API → receipt → balance.
- **Catches what only the UI can get wrong.** The receipt and balance are built in the front end, so an API test cannot see these errors. This one test found **3 bugs**: teams reversed on the receipt (BUG-03), payout calculated as stake × 2 (BUG-04), and the balance not updating after a bet (BUG-05).
- **One run, every problem.** Soft assertions after placement list all mismatches together instead of stopping at the first one, and a screenshot is attached to the report.
- **No hardcoded data.** Teams, odds and the expected payout come from the live API, so the test keeps working when the catalog changes.

### API test: stake validation (TC-02)
`API/tests/test_stake_validation.py`

- **The API is the real gatekeeper.** Anyone can call it directly and skip the UI checks, so money rules must hold at this layer.
- **Boundaries are where bugs hide.** One parametrized test covers 7 invalid stakes (below minimum, above maximum, 3 decimals, text, empty, negative) plus the exact minimum. It found **BUG-01**: a negative stake is accepted and *increases* the balance.
- **Fast and stable.** No browser, no timing issues; the whole file runs in seconds, so it can run on every commit.
- **Proves no money moved.** Every rejected case also checks that the stored balance is unchanged.

### Supporting test: reset balance (TC-09)
`API/tests/test_reset_balance.py`

This is not one of the two main tests. TC-09 is only **Medium** priority, because reset is a test-environment feature, not something customers use. I added it as a small **supporting check** for three reasons:

- **Every other test depends on it.** Each test resets the balance before it starts. If the reset is wrong, the money checks in the other tests compare against the wrong starting balance. This test guards the test setup itself: when it fails, other failures may come from bad data rather than real bugs.
- **It costs almost nothing.** One API call and one balance check, no browser, about one second.
- **It found a real bug.** It confirmed **BUG-02**: the reset response says €125.50, but the stored balance is €120.00. Because of this, the test fixtures read the starting balance from `GET /api/balance` instead of trusting the reset response.

### Supporting tests: past matches (TC-04)
`API/tests/test_past_match.py`, `UI/tests/test_past_match.py`

The product is for pre-match bets only, so a bet on a match that has already been played is a Critical risk: the result is already known. Two small tests check this at both layers: the API must reject the bet and keep the balance unchanged, and the UI must not offer clickable odds. Both are fast, and the UI test places no bet. They found **BUG-06**: past matches are listed with active odds and bets on them are accepted.

### Candidates considered but not chosen
| Scenario | Why not first |
|---|---|
| TC-03 Insufficient balance | High value, but its UI part depends on BUG-05 (stale balance) and needs a €100 bet per run. Next in line once BUG-05 is fixed. |
| TC-05 Error modal / Rebet | Needs a forced server failure; there is no reliable way to trigger one yet (see recommendation 2). |
| TC-08 API auth & malformed requests | Valuable and easy to add, but lower money risk than stake rules. Natural next API suite. |

## 2. What stays manual (for now) and why

| Area | Why manual |
|---|---|
| **TC-05 Error modal, Rebet, double charge (409)** | Failure is forced by blocking the request in DevTools; concurrent requests are timing-sensitive. A one-off manual check is more reliable than a flaky automated one until the app supports fault injection. |
| **TC-06 Selection rules** | Quick to check by hand, and the rules may still change (stake clearing on reselection is not defined in the spec). |
| **TC-07 / TC-10 Odds and date filters** | No money involved, visually driven, and expected behaviour is still unclear in the spec (invalid ranges, time zones). Automate once the rules are agreed. |
| **TC-11 Match list layout and labels** | Visual and copy checks need human judgment; a visual-regression tool fits better than assertions. |
| **Exploratory testing** | Most bugs in this project were found by exploring and then confirmed by automation. Exploration itself is not scriptable. |

## 3. Recommendations if the project scales

### 1. Run the tests in CI on every change
The project already includes a GitHub Actions workflow (`.github/workflows/tests.yml`).
- **On every pull request:** the fast API suite. On merge and nightly: the UI suite in headless Chrome.
- **Keep artifacts:** HTML reports with embedded screenshots on every run.
- **Keep known bugs visible but non-blocking:** mark them `xfail` with their bug ID and `strict=True`. A new bug turns the pipeline red; a fixed bug also turns it red, so the mark is removed and the test becomes a regression guard.
- **Secrets:** the user id is stored as a GitHub Secret, never in the code.

### 2. Make test data reliable and isolated

**The problem today**
- **One user and one balance for all tests.** If two tests ran at the same time, they would change the same balance and break each other: test A expects €110, but test B has already taken another €10. So tests have to run **one at a time**, and the CI uses `concurrency` so that two runs never overlap.
- **The balance reset is unreliable (BUG-02).** It promises €125.50 but stores €120. Tests can't trust the reset response and have to check the balance separately.
- **Failures are harder to trust.** When a test fails, it's not clear whether it's a real bug or data left behind by another test.

**What to ask the development team for**

1. **A pool of test users.** Several user ids instead of one (for example 5–10), so each test worker uses its **own** user and its own balance. `pytest-xdist` is a plugin that runs tests **in parallel** (`pytest -n 4` runs 4 workers). With one user per worker, tests run several times faster without affecting each other.
2. **A reliable "set balance" endpoint.** Today the balance can only be reset (and it resets to €120 instead of €125.50). Something like `POST /api/set-balance {"balance": 25.50}` would let a test start from any amount. For example, to test "insufficient balance" (TC-03), you currently have to **place a real €100 bet** to get down to €25.50. With this endpoint, the balance is set with one request.
3. **A fault-injection switch in test environments.** For example, a special header like `x-force-error: 500` that makes the server **deliberately** return an error, in test environments only and never in production. This would allow automating **TC-05** (error modal, Rebet, no double charge), which is manual-only today because there is no way to trigger an error.
4. **An option to disable the 1–4 s placement delay.** The app deliberately waits 1–4 seconds before sending a bet, so the user sees "Placing...". That's fine for users, but it makes tests **slower** and dependent on random timing. An option like `?fast=true` in test environments would remove the delay, so tests become faster and more stable.

**In short:** the tests work today, but slowly, one at a time, and with workarounds. With these four changes they would be **faster** (parallel, no delay), **more reliable** (clean, isolated data), and could cover **more scenarios** (TC-03 without real bets, TC-05 with forced errors).

### 3. Add test layers and close spec gaps
- **Component tests in the front-end repo** for the receipt mapping and payout formula. That is the cheapest place to catch BUG-03 and BUG-04, before any E2E test runs.
- **API contract tests:** validate every response against the OpenAPI schema (`/api/docs?format=json`) and automate TC-08.
- **Server-generated Bet ID and timestamp**, shown on the receipt, so bets can be traced and reconciled.
- **Spec clarifications** before the next release:
  - minimum stake (€1.00 vs €1.01);
  - payout rounding rule;
  - kickoff time and time zone;
  - invalid date ranges;
  - decimal separator.

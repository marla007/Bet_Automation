# Test Plan: Single Bet Placement

**Application under test:** https://qae-assignment-tau.vercel.app (desktop, latest Chrome)
**API:** https://qae-assignment-tau.vercel.app/api/docs
**Source:** Single Bet Placement Feature Specification
**Scope:** pre-match football singles: match list, odds selection, bet slip, stake validation, placement, receipt, error handling, balance, odds filter.
**Out of scope:** live betting, accumulators, other sports, mobile layouts, performance/load.

## How scenarios were prioritised

Priority is driven by **money impact × likelihood × detectability**:

| Priority | Meaning |
|---|---|
| **Critical** | Money moves incorrectly, or the customer is told something different from what was booked. Blocks release. |
| **High** | Core flow broken or misleading, with a workaround or no direct money loss. |
| **Medium** | Feature works incorrectly but does not affect money or the bet itself. |
| **Low** | Cosmetic or minor usability issue. |

Every money rule is checked at **both** layers: the UI shows the rule to the user, but the **API** is the real enforcement point, because anyone can call it directly.

## Coverage overview

| ID | Title | Priority | Type | Layer |
|----|-------|----------|------|-------|
| TC-01 | Place a single bet: receipt and balance are consistent | Critical | Happy path | UI + API |
| TC-02 | Stake limits and format are enforced | Critical | Boundary + Negative | UI + API |
| TC-03 | Bet cannot exceed the available balance | Critical | Boundary + Negative | UI + API |
| TC-04 | Bets on past or started matches are rejected | Critical | Negative + Boundary | UI + API |
| TC-05 | Failed placement: error modal, Rebet and no double charge | High | Negative | UI + API |
| TC-06 | Only one selection at a time; slip can be changed and cleared | High | Happy path + Negative | UI |
| TC-07 | Odds filter: inclusive bounds and invalid ranges | Medium | Boundary + Negative | UI |
| TC-08 | API rejects unauthorised and malformed requests | High | Negative | API |
| TC-09 | Reset balance restores the documented starting balance | Medium | Happy path + Negative | API + UI |
| TC-10 | Date filter: single day, range and invalid range | Medium | Boundary + Negative | UI |
| TC-11 | Match list shows correct, upcoming matches only | Low | Happy path + Boundary | UI + API |

**Core set:** TC-01 to TC-06 cover the 5–6 scenarios the assignment asks for. TC-07 to TC-11 extend coverage to the remaining UI features, the API contract and test-data setup.

## Test data and preconditions (all scenarios)

- A valid assigned user id, opened as `/?user-id=<id>` (UI) or sent as `x-user-id` header (API).
- Balance reset before each scenario: `POST /api/reset-balance`, then confirm with `GET /api/balance`. Spec starting balance: **€125.50**.
- Test match: first match in `GET /api/matches` (e.g. **Manchester Utd vs Chelsea**, home odds **2.45**). Expected values are calculated from the live odds, not hardcoded.

---

## TC-01: Place a single bet: receipt and balance are consistent

**Priority:** Critical
**Type:** Happy path

**Risk rationale:**
This is the core revenue journey and it touches every layer: match list → bet slip → API → receipt → balance. The receipt is the customer's proof of bet: a wrong payout, wrong odds or swapped teams leads to disputes and regulatory exposure. A balance that is not deducted (or deducted only on the server) shows the customer money they no longer have.

**Steps:**
1. Open the app. Note the header balance (B) and the match "Manchester Utd vs Chelsea".
2. Click odds **1** (home win, 2.45).
3. Check the bet slip: teams, market "Match Winner: Home", odds, selection count = 1.
4. Enter stake `10.00`.
5. Check Total Stake and Potential Payout.
6. Click **Place Bet**.
7. While placing, check the button state and the odds buttons.
8. When the receipt opens, check every field.
9. Click **Close**.
10. Check the header balance, the bet slip balance and `GET /api/balance`.

**Expected result:**
- Step 3: slip shows "Manchester Utd vs Chelsea", "Match Winner: Home", odds 2.45, count 1.
- Step 5: Total Stake **€10.00**, Potential Payout **€24.50** (10.00 × 2.45).
- Step 7: button shows "Placing..." and is disabled; odds buttons are disabled (no double submit).
- Step 8: receipt shows a Bet ID, **"Manchester Utd vs Chelsea"** (home first), selection Home, stake **€10.00**, odds **2.45**, payout **€24.50**, and placement time. All values match what was shown before placement.
- Step 9: receipt closes, the slip is empty.
- Step 10: header, bet slip and API all show **B − €10.00**.

---

## TC-02: Stake limits and format are enforced

**Priority:** Critical
**Type:** Boundary + Negative

**Risk rationale:**
Stake limits (€1.00–€100.00, max 2 decimals) are a financial and regulatory control. Off-by-one errors at the boundaries are the most common failure. The spec also contradicts itself on the minimum (€1.00 in the business rules, €1.01 in the validation table), so the exact boundary must be pinned. A rule enforced only in the UI is no rule at all: the API must reject the same values, and a rejected bet must never change the balance.

**Steps:**
1. **UI:** select any odds and enter each stake value from the table. Observe the message and the Place Bet button.
2. **API:** for each value, send `POST /api/place-bet` with a valid `matchId`, `"selection": "HOME"` and the stake. Then call `GET /api/balance`.

| Stake | Case | UI expected | API expected |
|---|---|---|---|
| *(empty)* | Missing value | Place Bet disabled | 422 |
| `0.99` | Just below minimum | "Minimum stake is €1.00", button disabled | 422 `invalid_stake_min` |
| `1.00` | Exact minimum | Accepted, payout = 1.00 × odds | 200, balance −1.00 |
| `100.00` | Exact maximum | Accepted | 200, balance −100.00 |
| `100.01` | Just above maximum | "Maximum stake is €100.00", button disabled | 422 `invalid_stake_max` |
| `5.555` | Three decimals | Third decimal cannot be typed | 422 `invalid_stake_precision` |
| `abc` | Text | Letters cannot be typed | 422 `invalid_stake_type` |
| `-10` | Negative | Minus sign cannot be typed | 422 `invalid_stake_min` |

**Expected result:**
- UI and API accept exactly **€1.00–€100.00 with at most 2 decimals** and reject everything else with the documented message or error code.
- For every rejected value, the balance is **unchanged**.
- For accepted values, the balance decreases by exactly the stake.

---

## TC-03: Bet cannot exceed the available balance

**Priority:** Critical
**Type:** Boundary + Negative

**Risk rationale:**
Accepting a stake the user cannot cover is a direct financial loss. The starting balance (€125.50) is close to the maximum stake (€100.00), so a second bet in the same session is the realistic trigger. This only works if the UI refreshes its balance after the first bet; a stale balance lets the user try bets they cannot afford.

**Steps:**
1. Reset the balance (€125.50). Place a **€100.00** bet and close the receipt. Remaining: **€25.50**.
2. Without reloading, select another odds and enter `25.51` (balance + €0.01).
3. Observe the bet slip message and the Place Bet button.
4. Change the stake to `25.50` (exactly the balance) and place the bet.
5. Reload the page and repeat step 2 with the new balance (€0.00) and stake `1.00`.
6. **API:** with €25.50 remaining, send `POST /api/place-bet` with stake `25.51`, then `GET /api/balance`.

**Expected result:**
- Step 3: "Insufficient balance" is shown and Place Bet is disabled (without needing a reload).
- Step 4: stake equal to the balance is **accepted**; balance becomes **€0.00**.
- Step 5: "Insufficient balance", Place Bet disabled.
- Step 6: API returns **422** (`insufficient_balance`); balance stays **€25.50**.

---

## TC-04: Bets on past or started matches are rejected

**Priority:** Critical
**Type:** Negative + Boundary

**Risk rationale:**
The product is for **pre-match** bets on **upcoming** matches only. A bet on a match that has already been played (or has started) is a bet on a known result: a direct financial loss and an obvious fraud vector. It must be blocked at **both** layers: the UI should not offer it, and the API must reject it, because anyone can call the API directly.

**Steps:**
1. Call `GET /api/matches` and find a match with a kickoff date **before today** and, if any, one **today** and one **in the future**.
2. **UI:** open the app and find the past match. Check its badge and its odds buttons. Try to click odds and place a €1.00 bet.
3. **UI:** repeat for a match dated **today** (boundary) and a future match (control).
4. **API:** send `POST /api/place-bet` for the past match with stake `1.00`. Then `GET /api/balance`.
5. **API:** repeat for the match dated today and the future match.

**Expected result:**
- Step 2: the past match is **hidden**, or shown with **disabled** odds; no bet can be placed.
- Step 3: the match dated today follows the agreed rule (bettable until kickoff; spec gives only a date, see ambiguities); the future match is bettable.
- Step 4: the API returns **422**; the balance is **unchanged**.
- Step 5: today's match follows the same rule as in the UI; the future match is accepted (200).

---

## TC-05: Failed placement: error modal, Rebet and no double charge

**Priority:** High
**Type:** Negative

**Risk rationale:**
Retries are where double charges happen. When placement fails, the user must see a clear error and be able to retry safely: **Rebet** must place exactly one bet, and **Close** must leave no stale selection. The API's `409 bet already in progress` exists to stop double submission; if it fails, one click can be charged twice.

**Steps:**
1. Select odds and enter stake `10.00`.
2. Force a failure: in Chrome DevTools → Network, block the `/api/place-bet` request (or set "Offline"). Click **Place Bet**.
3. Check the error modal.
4. Restore the network and click **Rebet**.
5. Check `GET /api/balance` and the receipt.
6. Repeat steps 1–3, then click **Close**. Repeat again and click **X**.
7. **API:** send two `POST /api/place-bet` requests for the same user at the same time.

**Expected result:**
- Step 3: modal "Something went wrong" with an explanation, a **Rebet** primary button, **Close**, and **X**. Balance unchanged.
- Step 4–5: modal closes, "Placing..." is shown, exactly **one** bet is placed and the balance is deducted **once** (−€10.00).
- Step 6: modal closes, the selection and stake are cleared, balance unchanged.
- Step 7: one request returns **200**, the other **409**; the balance is deducted **once**.
- The success receipt and the error modal are never shown at the same time.

---

## TC-06: Only one selection at a time; slip can be changed and cleared

**Priority:** High
**Type:** Happy path + Negative

**Risk rationale:**
The product supports singles only. If a second selection is added instead of replacing the first, or the slip keeps the old odds after a change, the user bets on something they did not choose. Odds that can be changed while a bet is being placed are a classic race condition.

**Steps:**
1. Click odds **1** on match A. Check the slip.
2. Click odds **X** on the same match.
3. Click odds **2** on a different match B.
4. Enter stake `10.00`, then click odds **1** on match A again.
5. Click the remove (X) button in the slip.
6. Select odds again, enter a stake, click **Remove All**.
7. Select odds, enter `10.00`, click **Place Bet**, and immediately try to click other odds while "Placing..." is shown.

**Expected result:**
- Steps 1–3: the slip always shows **exactly one** selection (count = 1), replaced by the latest click, with the correct teams, market and odds. The selected odds button is highlighted.
- Step 4: the new selection replaces the old one; the stake field is cleared (no stale stake on a new selection).
- Steps 5–6: the slip is empty, count = 0, the slip shows the balance.
- Step 7: odds buttons are disabled while placing; the bet is placed on the original selection.

---

## TC-07: Odds filter: inclusive bounds and invalid ranges

**Priority:** Medium
**Type:** Boundary + Negative

**Risk rationale:**
The filter helps users find matches; no money moves, so priority is lower. But the spec defines clear rules (bounds are **inclusive**, invalid ranges must be rejected with feedback), and boundary rules like these are easy to get wrong. A filter that silently hides matches makes the product look empty.

**Steps:**
1. Note a match whose lowest odds is exactly X (e.g. 2.45).
2. Open the odds filter. Set Min = `X`, Max = `10.00`. Apply.
3. Set Min = `X + 0.01`. Apply.
4. Set Min = `5.00`, Max = `2.00` (min > max). Apply.
5. Set Max to a high value allowed by the spec (e.g. `50.00`).
6. Click **Reset**.
7. Check "Showing N matches" after each step.

**Expected result:**
- Step 2: the match **is shown** (Min is inclusive).
- Step 3: the match is hidden if none of its odds are ≥ X + 0.01.
- Step 4: the range is **rejected with a clear message** and not applied.
- Step 5: the value is accepted within the spec's odds range.
- Step 6: all matches are shown, label "Odds: All".
- Step 7: the counter always equals the number of matches visible.

---

## TC-08: API rejects unauthorised and malformed requests

**Priority:** High
**Type:** Negative

**Risk rationale:**
Any client can call the API directly, so the API is the real gatekeeper. Requests without a valid user must never read or change a balance, and broken payloads must be rejected cleanly instead of being processed or crashing the server (500). Wrong status codes also break client error handling.

**Steps:**
Send each request and note the status code, the error body and (where relevant) `GET /api/balance` before and after.

| # | Request | Expected |
|---|---|---|
| 1 | `GET /api/balance` without `x-user-id` | 401 `missing_user_id` |
| 2 | `GET /api/balance` with an unknown user id | 401 `invalid_user_id` |
| 3 | `GET /api/place-bet` (wrong method) | 405 |
| 4 | `POST /api/place-bet` with body `not json` | 400 `invalid_json` |
| 5 | `POST /api/place-bet` with body `[]` | 400 `invalid_request` |
| 6 | `matchId` missing or `""` | 422 `invalid_match_id` |
| 7 | `matchId: "does-not-exist"` | 422 `invalid_match` |
| 8 | `selection: "home"` (lowercase) or `"WIN"` | 422 `invalid_selection` |
| 9 | Valid bet plus extra field `"odds": 1000` | 200; the server's odds are used, the extra field is ignored |

**Expected result:**
- Every request returns the documented status code and error code; none returns 500.
- No rejected request changes the balance.
- Request 9: response `odds` equals the match's real odds, and payout is calculated from them (the client cannot set its own odds).

---

## TC-09: Reset balance restores the documented starting balance

**Priority:** Medium
**Type:** Happy path + Negative

**Risk rationale:**
Reset is a test-environment feature, not a customer feature, so it is not Critical. But every other test depends on it: if the reset response and the stored balance disagree, every test starts from wrong data and money checks give false results. The API documentation itself hints that "response payload may differ from persisted balance".

**Steps:**
1. Place a bet so the balance changes.
2. Send `POST /api/reset-balance`. Note the `balance` in the response.
3. Send `GET /api/balance`.
4. Open the app and check the header balance.
5. Send `POST /api/reset-balance` twice in a row, then `GET /api/balance`.
6. Send `POST /api/reset-balance` without `x-user-id`.

**Expected result:**
- Step 2: 200, `"balance": 125.5`, `"currency": "EUR"`.
- Steps 3–4: API and UI both show **€125.50**, the same as the reset response.
- Step 5: repeated resets give the same result (**€125.50**).
- Step 6: 401; no balance is changed.

---

## TC-10: Date filter: single day, range and invalid range

**Priority:** Medium
**Type:** Boundary + Negative

**Risk rationale:**
Like the odds filter, it moves no money, but users rely on it to find matches. Date logic is a common source of off-by-one and time-zone bugs: a match on the boundary day can disappear, especially because kickoff has only a date and no time zone.

**Steps:**
1. Note the kickoff dates of the matches in the list.
2. Open the date filter, select a single day that has matches. Apply.
3. Select a range whose **start** and **end** are exactly the kickoff dates of two matches. Apply.
4. Select the end date first, then an earlier start date. Apply.
5. Select a range with no matches. Apply.
6. Click **Reset**, then **Cancel** after changing a date.
7. Check "Showing N matches" and the filter label after each step.

**Expected result:**
- Step 2: only matches on that day are shown; label "Date: DD/MM/YYYY".
- Step 3: matches on the start and end days **are included** (inclusive range).
- Step 4: the range is rejected with a message, or clearly corrected (start/end swapped) and shown in the label. *(Spec does not define this; behaviour must be agreed.)*
- Step 5: an empty list with a clear "no matches" state, not a blank area.
- Step 6: Reset shows all matches ("Date: All"); Cancel keeps the previously applied filter.
- Step 7: the counter always equals the number of visible matches.

---

## TC-11: Match list shows correct, upcoming matches only

**Priority:** Low
**Type:** Happy path + Boundary

**Risk rationale:**
This is mostly presentation, so the risk is lower. But two details carry real weight: matches that have already started must not be bettable (pre-match only), and team order and odds must match the API exactly, since they feed into the bet slip and receipt.

**Steps:**
1. Call `GET /api/matches` and open the app.
2. Compare each match card with the API data: competition, kickoff label, home team (first), away team, odds for 1 / X / 2.
3. Check the odds format.
4. Check the kickoff labels for matches today, tomorrow and later this week.
5. Check whether any match has a kickoff date in the past.
6. Check the counter "Showing N matches".

**Expected result:**
- Step 2: every card matches the API; home team is listed first; buttons 1 / X / 2 show home / draw / away odds.
- Step 3: odds always have 2 decimals (e.g. `3.10`, not `3.1`).
- Step 4: labels "Today", "Tomorrow", the weekday name, or the date, as applicable.
- Step 5: past matches are not shown, or are shown without bettable odds (covered in depth by **TC-04**).
- Step 6: N equals the number of matches returned by the API.

---

## Execution

**Executed:** the Critical scenarios **TC-01, TC-02 and TC-04**, plus **TC-09** as a check of the test setup. All of them are automated; results and defects are in [BUG_REPORTS.md](BUG_REPORTS.md).

**Next:** TC-03 (insufficient balance). Its UI part depends on BUG-05 (the balance is not updated after a bet), so it is most useful once that bug is fixed.

Automated coverage:

| Scenario | Automated test |
|-------|---|
| TC-01 | `UI/tests/test_place_bet.py::test_place_single_bet` |
| TC-02 | `API/tests/test_stake_validation.py` |
| TC-04 | `API/tests/test_past_match.py` |
| TC-04 | `UI/tests/test_past_match.py` |
| TC-09 | `API/tests/test_reset_balance.py` |

## Spec ambiguities raised

- **Minimum stake:** €1.00 (business rules, UI copy, API) vs €1.01 (validation table). Tested against €1.00; spec should be corrected.
- **Kickoff "date/time":** the API returns only a date (`kickoffDate`), no time or time zone.
- **Invalid date range** (start after end) is not covered by the spec.
- **Decimal separator** (`.` vs `,`) is not defined.
- **Payout rounding** (e.g. 3.33 × 2.45) is not defined.

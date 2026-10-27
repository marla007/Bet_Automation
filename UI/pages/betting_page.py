"""Main page: header balance and the match list with odds buttons."""

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By

from UI.pages.base_page import BasePage
from UI.pages.bet_slip import BetSlip
from UI.pages.receipt_modal import ReceiptModal


class BettingPage(BasePage):
    HEADER_BALANCE = (By.ID, "header-balance")
    MATCH_LIST = (By.ID, "match-list")
    ERROR_MODAL = (By.ID, "modal-error")

    def __init__(self, driver, base_url, timeout=10):
        super().__init__(driver, timeout)
        self.base_url = base_url
        self.bet_slip = BetSlip(driver, timeout)
        self.receipt = ReceiptModal(driver, timeout)

    def open(self, user_id):
        self.driver.get(f"{self.base_url}/?user-id={user_id}")
        self.wait.visible(self.MATCH_LIST)
        return self

    def get_header_balance(self):
        return self.get_amount(self.HEADER_BALANCE)

    def wait_for_header_balance(self, expected, timeout=5):
        """Give the header time to show the expected balance, then return what it really shows.

        Does not fail on its own: the test compares the returned value, so the report shows
        the actual balance instead of a bare timeout.
        """
        try:
            self.wait.text_contains(self.HEADER_BALANCE, f"€{expected:.2f}", timeout)
        except TimeoutException:
            pass
        return self.get_header_balance()

    @staticmethod
    def odds_button(match_id, selection):
        """selection: 'home', 'draw' or 'away' (buttons 1 / X / 2)."""
        return By.ID, f"odds-{match_id}-{selection}"

    def get_odds(self, match_id, selection):
        button = self.wait.visible(self.odds_button(match_id, selection))
        return float(button.find_element(By.CLASS_NAME, "oddsButtonValue").text)

    def is_match_shown(self, match_id):
        return self.is_displayed((By.ID, f"match-card-{match_id}"))

    def is_odds_enabled(self, match_id, selection):
        """Non-waiting check: can this odds button be clicked right now?"""
        buttons = self.driver.find_elements(*self.odds_button(match_id, selection))
        return bool(buttons) and buttons[0].is_enabled()

    def select_odds(self, match_id, selection):
        self.click(self.odds_button(match_id, selection))
        self.bet_slip.wait_until_open()
        return self.bet_slip

    def wait_for_bet_result(self, timeout=15):
        """The app waits 1-4 s before calling the API. Returns 'success' or 'error'."""
        shown = self.wait.any_visible(self.receipt.ROOT, self.ERROR_MODAL, timeout=timeout)
        return "success" if shown == self.receipt.ROOT else "error"

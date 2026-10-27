"""Success modal (receipt) shown after a bet is placed."""

from selenium.webdriver.common.by import By

from UI.pages.base_page import BasePage


class ReceiptModal(BasePage):
    ROOT = (By.ID, "modal-success")
    BET_ID = (By.ID, "modal-success-bet-id")
    MATCH = (By.ID, "modal-success-match")
    STAKE = (By.ID, "modal-success-stake")
    ODDS = (By.ID, "modal-success-odds")
    PAYOUT = (By.ID, "modal-success-payout")
    PLACED_AT = (By.ID, "modal-success-placed-at")
    CLOSE_BUTTON = (By.ID, "modal-success-close")

    def get_bet_id(self):
        return self.get_text(self.BET_ID)

    def get_match(self):
        return self.get_text(self.MATCH)

    def get_stake(self):
        return self.get_amount(self.STAKE)

    def get_odds(self):
        return float(self.get_text(self.ODDS))

    def get_payout(self):
        return self.get_amount(self.PAYOUT)

    def get_placed_at(self):
        return self.get_text(self.PLACED_AT)

    def close(self):
        self.click(self.CLOSE_BUTTON)
        self.wait.invisible(self.ROOT)

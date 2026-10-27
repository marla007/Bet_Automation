"""Bet slip panel: selection, stake, totals and the Place Bet button."""

from selenium.webdriver.common.by import By

from UI.pages.base_page import BasePage


class BetSlip(BasePage):
    SELECTION_TEAMS = (By.CSS_SELECTOR, "#bet-slip .betSelectionTeams")
    STAKE_INPUT = (By.ID, "bet-slip-stake-input")
    TOTAL_STAKE = (By.ID, "bet-slip-total-stake")
    POTENTIAL_PAYOUT = (By.ID, "bet-slip-potential-payout")
    PLACE_BET_BUTTON = (By.ID, "bet-slip-place-bet")
    BALANCE = (By.ID, "bet-slip-balance")

    def wait_until_open(self):
        self.wait.visible(self.STAKE_INPUT)

    def wait_until_empty(self):
        self.wait.invisible(self.STAKE_INPUT)

    def get_selection_teams(self):
        return self.get_text(self.SELECTION_TEAMS)

    def enter_stake(self, amount):
        self.type(self.STAKE_INPUT, amount)
        return self

    def get_total_stake(self):
        return self.get_amount(self.TOTAL_STAKE)

    def get_potential_payout(self):
        return self.get_amount(self.POTENTIAL_PAYOUT)

    def get_balance(self):
        """Shown only when the slip is empty."""
        return self.get_amount(self.BALANCE)

    def place_bet(self):
        self.wait.enabled(self.PLACE_BET_BUTTON)
        self.click(self.PLACE_BET_BUTTON)
        # The button switches to its "in progress" style while the bet is being placed
        self.wait.attribute_contains(self.PLACE_BET_BUTTON, "class", "placeBetButtonPlacing")

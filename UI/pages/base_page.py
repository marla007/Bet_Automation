"""Base class for all page objects: common actions built on the general waits."""

import os
import re
import sys
from datetime import datetime

from selenium.webdriver.common.keys import Keys

from UI.utils.waits import Waits

SELECT_ALL_KEY = Keys.COMMAND if sys.platform == "darwin" else Keys.CONTROL
SCREENSHOT_DIR = "screenshots"


class BasePage:
    def __init__(self, driver, timeout=10):
        self.driver = driver
        self.wait = Waits(driver, timeout)

    def click(self, locator):
        self.wait.clickable(locator).click()

    def type(self, locator, text):
        field = self.wait.visible(locator)
        field.send_keys(SELECT_ALL_KEY, "a")  # clear() does not trigger React's onChange
        field.send_keys(Keys.DELETE)
        field.send_keys(text)

    def get_text(self, locator):
        return self.wait.visible(locator).text.strip()

    def get_amount(self, locator):
        """Read a euro amount from the page: 'Balance: €125.50' -> 125.5"""
        return float(re.search(r"€\s*([\d.]+)", self.get_text(locator)).group(1))

    def is_displayed(self, locator):
        elements = self.driver.find_elements(*locator)
        return bool(elements) and elements[0].is_displayed()

    def take_screenshot(self, name):
        """Save the current screen as screenshots/<name>_<time>.png and return the path.
        'BUG-03 Receipt teams' becomes BUG-03_Receipt_teams_20261027_153508.png"""
        os.makedirs(SCREENSHOT_DIR, exist_ok=True)
        safe_name = re.sub(r"[^A-Za-z0-9-]+", "_", name).strip("_")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = f"{SCREENSHOT_DIR}/{safe_name}_{timestamp}.png"
        self.driver.save_screenshot(path)
        return path

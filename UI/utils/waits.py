"""General explicit waits, reused by every page object and usable directly in tests.

Each method waits only as long as needed and never uses time.sleep().
"""

from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


class Waits:
    def __init__(self, driver, timeout=10):
        self.driver = driver
        self.timeout = timeout

    def until(self, condition, message="", timeout=None):
        """Wait for any custom condition: a function that receives the driver."""
        return WebDriverWait(self.driver, timeout or self.timeout).until(condition, message)

    def visible(self, locator, timeout=None):
        return self.until(
            EC.visibility_of_element_located(locator), f"{locator} is not visible", timeout
        )

    def clickable(self, locator, timeout=None):
        return self.until(
            EC.element_to_be_clickable(locator), f"{locator} is not clickable", timeout
        )

    def invisible(self, locator, timeout=None):
        return self.until(
            EC.invisibility_of_element_located(locator), f"{locator} is still visible", timeout
        )

    def enabled(self, locator, timeout=None):
        return self.until(
            lambda driver: driver.find_element(*locator).is_enabled(),
            f"{locator} is not enabled",
            timeout,
        )

    def text_contains(self, locator, text, timeout=None):
        return self.until(
            EC.text_to_be_present_in_element(locator, text),
            f"{locator} does not contain {text!r}",
            timeout,
        )

    def attribute_contains(self, locator, attribute, value, timeout=None):
        """Wait until an attribute (e.g. class) contains a value. Safer than checking text,
        which can change with CSS such as text-transform: uppercase."""
        return self.until(
            EC.text_to_be_present_in_element_attribute(locator, attribute, value),
            f"{locator} [{attribute}] does not contain {value!r}",
            timeout,
        )

    def any_visible(self, *locators, timeout=None):
        """Wait until one of several elements appears and return the locator that appeared."""

        def first_visible(driver):
            for locator in locators:
                elements = driver.find_elements(*locator)
                if elements and elements[0].is_displayed():
                    return locator
            return False

        return self.until(first_visible, f"none of {locators} became visible", timeout)

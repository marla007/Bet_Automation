"""UI fixtures: browser, page objects, test data and screenshots on failure."""

import os
import shutil
from datetime import datetime

import pytest
import requests
from selenium import webdriver

import config
from common.test_data import pick_past_match, pick_upcoming_match
from UI.pages.betting_page import BettingPage
from UI.utils.waits import Waits

SCREENSHOT_DIR = "screenshots"


@pytest.fixture(scope="session", autouse=True)
def clean_screenshots():
    """Start every run with an empty screenshots/ folder, so it only holds the latest run."""
    shutil.rmtree(SCREENSHOT_DIR, ignore_errors=True)


@pytest.fixture
def driver():
    options = webdriver.ChromeOptions()
    if config.HEADLESS:
        options.add_argument("--headless=new")
    options.add_argument("--window-size=1440,900")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(options=options)

    yield driver
    driver.quit()


@pytest.fixture
def waits(driver):
    """General waits, available directly inside test cases."""
    return Waits(driver, config.TIMEOUT)


@pytest.fixture
def betting_page(driver):
    return BettingPage(driver, config.BASE_URL, config.TIMEOUT)


@pytest.fixture
def api_session():
    """Used only for test setup (balance reset, match data), not for UI checks.
    Resets the balance before and after the test, so every run starts clean."""
    session = requests.Session()
    session.headers["x-user-id"] = config.USER_ID
    session.post(f"{config.BASE_URL}/api/reset-balance").raise_for_status()
    yield session
    session.post(f"{config.BASE_URL}/api/reset-balance")
    session.close()


@pytest.fixture
def match(api_session):
    """First upcoming match from the live catalog, so the test never hardcodes teams or odds."""
    return pick_upcoming_match(api_session.get(f"{config.BASE_URL}/api/matches").json())


@pytest.fixture
def past_match(api_session):
    """A match whose kickoff date is before today; the test is skipped if there is none."""
    past = pick_past_match(api_session.get(f"{config.BASE_URL}/api/matches").json())
    if past is None:
        pytest.skip("No past matches in the catalog")
    return past


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """When a UI test fails (or hits a known bug), take a screenshot while the browser
    is still open: save it to screenshots/ and attach it to the HTML report."""
    outcome = yield
    report = outcome.get_result()
    if report.when != "call":
        return

    driver = item.funcargs.get("driver")
    known_bug = hasattr(report, "wasxfail")
    if driver is None or not (report.failed or known_bug):
        return

    os.makedirs(SCREENSHOT_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    driver.save_screenshot(f"{SCREENSHOT_DIR}/{item.name}_{timestamp}.png")

    pytest_html = item.config.pluginmanager.getplugin("html")
    if pytest_html:
        extras = getattr(report, "extras", [])
        extras.append(pytest_html.extras.image(driver.get_screenshot_as_base64()))
        report.extras = extras

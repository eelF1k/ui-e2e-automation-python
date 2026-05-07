from datetime import datetime
from pathlib import Path

import pytest

from tests.ui.driver_factory import DriverConfig, create_chrome_driver


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--base-url",
        action="store",
        default="http://localhost",
        help="Base URL of the application under test.",
    )
    parser.addoption(
        "--headless",
        action="store_true",
        default=False,
        help="Run browser in headless mode.",
    )


@pytest.fixture(scope="session")
def base_url(request: pytest.FixtureRequest) -> str:
    return str(request.config.getoption("--base-url"))


@pytest.fixture()
def driver(request: pytest.FixtureRequest):
    headless = bool(request.config.getoption("--headless"))
    drv = create_chrome_driver(DriverConfig(headless=headless))
    yield drv
    drv.quit()


@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item: pytest.Item, call: pytest.CallInfo):
    outcome = yield
    report = outcome.get_result()

    if report.when != "call" or report.passed:
        return

    drv = item.funcargs.get("driver")
    if drv is None:
        return

    target_dir = Path("reports/ui_failures")
    target_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    test_name = item.name.replace("/", "_").replace("\\", "_")
    stem = f"{test_name}_{timestamp}"

    screenshot_path = target_dir / f"{stem}.png"
    html_path = target_dir / f"{stem}.html"

    drv.save_screenshot(str(screenshot_path))
    html_path.write_text(drv.page_source, encoding="utf-8")


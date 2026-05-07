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


import pytest


def pytest_addoption(parser: pytest.Parser) -> None:
    parser.addoption(
        "--base-url",
        action="store",
        default="http://localhost",
        help="Base URL of the application under test.",
    )


@pytest.fixture(scope="session")
def base_url(request: pytest.FixtureRequest) -> str:
    return str(request.config.getoption("--base-url"))


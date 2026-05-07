import pytest

from tests.ui.pages.login_page import LoginPage


@pytest.mark.smoke
def test_login_success(driver, base_url: str) -> None:
    page = LoginPage(driver, base_url=base_url)
    page.open()

    page.login(username="standard_user", password="secret_sauce")

    assert "inventory" in driver.current_url


@pytest.mark.smoke
@pytest.mark.parametrize(
    ("username", "password"),
    [
        ("standard_user", "wrong_password"),
        ("locked_out_user", "secret_sauce"),
    ],
)
def test_login_shows_error(driver, base_url: str, username: str, password: str) -> None:
    page = LoginPage(driver, base_url=base_url)
    page.open()

    page.login(username=username, password=password)

    assert page.error_text()


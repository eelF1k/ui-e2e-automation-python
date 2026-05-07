import pytest

from tests.ui.pages.cart_page import CartPage
from tests.ui.pages.catalog_page import CatalogPage
from tests.ui.pages.login_page import LoginPage


@pytest.mark.regression
def test_checkout_navigation_after_adding_item(driver, base_url: str) -> None:
    login_page = LoginPage(driver, base_url=base_url)
    login_page.open()
    login_page.login(username="standard_user", password="secret_sauce")

    catalog_page = CatalogPage(driver, base_url=base_url)
    catalog_page.add_first_item_to_cart()
    catalog_page.open_cart()

    cart_page = CartPage(driver, base_url=base_url)
    assert cart_page.has_items(), "Cart should contain at least one item."

    cart_page.click_checkout()
    assert "checkout-step-one" in driver.current_url


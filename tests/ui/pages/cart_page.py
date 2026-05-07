from __future__ import annotations

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from tests.ui.pages.base_page import BasePage


class CartPage(BasePage):
    CART_ITEM = (By.CSS_SELECTOR, ".cart_item")
    CHECKOUT_BUTTON = (By.ID, "checkout")

    def __init__(self, driver: WebDriver, base_url: str) -> None:
        super().__init__(driver, base_url)

    def has_items(self) -> bool:
        return bool(self.driver.find_elements(*self.CART_ITEM))

    def click_checkout(self) -> None:
        self.click(self.CHECKOUT_BUTTON)


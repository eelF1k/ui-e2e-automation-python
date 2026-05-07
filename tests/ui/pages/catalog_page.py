from __future__ import annotations

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from tests.ui.pages.base_page import BasePage


class CatalogPage(BasePage):
    CART_LINK = (By.CSS_SELECTOR, ".shopping_cart_link")
    FIRST_ADD_TO_CART_BUTTON = (By.CSS_SELECTOR, ".inventory_item:first-of-type button")

    def __init__(self, driver: WebDriver, base_url: str) -> None:
        super().__init__(driver, base_url)

    def add_first_item_to_cart(self) -> None:
        self.click(self.FIRST_ADD_TO_CART_BUTTON)

    def open_cart(self) -> None:
        self.click(self.CART_LINK)


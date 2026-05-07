from __future__ import annotations

from urllib.parse import urljoin

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

from tests.ui.waits import Waits


class BasePage:
    def __init__(self, driver: WebDriver, base_url: str) -> None:
        self.driver = driver
        self.base_url = base_url.rstrip("/") + "/"
        self.wait = Waits(driver)

    def open(self, path: str) -> None:
        self.driver.get(urljoin(self.base_url, path.lstrip("/")))

    def find(self, by: str, value: str) -> WebElement:
        return self.driver.find_element(by, value)

    def type(self, locator: tuple[str, str], text: str, clear: bool = True) -> None:
        el = self.wait.visible(locator)
        if clear:
            el.clear()
        el.send_keys(text)

    def click(self, locator: tuple[str, str]) -> None:
        self.wait.clickable(locator).click()

    @staticmethod
    def css(selector: str) -> tuple[str, str]:
        return (By.CSS_SELECTOR, selector)

    @staticmethod
    def xpath(selector: str) -> tuple[str, str]:
        return (By.XPATH, selector)


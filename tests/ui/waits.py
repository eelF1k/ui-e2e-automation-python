from __future__ import annotations

from typing import Callable

from selenium.common.exceptions import TimeoutException
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement
from selenium.webdriver.support import expected_conditions as ec
from selenium.webdriver.support.ui import WebDriverWait


class Waits:
    def __init__(self, driver: WebDriver, timeout_s: int = 10) -> None:
        self._driver = driver
        self._timeout_s = timeout_s

    def until(self, condition: Callable[[WebDriver], object], timeout_s: int | None = None) -> object:
        return WebDriverWait(self._driver, timeout_s or self._timeout_s).until(condition)

    def visible(self, locator: tuple[str, str], timeout_s: int | None = None) -> WebElement:
        return WebDriverWait(self._driver, timeout_s or self._timeout_s).until(ec.visibility_of_element_located(locator))

    def clickable(self, locator: tuple[str, str], timeout_s: int | None = None) -> WebElement:
        return WebDriverWait(self._driver, timeout_s or self._timeout_s).until(ec.element_to_be_clickable(locator))

    def gone(self, locator: tuple[str, str], timeout_s: int | None = None) -> bool:
        try:
            return bool(
                WebDriverWait(self._driver, timeout_s or self._timeout_s).until(ec.invisibility_of_element_located(locator))
            )
        except TimeoutException:
            return False


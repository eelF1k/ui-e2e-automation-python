from __future__ import annotations

from dataclasses import dataclass

from selenium import webdriver
from selenium.webdriver.chrome.options import Options as ChromeOptions
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager


@dataclass(frozen=True)
class DriverConfig:
    headless: bool = True
    window_width: int = 1920
    window_height: int = 1080
    page_load_timeout_s: int = 30
    script_timeout_s: int = 30


def create_chrome_driver(config: DriverConfig) -> webdriver.Chrome:
    options = ChromeOptions()
    if config.headless:
        options.add_argument("--headless=new")
    options.add_argument(f"--window-size={config.window_width},{config.window_height}")
    options.add_argument("--disable-gpu")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")

    service = ChromeService(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    driver.set_page_load_timeout(config.page_load_timeout_s)
    driver.set_script_timeout(config.script_timeout_s)
    return driver


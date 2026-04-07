"""
Home Page — eBay landing page search entry point.
"""
from __future__ import annotations

import logging

import allure
from playwright.sync_api import Page

from pages.base_page import BasePage

logger = logging.getLogger(__name__)


class HomePage(BasePage):
    PAGE_NAME = "HomePage"

    # ---- Selectors -------------------------------------------------------
    SEARCH_INPUT = "#gh-ac"
    SEARCH_BUTTON = "#gh-btn"

    def __init__(self, page: Page, config: dict) -> None:
        super().__init__(page, config)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @allure.step("Open eBay home page")
    def open(self) -> None:
        self.navigate(self.config["base_url"])
        self.dismiss_overlays()
        self.take_screenshot("home_page_loaded")
        logger.info("[HomePage] Home page opened.")

    @allure.step("Search for: {query}")
    def search(self, query: str) -> None:
        """Type query into the search bar and submit."""
        logger.info(f"[HomePage] Searching for: '{query}'")
        self.wait_for_selector(self.SEARCH_INPUT)
        self.clear_and_fill(self.SEARCH_INPUT, query)
        self.click(self.SEARCH_BUTTON)
        self.page.wait_for_load_state("domcontentloaded")
        logger.info("[HomePage] Search submitted.")

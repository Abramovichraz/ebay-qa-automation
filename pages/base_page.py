"""
Base Page — shared Playwright helpers used by every page object.
"""
from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import Optional

import allure
from playwright.sync_api import Page, Locator, TimeoutError as PlaywrightTimeoutError

logger = logging.getLogger(__name__)


class BasePage:
    """Abstract base providing common Playwright utilities."""

    # Override in subclasses to give each page a readable name in logs/reports
    PAGE_NAME: str = "BasePage"

    def __init__(self, page: Page, config: dict) -> None:
        self.page = page
        self.config = config
        self._screenshots_dir = Path(config["paths"]["screenshots"])
        self._screenshots_dir.mkdir(parents=True, exist_ok=True)
        self._default_timeout: int = config["timeouts"]["default"]

    # ------------------------------------------------------------------
    # Navigation helpers
    # ------------------------------------------------------------------

    def navigate(self, url: str) -> None:
        """Navigate to the given URL and wait for network idle."""
        logger.info(f"[{self.PAGE_NAME}] Navigating to: {url}")
        self.page.goto(url, timeout=self.config["timeouts"]["navigation"])
        self.page.wait_for_load_state("domcontentloaded")

    def get_current_url(self) -> str:
        return self.page.url

    # ------------------------------------------------------------------
    # Element interaction helpers
    # ------------------------------------------------------------------

    def click(self, selector: str, timeout: Optional[int] = None) -> None:
        timeout = timeout or self._default_timeout
        logger.debug(f"[{self.PAGE_NAME}] Clicking: {selector}")
        self.page.locator(selector).first.click(timeout=timeout)

    def fill(self, selector: str, value: str, timeout: Optional[int] = None) -> None:
        timeout = timeout or self._default_timeout
        logger.debug(f"[{self.PAGE_NAME}] Filling '{selector}' with '{value}'")
        self.page.locator(selector).first.fill(value, timeout=timeout)

    def clear_and_fill(self, selector: str, value: str) -> None:
        element = self.page.locator(selector).first
        element.clear()
        element.fill(value)

    def get_text(self, selector: str, timeout: Optional[int] = None) -> str:
        timeout = timeout or self._default_timeout
        return (self.page.locator(selector).first.inner_text(timeout=timeout) or "").strip()

    def is_visible(self, selector: str, timeout: int = 3000) -> bool:
        try:
            self.page.locator(selector).first.wait_for(state="visible", timeout=timeout)
            return True
        except PlaywrightTimeoutError:
            return False

    def wait_for_selector(self, selector: str, timeout: Optional[int] = None) -> None:
        timeout = timeout or self._default_timeout
        self.page.locator(selector).first.wait_for(state="visible", timeout=timeout)

    def select_option_by_text(self, selector: str, text: str) -> None:
        self.page.locator(selector).first.select_option(label=text)

    # ------------------------------------------------------------------
    # Screenshot helpers
    # ------------------------------------------------------------------

    def take_screenshot(self, name: str) -> str:
        """Save a screenshot and attach it to the Allure report."""
        safe_name = name.replace(" ", "_").replace("/", "-")
        filepath = self._screenshots_dir / f"{safe_name}.png"
        self.page.screenshot(path=str(filepath), full_page=True)
        logger.info(f"[{self.PAGE_NAME}] Screenshot saved: {filepath}")
        with open(filepath, "rb") as f:
            allure.attach(
                f.read(),
                name=name,
                attachment_type=allure.attachment_type.PNG,
            )
        return str(filepath)

    # ------------------------------------------------------------------
    # Utility
    # ------------------------------------------------------------------

    def wait(self, ms: int) -> None:
        self.page.wait_for_timeout(ms)

    def scroll_to_bottom(self) -> None:
        self.page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        self.wait(500)

    def dismiss_overlays(self) -> None:
        """Dismiss common eBay overlays / cookie banners if present."""
        dismissal_selectors = [
            "button#gdpr-banner-accept",
            "button[aria-label='Close']",
            "button.gh-eb-Lightbox-close",
            "#signin-guest-continue",
        ]
        for sel in dismissal_selectors:
            if self.is_visible(sel, timeout=1500):
                try:
                    self.click(sel)
                    logger.info(f"[{self.PAGE_NAME}] Dismissed overlay: {sel}")
                    self.wait(300)
                except Exception:
                    pass

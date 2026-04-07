"""
Login Page — eBay sign-in flow.
Note: eBay may present CAPTCHA for automated logins.
      Leave credentials blank in test_data.json to skip login (guest flow).
"""
from __future__ import annotations

import logging

import allure
from playwright.sync_api import Page

from pages.base_page import BasePage

logger = logging.getLogger(__name__)


class LoginPage(BasePage):
    PAGE_NAME = "LoginPage"

    # ---- Selectors -------------------------------------------------------
    SIGN_IN_LINK = "header a:has-text('Sign in'), a[href*='signin']"
    EMAIL_INPUT = "input#userid, input[name='userid']"
    CONTINUE_BTN = "button#signin-continue-btn, button[name='signin-continue-btn']"
    PASSWORD_INPUT = "input#pass, input[name='pass']"
    SIGN_IN_BTN = "button#sgnBt, button[name='sgnBt']"
    USER_GREETING = "span.gh-ib"          # greeting shown when logged in
    ERROR_BANNER = ".error-message"

    def __init__(self, page: Page, config: dict) -> None:
        super().__init__(page, config)

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @allure.step("Login to eBay with username: {username}")
    def login(self, username: str, password: str) -> bool:
        """
        Attempt to log in.  Returns True if successful, False otherwise.
        Skipped when credentials are empty (guest/anonymous flow).
        """
        if not username or not password:
            logger.info("[LoginPage] No credentials provided — skipping login (guest mode).")
            return False

        logger.info(f"[LoginPage] Attempting login for: {username}")
        
        # Start from home page to look more human
        self.navigate(self.config["base_url"])
        self.dismiss_overlays()
        
        # Click Sign In link
        try:
            self.click(self.SIGN_IN_LINK, timeout=10000)
            logger.info("[LoginPage] Clicked Sign In link.")
        except Exception:
            logger.info("[LoginPage] Sign In link not found or already on sign-in page. Navigating directly.")
            self.navigate(self.config["base_url"] + "/signin/")

        self.dismiss_overlays()

        # Enter email
        try:
            self.wait_for_selector(self.EMAIL_INPUT, timeout=15000)
            self.fill(self.EMAIL_INPUT, username)
            self.click(self.CONTINUE_BTN)
            self.wait(2000)
        except Exception as e:
            logger.warning(f"[LoginPage] Email step failed: {e}")
            self.take_screenshot("login_email_step_error")
            return False

        # Enter password
        try:
            # Check for CAPTCHA before password field
            if self.page.locator("text=verify you are human").is_visible() or self.is_visible("div#captcha") or self.page.locator("iframe[src*='captcha']").is_visible():
                logger.warning("[LoginPage] CAPTCHA detected after email step.")
                self.take_screenshot("login_captcha_after_email")
                return False

            self.wait_for_selector(self.PASSWORD_INPUT, state="visible", timeout=15000)
            self.fill(self.PASSWORD_INPUT, password)
            self.click(self.SIGN_IN_BTN)
            self.wait(3000)
        except Exception as e:
            logger.warning(f"[LoginPage] Password step failed: {e}")
            self.take_screenshot("login_password_step_error")
            return False

        if self.is_visible(self.USER_GREETING):
            logger.info("[LoginPage] Login successful.")
            self.take_screenshot("login_success")
            return True

        if self.is_visible(self.ERROR_BANNER):
            error = self.get_text(self.ERROR_BANNER)
            logger.warning(f"[LoginPage] Login failed: {error}")
            self.take_screenshot("login_failure")
        else:
            logger.warning("[LoginPage] Login status unknown — possible CAPTCHA or redirect.")
            self.take_screenshot("login_unknown")

        return False

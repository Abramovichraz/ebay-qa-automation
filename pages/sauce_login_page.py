"""
SauceDemo Login Page — for the stable E2E demo run.
"""
from playwright.sync_api import Page
from pages.base_page import BasePage

class SauceLoginPage(BasePage):
    URL = "https://www.saucedemo.com/"
    
    USERNAME_INPUT = "input#user-name"
    PASSWORD_INPUT = "input#password"
    LOGIN_BUTTON = "input#login-button"

    def __init__(self, page: Page, config: dict):
        super().__init__(page, config)

    def open(self):
        self.navigate(self.URL)

    def login(self, username, password):
        self.fill(self.USERNAME_INPUT, username)
        self.fill(self.PASSWORD_INPUT, password)
        self.click(self.LOGIN_BUTTON)

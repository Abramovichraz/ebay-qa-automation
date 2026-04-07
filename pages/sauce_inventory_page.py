"""
SauceDemo Inventory Page — for the stable E2E demo run.
"""
from typing import List, Optional
from playwright.sync_api import Page
from pages.base_page import BasePage

class SauceInventoryPage(BasePage):
    URL = "https://www.saucedemo.com/inventory.html"
    
    ITEM_NAME = ".inventory_item_name"
    ADD_TO_CART_BTN = "button.btn_inventory"
    CART_BADGE = "span.shopping_cart_badge"
    CART_LINK = "a.shopping_cart_link"

    def __init__(self, page: Page, config: dict):
        super().__init__(page, config)

    def add_item_to_cart_by_index(self, index: int):
        self.page.locator(self.ADD_TO_CART_BTN).nth(index).click()

    def get_cart_count(self) -> int:
        badge = self.page.locator(self.CART_BADGE)
        if badge.is_visible():
            return int(badge.get_text_contents().first)
        return 0

    def navigate_to_cart(self):
        self.click(self.CART_LINK)

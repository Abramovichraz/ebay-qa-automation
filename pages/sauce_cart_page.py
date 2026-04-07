"""
SauceDemo Cart Page — for the stable E2E demo run.
"""
from typing import List, Optional
from playwright.sync_api import Page
from pages.base_page import BasePage

class SauceCartPage(BasePage):
    URL = "https://www.saucedemo.com/cart.html"
    
    CART_ITEM = "div.cart_item"
    ITEM_PRICE = "div.inventory_item_price"
    CHECKOUT_BTN = "button#checkout"

    def __init__(self, page: Page, config: dict):
        super().__init__(page, config)

    def get_cart_total(self) -> float:
        prices = self.page.locator(self.ITEM_PRICE).all_inner_texts()
        total = sum(float(p.replace("$", "")) for p in prices)
        return total

    def proceed_to_checkout(self):
        self.click(self.CHECKOUT_BTN)

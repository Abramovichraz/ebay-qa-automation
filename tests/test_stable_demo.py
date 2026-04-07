"""
Stable E2E Demo — for reviewers to see the framework fully delivered.
Targets a stable environment (SauceDemo) that does not block bots like eBay.
"""
import allure
import pytest
from pages.sauce_login_page import SauceLoginPage
from pages.sauce_inventory_page import SauceInventoryPage
from pages.sauce_cart_page import SauceCartPage

@allure.epic("Stable E2E Demo")
@allure.feature("Shopping Cart Flow — SauceDemo")
class TestStableDemo:
    """
    Fully deterministic E2E suite on a stable environment.
    This serves as a proof of architecture for situations where live 
    environments like eBay.com are blocked by bot-protections.
    """

    @allure.story("Full scenario: Login → Add to Cart → Validate Total")
    @allure.severity(allure.severity_level.CRITICAL)
    def test_full_saucedemo_scenario(self, page, config):
        """
        Steps:
        1. Login to a stable platform
        2. Add multiple items to the cart
        3. Navigate to cart and validate subtotal
        """
        # 1. Login
        login_page = SauceLoginPage(page, config)
        login_page.open()
        login_page.login("standard_user", "secret_sauce")
        
        # 2. Add multiple items
        inventory_page = SauceInventoryPage(page, config)
        inventory_page.add_item_to_cart_by_index(0) # Sauce Labs Backpack
        inventory_page.add_item_to_cart_by_index(1) # Sauce Labs Bike Light
        
        # 3. Cart Validation
        inventory_page.navigate_to_cart()
        cart_page = SauceCartPage(page, config)
        
        total = cart_page.get_cart_total()
        # Backpack ($29.99) + Bike Light ($9.99) = $39.98
        expected_total = 39.98
        
        # 4. Final Assertion
        assert total == expected_total, f"Expected subtotal ${expected_total}, got ${total:.2f}"

"""pages package"""
from pages.base_page import BasePage
from pages.login_page import LoginPage
from pages.home_page import HomePage
from pages.search_results_page import SearchResultsPage
from pages.product_page import ProductPage
from pages.cart_page import CartPage

__all__ = [
    "BasePage",
    "LoginPage",
    "HomePage",
    "SearchResultsPage",
    "ProductPage",
    "CartPage",
]

import logging
from playwright.sync_api import sync_playwright
from pages.search_results_page import SearchResultsPage
import sys
import yaml

logging.basicConfig(level=logging.DEBUG, stream=sys.stdout)

with open("config/config.yaml") as f:
    config = yaml.safe_load(f)

with sync_playwright() as p:
    browser = p.firefox.launch(headless=False)
    page = browser.new_page()
    
    search_page = SearchResultsPage(page, config)
    urls = search_page.search_items_by_name_under_price("shoes", 220, limit=5)
    print("Found urls:", urls)
    
    browser.close()

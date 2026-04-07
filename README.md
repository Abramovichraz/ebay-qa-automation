eBay QA Automation — E2E Test

Playwright + Python · POM · OOP · Data-Driven

Overview

This project implements an end-to-end automation flow for an e-commerce website (eBay example), covering:

Login (optional)
Product search with price filtering
Adding items to cart
Validating cart total against a budget

The solution follows clean architecture principles:

Page Object Model (POM)
Object-Oriented Design (OOP)
Data-Driven testing (JSON input)
Project Structure
ebay-qa-automation/
├── config/
│   └── config.yaml
├── data/
│   └── test_data.json
├── pages/
│   ├── base_page.py
│   ├── login_page.py
│   ├── home_page.py
│   ├── search_results_page.py
│   ├── product_page.py
│   └── cart_page.py
├── tests/
│   └── test_ebay_e2e.py   # Main E2E test
├── utils/
│   └── helpers.py
├── reports/
├── conftest.py
├── pytest.ini
└── requirements.txt
Setup
1. Install dependencies
pip install -r requirements.txt
playwright install chromium
2. (Optional) Set credentials

You can run the test in guest mode, or provide credentials.

Recommended (more secure):

Create a .env file:

EBAY_EMAIL=your@email.com
EBAY_PASSWORD=yourpassword
Run Test

Run the main E2E scenario:

python -m pytest tests/test_ebay_e2e.py -v
Test Scenario

The main test (TC_001) performs:

Login (optional)
Search for items by name under a maximum price
Collect matching product URLs
Add item(s) to cart

Validate cart total does not exceed:

budget_per_item × number_of_items
Core Functions
Function	Description
search_items_by_name_under_price	Searches products and returns URLs under max price
add_items_to_cart	Adds selected items to cart
assert_cart_total_not_exceeds	Validates total against budget
login	Performs authentication (optional)
Reports

After execution:

Screenshots are saved in reports/screenshots/
HTML report is generated automatically
Allure report can be generated:
allure serve reports/allure-results
⚠️ Known Limitations

This project runs against a live production website (eBay).

eBay uses anti-bot protection (CAPTCHA)
Automation may be blocked during:
Login
Navigation
Cart interaction
Handling Strategy
CAPTCHA detection is implemented
When detected, the test is skipped gracefully (pytest.skip)
This avoids false failures caused by external systems
Design Notes
Clean separation between test logic and UI logic (POM)
Reusable page objects
Data-driven scenario configuration via JSON
Minimal, focused implementation aligned with assignment requirements
Final Note

This solution focuses on:

Clean architecture
Readability
Stability under real-world conditions

Rather than bypassing external protections, it demonstrates how to handle them correctly in a production-like environment.
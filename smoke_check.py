import sys
sys.path.insert(0, ".")

# Import all modules
from utils.helpers import load_config, load_test_data, get_scenarios, get_credentials
from pages.base_page import BasePage
from pages.login_page import LoginPage
from pages.home_page import HomePage
from pages.search_results_page import SearchResultsPage
from pages.product_page import ProductPage
from pages.cart_page import CartPage

print("All imports OK")

cfg = load_config("config/config.yaml")
data = load_test_data("data/test_data.json")
scenarios = get_scenarios()

print(f"Config loaded: browser={cfg['browser']['name']}, headless={cfg['browser']['headless']}")
print(f"Scenarios loaded: {len(scenarios)} scenario(s)")
for s in scenarios:
    print(f"  [{s['id']}] {s['description']} | query='{s['search_query']}', max_price={s['max_price']}, limit={s['limit']}")

creds = get_credentials()
print(f"Credentials present: {'Yes' if creds['username'] else 'No (guest mode)'}")
print("\nAll checks passed!")

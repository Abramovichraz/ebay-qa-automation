from playwright.sync_api import sync_playwright

with sync_playwright() as p:
    browser = p.firefox.launch(headless=False)
    page = browser.new_page()
    page.goto("https://www.ebay.com/sch/i.html?_nkw=shoes&_udhi=220&LH_BIN=1&_sop=15")
    page.wait_for_timeout(5000)

    # find all a tags with /itm/ inside them
    links = page.locator("a[href*='/itm/']").all()
    print(f"Found {len(links)} item links")
    for idx, l in enumerate(links[:5]):
        url = l.get_attribute("href")
        print(f"[{idx}] Link inner text len: {len(l.inner_text())}, href: {url[:80]}...")
        # Get parent container classes up to 4 parents
        try:
            p1 = l.locator("xpath=..").first
            p2 = l.locator("xpath=../..").first
            p3 = l.locator("xpath=../../..").first
            p4 = l.locator("xpath=../../../..").first
            print(f"  Parent 1 class: {p1.get_attribute('class')}")
            print(f"  Parent 2 class: {p2.get_attribute('class')}")
            print(f"  Parent 3 class: {p3.get_attribute('class')}")
            print(f"  Parent 4 class: {p4.get_attribute('class')}")
            
            # Find any text that looks like a price near the link:
            parent = l.locator("xpath=ancestor::li[1] | ancestor::div[contains(@class,'item')][1] | ancestor::div[contains(@class,'card')][1]").first
            if parent:
                parent_text = parent.inner_text()
                print(f"  Found ancestor container, length of text: {len(parent_text)}")
                print(f"  Sample text: {parent_text[:100].replace(chr(10), ' // ')}")
            else:
                print("  No common item ancestor found")
        except Exception as e:
            print("  Except:", e)
    browser.close()

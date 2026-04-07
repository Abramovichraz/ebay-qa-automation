"""
Product Page — opens a listing, selects variants, adds item to cart.

Core function implemented here:
    add_items_to_cart(urls: list[str]) → None
"""
from __future__ import annotations

import logging
import random
import re
from typing import List, Optional

import allure
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError
from tenacity import retry, stop_after_attempt, wait_fixed

from pages.base_page import BasePage

logger = logging.getLogger(__name__)


class ProductPage(BasePage):
    PAGE_NAME = "ProductPage"

    # ---- Selectors -------------------------------------------------------
    # Add to cart button — eBay uses various IDs across listing types
    ADD_TO_CART_SELECTORS = [
        "#atcBtn_btn",
        "#isCartBtn_btn",
        "a[data-testid='x-atc-action']",
        "button[data-testid='x-atc-action']",
        "a:has-text('Add to cart')",
        "button:has-text('Add to cart')",
        "a[data-tl-id='VI-addToCart']",
        "a#isCartBtn",
        "button[data-tl-id='VI-addToCart']",
        "span[id*='addToCart'] a",
    ]

    # View cart / Go to checkout confirmation popup
    VIEW_CART_POPUP = "a[href*='/cart']"
    CART_CONFIRM_CLOSE = "button[aria-label='Close']"

    # Variant selectors (size, color, style, etc.) — scoped to purchase area only
    VARIANT_SELECT = "div.x-item-purchase select, select.msku-sel, div.ux-layout-section--app-msku select"
    VARIANT_BUTTON = "div.x-item-purchase button, div.msku-btn-list button"

    # Item title
    ITEM_TITLE = "h1.x-item-title__mainTitle span"

    # Item price
    ITEM_PRICE = "div.x-price-primary span.ux-textspans"

    def __init__(self, page: Page, config: dict) -> None:
        super().__init__(page, config)

    # ------------------------------------------------------------------
    # Core Function 2: add_items_to_cart
    # ------------------------------------------------------------------

    @allure.step("Add items to cart")
    def add_items_to_cart(self, urls: List[str], max_price: Optional[float] = None) -> None:
        """
        Iterate over each product URL, select any required variants randomly,
        verify the price (if max_price is provided), click Add to Cart, 
        then return to the previous context for the next item.

        Saves a screenshot after each successful add.
        """
        logger.info(f"[ProductPage] add_items_to_cart called with {len(urls)} URLs")
        successful = 0

        for idx, url in enumerate(urls, start=1):
            logger.info(f"[ProductPage] Processing item {idx}/{len(urls)}: {url}")
            with allure.step(f"Item {idx}: {url}"):
                try:
                    # using domcontentloaded for faster/more resilient navigation on heavy eBay pages
                    self.page.goto(url, wait_until="domcontentloaded", timeout=45000)
                    self.dismiss_overlays()
                    self.wait(1500)

                    title = self._get_item_title()
                    logger.info(f"[ProductPage] Item title: {title}")

                    # Validate price before adding
                    if max_price is not None:
                        price = self.get_item_price()
                        if price is not None:
                            logger.info(f"[ProductPage] Validating price: {price} <= {max_price}")
                            assert price <= max_price, f"Price validation failed: Item price ${price:.2f} exceeds max ${max_price:.2f}"
                        else:
                            logger.warning("[ProductPage] Could not read item price — skipping strict price validation.")

                    # Select variants (size, colour, etc.) — random pick
                    self._select_variants_randomly()

                    # Click Add to Cart
                    added = self._click_add_to_cart()

                    if added:
                        successful += 1
                        self.take_screenshot(f"cart_add_{idx}_{title[:20]}")
                        
                        # If more items to go, dismiss popup. If it's the LAST one, keep it
                        # so the CartPage can click 'Go to cart' which is more 'human'
                        if idx < len(urls):
                            self._dismiss_cart_popup()
                        
                        logger.info(f"[ProductPage] ✓ Item {idx} added to cart.")
                    else:
                        logger.warning(f"[ProductPage] ✗ Could not add item {idx} to cart.")
                        self.take_screenshot(f"cart_add_FAILED_{idx}")

                except Exception as exc:
                    logger.error(f"[ProductPage] Error processing item {idx}: {exc}")
                    self.take_screenshot(f"cart_add_ERROR_{idx}")

        logger.info(f"[ProductPage] Done — {successful}/{len(urls)} items added to cart.")

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _get_item_title(self) -> str:
        try:
            return self.get_text(self.ITEM_TITLE)
        except Exception:
            return "unknown_item"

    def get_item_price(self) -> Optional[float]:
        text = ""
        try:
            text = self.get_text(self.ITEM_PRICE)
            if not text: return None
            
            cleaned = text.replace("ILS", "").replace("NIS", "").replace("₪", "").replace("$", "").replace(",", "").strip()
            match = re.search(r"\d+(\.\d+)?", cleaned)
            if match:
                return float(match.group())
                
        except Exception as exc:
            logger.debug(f"[ProductPage] get_item_price failed to parse: '{text}' - {exc}")
        return None

    def _select_variants_randomly(self) -> None:
        """
        If the listing requires variant selection (size/colour/style),
        pick one randomly from available options.
        Supports various select and button-group pickers common on eBay.
        """
        # --- Handle <select> dropdowns ---
        try:
            # We look for ANY visible select elements within the purchase section
            container = self.page.locator("div.x-item-purchase, div#mainContent")
            all_selects = container.locator("select:visible").all()
            
            for sel in all_selects:
                options = sel.locator("option").all()
                valid_options = []
                for opt in options:
                    val = (opt.get_attribute("value") or "").strip()
                    txt = (opt.inner_text() or "").lower()
                    if val and val != "-1" and "select" not in txt:
                        valid_options.append(opt)
                
                if valid_options:
                    chosen = random.choice(valid_options)
                    value = chosen.get_attribute("value")
                    sel.select_option(value=value)
                    self.wait(1000)
                    logger.info(f"[ProductPage] Selected variant: {chosen.inner_text().strip()}")
        except Exception as exc:
            logger.debug(f"[ProductPage] Variant selection encountered issue: {exc}")

        # --- Handle button-group pickers ---
        try:
            # Common variant button selectors
            for btn in self.page.locator(self.VARIANT_BUTTON).all():
                if btn.is_visible() and not "disabled" in (btn.get_attribute("class") or "").lower():
                    # We pick one button group and click one valid button
                    btn.click()
                    self.wait(1000)
                    logger.info(f"[ProductPage] Selected variant (button): {btn.inner_text().strip()}")
                    break
        except Exception as exc:
            logger.debug(f"[ProductPage] Button selection skipped: {exc}")
        except Exception as exc:
            logger.debug(f"[ProductPage] Button variant selection skipped: {exc}")

    @retry(stop=stop_after_attempt(3), wait=wait_fixed(1.5))
    def _click_add_to_cart(self) -> bool:
        """
        Try each known Add to Cart selector in priority order.
        Retries up to 3 times to handle dynamic button loading or flaky renders.
        Returns True if successfully clicked.
        """
        for selector in self.ADD_TO_CART_SELECTORS:
            if self.is_visible(selector, timeout=2000):
                try:
                    self.click(selector)
                    self.wait(1500)
                    logger.info(f"[ProductPage] Add to Cart clicked via: {selector}")
                    return True
                except Exception as exc:
                    logger.debug(f"[ProductPage] Add to Cart failed ({selector}): {exc}")
        return False

    def _dismiss_cart_popup(self) -> None:
        """Close any 'Item added to cart' overlay."""
        popup_close_selectors = [
            self.CART_CONFIRM_CLOSE,
            "button[data-tl-id='VI-atcBtn-closeMiniCart']",
            "a[aria-label='Close layer']",
        ]
        for sel in popup_close_selectors:
            if self.is_visible(sel, timeout=2000):
                try:
                    self.click(sel)
                    self.wait(500)
                    return
                except Exception:
                    pass

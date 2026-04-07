"""
Search Results Page — applies price filter, extracts item URLs, handles pagination.

Core function implemented here:
    search_items_by_name_under_price(query, max_price, limit=5) → list[str]
"""
from __future__ import annotations

import logging
import re
from typing import List, Optional

import allure
from playwright.sync_api import Page, TimeoutError as PlaywrightTimeoutError

from pages.base_page import BasePage

logger = logging.getLogger(__name__)


class SearchResultsPage(BasePage):
    PAGE_NAME = "SearchResultsPage"

    # ---- Selectors -------------------------------------------------------
    # Price filter inputs (hidden in sidebar, revealed after search)
    PRICE_MIN_INPUT = "input[name='_udlo']"
    PRICE_MAX_INPUT = "input[name='_udhi']"
    PRICE_SUBMIT_BUTTON = "button.x-refine__go-btn"
    # Alternative price filter via URL approach (used as fallback)

    # Item listing selectors
    ITEM_CONTAINER = "li.s-item"
    ITEM_LINK = "a.s-item__link"
    ITEM_PRICE = "span.s-item__price"
    ITEM_TITLE = "div.s-item__title"

    # Pagination
    NEXT_PAGE_BTN = "a[aria-label='Go to next search page']"
    NEXT_PAGE_BTN_ALT = "li.pagination__next > a"

    def __init__(self, page: Page, config: dict) -> None:
        super().__init__(page, config)
        self._max_pages: int = config["ebay"]["pagination_max_pages"]
        self._filter_delay: int = config["ebay"]["price_filter_submit_delay"]

    # ------------------------------------------------------------------
    # Core Function 1: search_items_by_name_under_price
    # ------------------------------------------------------------------

    @allure.step("Search items '{query}' under ${max_price}, limit={limit}")
    def search_items_by_name_under_price(
        self,
        query: str,
        max_price: float,
        limit: int = 5,
    ) -> List[str]:
        """
        Perform a search and collect up to `limit` item URLs where price ≤ max_price.

        Strategy:
        1. Apply URL-based price filter (most reliable on eBay).
        2. Scrape items from current page, filter by price.
        3. Paginate via "Next" button until limit reached or pages exhausted.

        Returns a list of item URLs (may be fewer than limit if results are scarce).
        """
        logger.info(
            f"[SearchResultsPage] Searching: query='{query}', max_price={max_price}, limit={limit}"
        )

        self._apply_price_filter_via_url(query, max_price)
        self.take_screenshot("search_results_price_filtered")

        # CHECK FOR ZERO RESULTS (avoiding 'similar items' false positives)
        if self._is_zero_results(query):
            logger.info(f"[SearchResultsPage] Zero results found for query: '{query}'")
            return []

        collected_urls: List[str] = []
        page_num = 0

        while len(collected_urls) < limit and page_num < self._max_pages:
            page_num += 1
            logger.info(f"[SearchResultsPage] Scraping page {page_num}...")
            self.wait(800)

            new_urls = self._collect_items_on_current_page(max_price, limit - len(collected_urls))
            collected_urls.extend(new_urls)
            logger.info(
                f"[SearchResultsPage] Page {page_num}: found {len(new_urls)} items, "
                f"total so far: {len(collected_urls)}"
            )

            if len(collected_urls) >= limit:
                break

            if not self._go_to_next_page():
                logger.info("[SearchResultsPage] No more pages — stopping pagination.")
                break

        result = collected_urls[:limit]
        logger.info(f"[SearchResultsPage] Final URL list ({len(result)} items): {result}")
        allure.attach(
            "\n".join(result),
            name="Collected Item URLs",
            attachment_type=allure.attachment_type.TEXT,
        )
        return result

    # ------------------------------------------------------------------
    # Private helpers
    # ------------------------------------------------------------------

    def _is_zero_results(self, query: str) -> bool:
        """
        Check if eBay explicitly states zero results match the query.
        This prevents picking up 'similar items' or 'results for fewer words'.
        """
        zero_markers = [
            "h1.srp-save-search__no-results",
            "div.srp-save-search__no-results",
            ".s-messaging__content-title:has-text('0 results')",
            "header.srp-results__header:has-text('0 results')",
            "div.s-message__content:has-text('0 matches')",
        ]
        for marker in zero_markers:
            if self.is_visible(marker, timeout=2000):
                logger.debug(f"[SearchResultsPage] Found zero-result marker: {marker}")
                return True
        
        # Check if results are only from 'Results matching fewer words'
        # These are often in a separate div/header
        fewer_words_header = "xpath=//*[contains(text(), 'matching fewer words')]"
        if self.is_visible(fewer_words_header, timeout=1000):
            # If the item count before this header is zero, then it's effectively zero results
            # But the simplest check is the presence of the '0 results' text.
            pass

        return False

    def _apply_price_filter_via_url(self, query: str, max_price: float) -> None:
        """
        Build a search URL with _udhi (max price) baked in.
        This is the most reliable way to apply price filters on eBay.
        """
        encoded_query = query.replace(" ", "+")
        url = (
            f"{self.config['base_url']}/sch/i.html"
            f"?_nkw={encoded_query}"
            f"&_udhi={int(max_price)}"
            f"&LH_BIN=1"          # Buy It Now only (has fixed prices)
            f"&_sop=15"           # Sort: Price + Shipping: lowest first
        )
        logger.info(f"[SearchResultsPage] Navigating to filtered URL: {url}")
        self.navigate(url)
        self.page.wait_for_load_state("domcontentloaded")
        self.dismiss_overlays()

        # Also try to fill in the on-page price inputs for visual confirmation
        self._try_fill_sidebar_price_filter(max_price)

    def _try_fill_sidebar_price_filter(self, max_price: float) -> None:
        """Optionally fill the sidebar price filter fields (best-effort)."""
        try:
            if self.is_visible(self.PRICE_MAX_INPUT, timeout=3000):
                self.clear_and_fill(self.PRICE_MAX_INPUT, str(int(max_price)))
                if self.is_visible(self.PRICE_SUBMIT_BUTTON, timeout=2000):
                    self.click(self.PRICE_SUBMIT_BUTTON)
                    self.wait(self._filter_delay)
                    self.page.wait_for_load_state("domcontentloaded")
                    logger.info("[SearchResultsPage] Sidebar price filter applied.")
        except Exception as exc:
            logger.debug(f"[SearchResultsPage] Sidebar price filter skipped: {exc}")

    def _collect_items_on_current_page(
        self, max_price: float, remaining: int
    ) -> List[str]:
        """
        Scrape items from the current search-results page.
        Uses XPath to locate price elements and validate against max_price.
        Returns up to `remaining` matching URLs.
        """
        # CRITICAL: Wait for network to settle so items render
        try:
            self.page.wait_for_load_state("networkidle", timeout=5000)
            self.page.locator("li.s-item, .s-card").first.wait_for(timeout=3000)
        except Exception as exc:
            logger.debug(f"[SearchResultsPage] Wait strategy skipped/timed out: {exc}")

        collected: List[str] = []

        # eBay heavily A/B tests its DOM structure and localization tags.
        # We try multiple plausible item container selectors robustly.
        candidate_selectors = [
            "//li[contains(@class,'s-item')]",
            "//div[contains(@class,'s-item')]",
            "//li[contains(@data-view, 'mi:')]",
            "//div[contains(@class,'item-card')]",
            "//div[contains(@class,'product-card')]",
            "//div[contains(@class,'s-card')]",
            "//li[contains(@class,'s-card')]",
            "//ul[contains(@class,'srp-results')]//li"
        ]
        
        items = []
        for sel in candidate_selectors:
            elements = self.page.locator(sel).all()
            # Valid item containers MUST contain an actual link to an item
            # eBay often embeds 1-2 empty template 's-item' divs at the top of the DOM.
            if len(elements) > 0:
                valid_count = self.page.locator(sel).locator("xpath=.//a[contains(@href,'/itm/')]").count()
                if valid_count > 0:
                    items = elements
                    logger.debug(f"[SearchResultsPage] Found {len(items)} items using selector: {sel}")
                    break

        if not items:
            logger.warning("[SearchResultsPage] Could not find any valid item containers using known selectors.")

        for item in items:
            if len(collected) >= remaining:
                break

            try:
                # Get the link (href)
                link_el = item.locator("xpath=.//a[contains(@href,'/itm/')]").first
                url = link_el.get_attribute("href", timeout=1000)
                if not url or "ebay.com" not in url:
                    continue

                # Get the price text - use multiple strategies
                price_text = ""
                price_locators = [
                    "xpath=.//*[contains(@class,'price')]",
                    "text=ILS",
                    "text=NIS",
                    "text=₪",
                    "text=$",
                ]
                for p_loc in price_locators:
                    p_el = item.locator(p_loc).first
                    try:
                        price_text = p_el.inner_text(timeout=1000)
                        if price_text:
                            break
                    except Exception:
                        continue

                if not price_text:
                    # Fallback to scanning all text in the item
                    price_text = item.inner_text()

                price = self._parse_price(price_text)
                if price is None:
                    continue  # Could not determine price — skip

                # Price validation
                if price > max_price:
                    continue

                collected.append(url)
                title_el = item.locator("xpath=.//*[contains(@class,'title')]").first
                title = title_el.inner_text(timeout=1000) if title_el else url.split("/")[-1]

                # Secondary Filter 1: Skip generic ads/placeholders
                if any(kw in title.lower() for kw in ["shop on ebay", "shop by brand"]):
                    logger.debug(f"[SearchResultsPage] Skipping non-item link: '{title}'")
                    collected.pop()
                    continue

                # Secondary Filter 2: Relevance Check (Anti-Fuzzy Match)
                # Ensure the title contains at least one significant keyword from the query
                # to filter out eBay's 'similar items' or 'results matching fewer words'.
                query_keywords = [kw.lower() for kw in query.split() if len(kw) > 3]
                if query_keywords and not any(kw in title.lower() for kw in query_keywords):
                    logger.warning(f"[SearchResultsPage] Skipping irrelevant result: '{title}' (no query keywords found)")
                    collected.pop()
                    continue

                logger.info(
                    f"[SearchResultsPage] ✓ Item accepted: price=${price:.2f} | {title[:60]}"
                )

            except Exception as exc:
                logger.debug(f"[SearchResultsPage] Skipping item due to error: {exc}")
                continue

        return collected

    def _go_to_next_page(self) -> bool:
        """Click the 'Next' pagination button. Returns True if navigation occurred."""
        for selector in [self.NEXT_PAGE_BTN, self.NEXT_PAGE_BTN_ALT]:
            if self.is_visible(selector, timeout=2000):
                try:
                    self.click(selector)
                    self.page.wait_for_load_state("domcontentloaded")
                    self.wait(800)
                    return True
                except Exception as exc:
                    logger.debug(f"[SearchResultsPage] Pagination click failed ({selector}): {exc}")
        return False

    @staticmethod
    def _parse_price(price_text: str) -> Optional[float]:
        """
        Extract a numeric price from eBay price strings.
        """
        if not price_text:
            return None
            
        # Strongly strip common currencies or commas
        cleaned = price_text.replace("ILS", "").replace("NIS", "").replace("₪", "").replace("$", "").replace(",", "").strip()
        
        # Match digit patterns
        match = re.search(r"\d+(\.\d+)?", cleaned)
        if not match:
            return None
            
        return float(match.group())

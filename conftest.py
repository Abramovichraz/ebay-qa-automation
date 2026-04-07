"""
conftest.py — Pytest fixtures shared across all tests.

pytest-playwright (>=0.5) already provides:
  - playwright  (session-scoped)
  - browser     (session-scoped)
  - browser_context (function-scoped)
  - page        (function-scoped)

We configure them via the official override hooks:
  - browser_type_launch_args  → headless, slow_mo
  - browser_context_args      → viewport, locale, timezone

We add our own fixtures on top:
  - config    : loaded YAML configuration dict
  - test_data : loaded JSON test data dict
"""
from __future__ import annotations

import logging
from pathlib import Path

import allure
import pytest

from utils.helpers import ensure_dirs, load_config, load_test_data, setup_logging

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Session-scoped: load config + test data once per session
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def config() -> dict:
    cfg = load_config("config/config.yaml")
    ensure_dirs(
        cfg["paths"]["screenshots"],
        cfg["paths"]["allure_results"],
        Path(cfg["paths"]["html_report"]).parent.as_posix(),
    )
    setup_logging()
    return cfg


@pytest.fixture(scope="session")
def test_data() -> dict:
    return load_test_data("data/test_data.json")


# ---------------------------------------------------------------------------
# pytest-playwright configuration hooks
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def browser_type_launch_args(config: dict) -> dict:
    """Override launch args — read from our YAML config."""
    return {
        "headless": config["browser"]["headless"],
        "slow_mo": config["browser"]["slow_mo"],
    }


@pytest.fixture(scope="session")
def browser_context_args(config: dict) -> dict:
    """Override context args — viewport, locale, timezone."""
    vp = config["browser"]["viewport"]
    return {
        "viewport": {"width": vp["width"], "height": vp["height"]},
        "locale": "en-US",
        "timezone_id": "America/New_York",
    }


# ---------------------------------------------------------------------------
# Hook: capture final screenshot + attach to Allure on every test
# ---------------------------------------------------------------------------

@pytest.fixture(scope="function", autouse=True)
def attach_screenshot_on_result(page, request):
    """After each test, attach a screenshot to Allure (pass or fail)."""
    yield
    try:
        screenshot_bytes = page.screenshot(full_page=True)
        allure.attach(
            screenshot_bytes,
            name=f"final_state — {request.node.name}",
            attachment_type=allure.attachment_type.PNG,
        )
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Hook: add readable test titles to Allure
# ---------------------------------------------------------------------------

def pytest_runtest_setup(item):
    allure.dynamic.title(item.name.replace("_", " ").title())

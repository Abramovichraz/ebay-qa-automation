"""
Utility helpers — config loading, test data loading, logging setup.
"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path
from typing import Any, Dict, List

import yaml

logger = logging.getLogger(__name__)


def load_config(config_path: str = "config/config.yaml") -> Dict[str, Any]:
    """Load and return the YAML configuration."""
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {config_path}")
    with open(path, "r", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    logger.info(f"[helpers] Config loaded from: {path}")
    return cfg


def load_test_data(data_path: str = "data/test_data.json") -> Dict[str, Any]:
    """Load and return the JSON test data."""
    path = Path(data_path)
    if not path.exists():
        raise FileNotFoundError(f"Test data file not found: {data_path}")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    logger.info(f"[helpers] Test data loaded from: {path}")
    return data


def get_scenarios(data_path: str = "data/test_data.json") -> List[Dict[str, Any]]:
    """Return the list of test scenarios from the data file."""
    data = load_test_data(data_path)
    return data.get("scenarios", [])


def get_credentials(data_path: str = "data/test_data.json") -> Dict[str, str]:
    """Return eBay credentials from the data file."""
    data = load_test_data(data_path)
    return data.get("credentials", {"username": "", "password": ""})


def setup_logging(level: str = "INFO") -> None:
    """Configure root logger for the test session."""
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def ensure_dirs(*paths: str) -> None:
    """Create directories if they do not exist."""
    for p in paths:
        Path(p).mkdir(parents=True, exist_ok=True)

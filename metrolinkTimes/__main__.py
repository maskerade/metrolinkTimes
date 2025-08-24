"""Main entry point for the Metrolink Times FastAPI application."""

import json
import logging
from pathlib import Path
from typing import Any

import uvicorn

from metrolinkTimes.api import app

logger = logging.getLogger(__name__)


def load_config() -> dict[str, Any]:
    """Load configuration from file with fallback to defaults."""
    # Look for config file in multiple locations (local first, then system)
    config_paths = [
        Path("config/metrolinkTimes.conf"),  # Local to project
        Path("metrolinkTimes.conf"),  # Current directory
        Path("/etc/metrolinkTimes/metrolinkTimes.conf"),  # System-wide
    ]

    default_config = {
        "port": 5050,
        "host": "0.0.0.0",
        "Access-Control-Allow-Origin": "*",
    }

    for config_path in config_paths:
        if config_path.exists():
            try:
                with config_path.open() as conf_file:
                    config = json.load(conf_file)
                    logger.info(f"Loaded config from {config_path}")
                    # Merge with defaults
                    return {**default_config, **config}
            except (json.JSONDecodeError, OSError) as e:
                logger.error(f"Could not parse config file {config_path}: {e}")
                continue

    logger.warning(
        f"No config file found. Checked: {', '.join(str(p) for p in config_paths)}"
    )
    logger.info("Using default configuration")
    return default_config


def main() -> None:
    """Main entry point for the FastAPI application."""
    # Setup basic logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Load configuration
    config = load_config()

    logger.info(f"Starting Metrolink Times API on {config['host']}:{config['port']}")

    # Run the FastAPI app with uvicorn
    uvicorn.run(
        app, host=config["host"], port=config["port"], log_level="info", access_log=True
    )


if __name__ == "__main__":
    main()

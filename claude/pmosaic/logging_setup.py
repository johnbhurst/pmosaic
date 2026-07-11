"""Logging configuration shared by the CLI scripts."""

import datetime
import logging
import os


def setup_logging(script_name, debug=False):
    """Configure root logging to both the console and a dated log file."""
    level = logging.DEBUG if debug else logging.INFO
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    log_file = f"{script_name}.log.{date_str}"

    formatter = logging.Formatter("%(asctime)s %(levelname)s - %(message)s")

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)

    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)

    logger = logging.getLogger()
    logger.setLevel(level)
    logger.handlers.clear()
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    logging.debug("Logging to %s", os.path.abspath(log_file))

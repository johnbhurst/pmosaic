# Copyright 2024 John Hurst
# John Hurst (john.b.hurst@gmail.com)
# 2024-08-01

import datetime
import inspect
import logging
import os


def setup_logging(level=logging.INFO):
    calling_frame = inspect.currentframe().f_back
    script_name = os.path.splitext(os.path.basename(inspect.getfile(calling_frame)))[0]
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    log_file = f"{script_name}.log.{date_str}"
    formatter = logging.Formatter("%(asctime)s %(levelname)s - %(message)s")
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    file_handler = logging.FileHandler(log_file)
    file_handler.setFormatter(formatter)
    logger = logging.getLogger()
    logger.setLevel(level)
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)





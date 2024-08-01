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


def average_rgb(image):
    pixels = image.load()
    width, height = image.size
    r = g = b = 0
    for x in range(width):
        for y in range(height):
            r += pixels[x, y][0]
            g += pixels[x, y][1]
            b += pixels[x, y][2]
    size = width * height
    return {"red": r // size, "green": g // size, "blue": b // size}


def average_quadrants(image):
    width, height = image.size
    half_width = width // 2
    half_height = height // 2
    q1 = image.crop((0, 0, half_width, half_height))
    q2 = image.crop((half_width, 0, width, half_height))
    q3 = image.crop((0, half_height, half_width, height))
    q4 = image.crop((half_width, half_height, width, height))
    return {
        "top_left": average_rgb(q1),
        "top_right": average_rgb(q2),
        "bot_left": average_rgb(q3),
        "bot_right": average_rgb(q4)
    }





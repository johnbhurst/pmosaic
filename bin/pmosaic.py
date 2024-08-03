# Copyright 2024 John Hurst
# John Hurst (john.b.hurst@gmail.com)
# 2024-08-01

import datetime
import inspect
import json
import logging
import numpy as np
import os
from math import sqrt

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


def crop_square(image):
    width, height = image.size
    if width > height:
        return image.crop(((width - height) // 2, 0, (width + height) // 2, height))
    elif height > width:
        return image.crop((0, (height - width) // 2, width, (height + width) // 2))
    else:
        return image


def average_rgb(data):
    r, g, b = data.mean(axis=(0, 1))
    return {"red": int(r), "green": int(g), "blue": int(b)}


def average_quadrants(image):
    data = np.array(image)
    height, width, _ = data.shape
    height_half, width_half = height // 2, width // 2

    return {
        "top_left": av_rgb(data[:height_half, :width_half]),
        "top_right": av_rgb(data[:height_half, width_half:]),
        "bot_Left": av_rgb(data[height_half:, :width_half]),
        "bot_right": av_rgb(data[height_half:, width_half:])
    }


def load_library(libfile):
    with open(libfile) as f:
        return [json.loads(line) for line in f]


def quadrant_colors_distance(qc1, qc2):
    return sqrt(float(sum(
        pow(qc1[quadrant][color]^2 - qc2[quadrant][color], 2)
        for quadrant in ["top_left", "top_right", "bot_left", "bot_right"]
        for color in ["red", "green", "blue"]))
    )


def best_match(image, library):
    image_quadrants = average_quadrants(image)
    best_match = None
    best_distance = float("inf")
    for lib_entry in library:
        lib_quadrants = lib_entry["quadrant_colors"]
        distance = quadrant_colors_distance(image_quadrants, lib_quadrants)
        if distance < best_distance:
            best_distance = distance
            best_match = lib_entry
    return best_match


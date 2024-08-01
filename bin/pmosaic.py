# Copyright 2024 John Hurst
# John Hurst (john.b.hurst@gmail.com)
# 2024-08-01

import datetime
import inspect
import json
import logging
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


def load_library(libfile):
    with open(libfile) as f:
        return [json.loads(line) for line in f]


def quadrant_colors_distance(qc1, qc2):
    # v1 = pow(float(qc1["top_left"]["red"] - qc2["top_left"]["red"]), 2.0)
    # v2 = pow(float(qc1["top_left"]["green"] - qc2["top_left"]["green"]), 2.0)
    # v3 = pow(float(qc1["top_left"]["blue"] - qc2["top_left"]["blue"]), 2.0)
    # v4 = pow(float(qc1["top_right"]["red"] - qc2["top_right"]["red"]), 2.0)
    # v5 = pow(float(qc1["top_right"]["green"] - qc2["top_right"]["green"]), 2.0)
    # v6 = pow(float(qc1["top_right"]["blue"] - qc2["top_right"]["blue"]), 2.0)
    # v7 = pow(float(qc1["bot_left"]["red"] - qc2["bot_left"]["red"]), 2.0)
    # v8 = pow(float(qc1["bot_left"]["green"] - qc2["bot_left"]["green"]), 2.0)
    # v9 = pow(float(qc1["bot_left"]["blue"] - qc2["bot_left"]["blue"]), 2.0)
    # v10 = pow(float(qc1["bot_right"]["red"] - qc2["bot_right"]["red"]), 2.0)
    # v11 = pow(float(qc1["bot_right"]["green"] - qc2["bot_right"]["green"]), 2.0)
    # v12 = pow(float(qc1["bot_right"]["blue"] - qc2["bot_right"]["blue"]), 2.0)
    # sum = v1 + v2 + v3 + v4 + v5 + v6 + v7 + v8 + v9 + v10 + v11 + v12
    # print(f"{v1=}, {v2=}, {v3=}, {v4=}, {v5=}, {v6=}, {v7=}, {v8=}, {v9=}, {v10=}, {v11=}, {v12=}")
    # print(sum)
    # return sqrt(sum)
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


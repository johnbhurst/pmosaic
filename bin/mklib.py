#!/usr/bin/env python
# Copyright 2024 John Hurst
# John Hurst (john.b.hurst@gmail.com)
# 2024-07-31

import argparse
import json
import logging
import pmosaic
from PIL import Image

parser = argparse.ArgumentParser(description="Create a 'mosaic library' from a collection of images, recording for each one the average RGB values of each of four quaadrants.")
parser.add_argument("-d", "--debug", action="store_true", help="Enable debug logging.")
parser.add_argument("-f", "--libfile", default="libfile.txt", help="File to store the mosaic library data.")
parser.add_argument("files", nargs="+", help="Image files to process.")
args = parser.parse_args()


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


def create_mosaic_library(files, libfile):
    with open(libfile, "w") as f:
        for i, filename in enumerate(files):
            logging.info(f"Processing {filename}")
            image = Image.open(filename)
            # crop the image to the middle square portion
            width, height = image.size
            if width > height:
                image = image.crop(((width - height) // 2, 0, (width + height) // 2, height))
            elif height > width:
                image = image.crop((0, (height - width) // 2, width, (height + width) // 2))
            quadrant_colors = average_quadrants(image)
            print(json.dumps({"filename": filename, "quadrant_colors": quadrant_colors}), file=f)


pmosaic.setup_logging(level=logging.DEBUG if args.debug else logging.INFO)
create_mosaic_library(args.files, args.libfile)

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

pmosaic.setup_logging(level=logging.DEBUG if args.debug else logging.INFO)
with open(args.libfile, "w") as f:
    for i, filename in enumerate(args.files):
        logging.info(f"Processing {filename}")
        with Image.open(filename) as image:
            # crop the image to the middle square portion
            width, height = image.size
            if width > height:
                image = image.crop(((width - height) // 2, 0, (width + height) // 2, height))
            elif height > width:
                image = image.crop((0, (height - width) // 2, width, (height + width) // 2))
            quadrant_colors = pmosaic.average_quadrants(image)
            print(json.dumps({"filename": filename, "quadrant_colors": quadrant_colors}), file=f)

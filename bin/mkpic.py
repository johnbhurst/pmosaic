#!/usr/bin/env python
# Copyright 2024 John Hurst
# John Hurst (john.b.hurst@gmail.com)
# 2024-07-31

import argparse
import logging
import os
import pmosaic
from PIL import Image

parser = argparse.ArgumentParser(description="Compose a photo mosaic for images using metadata and picture library.")
parser.add_argument("-d", "--debug", action="store_true", help="Enable debug logging.")
parser.add_argument("-c", "--tilesize", type=int, default=200, help="Size of the tiles in the output image.")
parser.add_argument("-f", "--libfile", default="libfile.txt", help="File to store the mosaic library data.")
parser.add_argument("-i", "--imagesize", type=int, default=4000, help="Size of the output image.")
parser.add_argument("files", nargs="+", help="Image files to process.")
args = parser.parse_args()

pmosaic.setup_logging(level=logging.DEBUG if args.debug else logging.INFO)
library = pmosaic.load_library(args.libfile)
for file in args.files:
    logging.info(f"Processing {file}")
    with Image.open(file) as image:
        width, height = image.size
        if width > height:
            image = image.crop(((width - height) // 2, 0, (width + height) // 2, height))
        elif height > width:
            image = image.crop((0, (height - width) // 2, width, (height + width) // 2))
        new_image = Image.new("RGB", (args.imagesize, args.imagesize))
        num_tiles = args.imagesize // args.tilesize
        cellsize = image.width // num_tiles
        for y in range(num_tiles):
            logging.info(f"Processing row {y}")
            for x in range(num_tiles):
                cell = image.crop((x * cellsize, y * cellsize, (x + 1) * cellsize, (y + 1) * cellsize))
                best_match = pmosaic.best_match(cell, library)
                tile = Image.open(best_match["filename"])
                if tile.width > tile.height:
                    tile = tile.crop(((tile.width - tile.height) // 2, 0, (tile.width + tile.height) // 2, tile.height))
                elif tile.height > tile.width:
                    tile = tile.crop((0, (tile.height - tile.width) // 2, tile.width, (tile.height + tile.width) // 2))
                tile = tile.resize((args.tilesize, args.tilesize))
                new_image.paste(tile, (x * args.tilesize, y * args.tilesize))
        new_filename = f"{os.path.splitext(file)[0]}_mosaic{os.path.splitext(file)[1]}"
        new_image.save(new_filename)

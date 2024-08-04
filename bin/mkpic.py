#!/usr/bin/env python
# Copyright 2024 John Hurst
# John Hurst (john.b.hurst@gmail.com)
# 2024-07-31

import argparse
import json
import logging
import os
import pmosaic
from PIL import Image

parser = argparse.ArgumentParser(description="Compose a photo mosaic for images using metadata and picture library.")
parser.add_argument("-d", "--debug", action="store_true", help="Enable debug logging.")
parser.add_argument("-c", "--tilesize", type=int, default=200, help="Size of the tiles in the output image.")
parser.add_argument("-f", "--libfile", default="libfile.txt", help="File to store the mosaic library data.")
parser.add_argument("-i", "--imagesize", type=int, default=4000, help="Size of the output image.")
parser.add_argument("-o", "--outfile", type=str, default="DEFAULT", help="Output file name.")
parser.add_argument("file", help="Image file to process.")
args = parser.parse_args()

pmosaic.setup_logging(level=logging.DEBUG if args.debug else logging.INFO)
with open(args.libfile) as f:
    library = [json.loads(line) for line in f]
logging.info(f"Processing {args.file}")
with Image.open(args.file) as file_image:
    image = pmosaic.crop_square(file_image)
    new_image = Image.new("RGB", (args.imagesize, args.imagesize))
    num_tiles = args.imagesize // args.tilesize
    cellsize = image.width // num_tiles
    for row in range(num_tiles):
        logging.info(f"Processing row {row}")
        for col in range(num_tiles):
            cell = image.crop((col * cellsize, row * cellsize, (col + 1) * cellsize, (row + 1) * cellsize))
            best_match = pmosaic.best_match(cell, library)
            with Image.open(best_match["filename"]) as file_tile:
                tile = pmosaic.crop_square(file_tile).resize((args.tilesize, args.tilesize))
                new_image.paste(tile, (col * args.tilesize, row * args.tilesize))
    new_filename = args.outfile if args.outfile != "DEFAULT" else f"{os.path.splitext(args.file)[0]}_mosaic{os.path.splitext(args.file)[1]}"
    new_image.save(new_filename)

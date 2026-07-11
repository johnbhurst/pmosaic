#!/usr/bin/env python
"""Index an image library for photomosaic construction.

Usage:
    bin/mklib.py [--options] --libfile=library.json library-files...

For each image file, crop a centered square tile, hash its pixel data, compute
average-color vectors for every supported grid and color model, and append one
JSON record per file to the library file.
"""

import argparse
import logging
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pmosaic import color, library, tiles
from pmosaic.imaging import load_image
from pmosaic.logging_setup import setup_logging


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug logging.")
    parser.add_argument("--libfile", required=True, help="JSON Lines library file to append to.")
    parser.add_argument("files", nargs="+", help="Image files to index.")
    return parser.parse_args(argv)


def index_file(filename):
    """Build the image record for one file, or return ``None`` on failure."""
    image = load_image(filename)
    full_width, full_height = image.size

    square, x, y, size = tiles.crop_square(image)
    md5 = tiles.tile_md5(square)
    color_vecs = color.all_color_vecs(np.asarray(square))

    tile_record = {
        "md5": md5,
        "x": x,
        "y": y,
        "width": size,
        "height": size,
        "color_vecs": color_vecs,
        "weight": 1.0,
    }
    return {
        "filename": os.path.abspath(filename),
        "width": full_width,
        "height": full_height,
        "tiles": [tile_record],
    }


def main(argv=None):
    args = parse_args(argv)
    setup_logging("mklib", debug=args.debug)

    total = len(args.files)
    processed = 0
    failed = 0
    for index, filename in enumerate(args.files, start=1):
        logging.info("[%d/%d] Processing %s", index, total, filename)
        try:
            record = index_file(filename)
        except Exception as exc:
            logging.error("[%d/%d] Error processing %s: %s", index, total, filename, exc)
            failed += 1
            continue
        library.append_record(args.libfile, record)
        processed += 1

    logging.info("Done: %d indexed, %d failed -> %s", processed, failed, args.libfile)
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())

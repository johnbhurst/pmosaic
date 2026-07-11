#!/usr/bin/env python
"""Build a photomosaic of a target image from an indexed library.

Usage:
    bin/mkpic.py [--options] --libfiles=library.json[,...] \\
                 --outfile=output.jpg image-file
"""

import argparse
import logging
import os
import sys
from collections import defaultdict

import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pmosaic import color, library
from pmosaic.imaging import load_image
from pmosaic.logging_setup import setup_logging


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("-d", "--debug", action="store_true", help="Enable debug logging.")
    parser.add_argument("--libfiles", required=True,
                        help="Comma-separated library files.")
    parser.add_argument("--outfile", required=True, help="Output JPEG file.")
    parser.add_argument("--grid-model", default="2x2", choices=sorted(color.GRID_MODELS),
                        help="Grid model to match on (default: 2x2).")
    parser.add_argument("--color-model", default="RGB", choices=list(color.COLOR_MODELS),
                        help="Color model to match on (default: RGB).")
    parser.add_argument("--tile-size", type=int, default=200,
                        help="Size in pixels of each output tile (default: 200).")
    parser.add_argument("--width", type=int, default=None, help="Output width (default: input width).")
    parser.add_argument("--height", type=int, default=None, help="Output height (default: input height).")
    parser.add_argument("--reuse-penalty", type=float, default=0.0,
                        help="Penalty factor discouraging tile reuse (default: 0).")
    parser.add_argument("--easter_eggs", "--easter-eggs", dest="easter_eggs", default=None,
                        help="Comma-separated easter-egg library files, each placed exactly once.")
    parser.add_argument("image", help="Target image file to reproduce as a mosaic.")
    return parser.parse_args(argv)


def _split_paths(value):
    if not value:
        return []
    return [p for p in (s.strip() for s in value.split(",")) if p]


def collect_tiles(entries, grid_model, color_model):
    """Flatten library entries into ``(entry, tile, vec, weight)`` tuples.

    Vectors are parsed to NumPy arrays once, up front.
    """
    result = []
    for entry in entries:
        for tile in entry.get("tiles", []):
            try:
                vec = np.asarray(tile["color_vecs"][grid_model][color_model], dtype=np.float64)
            except (KeyError, TypeError):
                logging.warning("Tile %s missing %s/%s vector; skipping",
                                tile.get("md5"), grid_model, color_model)
                continue
            result.append((entry, tile, vec, float(tile.get("weight", 1.0))))
    return result


def extract_tile_image(entry, tile, tile_size):
    """Open the source image for *entry* and return the scaled tile image."""
    image = load_image(entry["filename"])
    box = (tile["x"], tile["y"], tile["x"] + tile["width"], tile["y"] + tile["height"])
    return image.crop(box).resize((tile_size, tile_size), Image.LANCZOS)


def compute_input_vectors(input_image, num_x, num_y, grid_model, color_model):
    """Compute the target color vector for each output-grid cell of the input."""
    arr = np.asarray(input_image)
    h, w = arr.shape[:2]
    xs = np.linspace(0, w, num_x + 1).astype(int)
    ys = np.linspace(0, h, num_y + 1).astype(int)

    vecs = {}
    for j in range(num_y):
        for i in range(num_x):
            cell = arr[ys[j]:ys[j + 1], xs[i]:xs[i + 1]]
            vecs[(i, j)] = color.color_vector(cell, grid_model, color_model)
    return vecs


def place_easter_eggs(easter_eggs, input_vecs, positions, occupied,
                      output_image, tile_size, grid_model, color_model):
    """Place each easter egg exactly once at its best free matching position."""
    for entry in easter_eggs:
        egg_tiles = entry.get("tiles")
        if not egg_tiles:
            logging.warning("Easter egg %s has no tiles; skipping", entry.get("filename"))
            continue
        tile = egg_tiles[0]
        try:
            egg_vec = np.asarray(tile["color_vecs"][grid_model][color_model], dtype=np.float64)
        except (KeyError, TypeError):
            logging.warning("Easter egg %s missing %s/%s vector; skipping",
                            entry.get("filename"), grid_model, color_model)
            continue

        best_pos = None
        best_distance = float("inf")
        for pos in positions:
            if pos in occupied:
                continue
            distance = float(np.linalg.norm(input_vecs[pos] - egg_vec))
            if distance < best_distance:
                best_distance = distance
                best_pos = pos

        if best_pos is None:
            logging.warning("No free position for easter egg %s", entry.get("filename"))
            continue

        occupied.add(best_pos)
        i, j = best_pos
        tile_image = extract_tile_image(entry, tile, tile_size)
        output_image.paste(tile_image, (i * tile_size, j * tile_size))
        logging.info("Placed easter egg %s at (%d, %d), distance=%.3f",
                     entry.get("filename"), i, j, best_distance)


def fill_main(lib_tiles, input_vecs, positions, occupied, use_counts,
              output_image, tile_size, reuse_penalty):
    """Fill all unoccupied positions with the best-matching library tiles."""
    total = len(positions) - len(occupied)
    filled = 0
    for pos in positions:
        if pos in occupied:
            continue
        input_vec = input_vecs[pos]

        best = None
        best_distance = float("inf")
        for entry, tile, vec, weight in lib_tiles:
            vec_distance = float(np.linalg.norm(input_vec - vec))
            md5 = tile["md5"]
            distance = (1.0 + use_counts[md5] * reuse_penalty) / weight * vec_distance
            if distance < best_distance:
                best_distance = distance
                best = (entry, tile)

        if best is None:
            logging.error("No library tile available for position %s", pos)
            continue

        entry, tile = best
        i, j = pos
        tile_image = extract_tile_image(entry, tile, tile_size)
        output_image.paste(tile_image, (i * tile_size, j * tile_size))
        use_counts[tile["md5"]] += 1

        filled += 1
        if filled % 25 == 0 or filled == total:
            logging.info("Filled %d/%d tiles", filled, total)


def main(argv=None):
    args = parse_args(argv)
    setup_logging("mkpic", debug=args.debug)

    lib_paths = _split_paths(args.libfiles)
    egg_paths = _split_paths(args.easter_eggs)

    library_entries = library.load_library(lib_paths)
    easter_eggs = library.load_library(egg_paths) if egg_paths else []

    lib_tiles = collect_tiles(library_entries, args.grid_model, args.color_model)
    if not lib_tiles:
        logging.error("No usable library tiles for %s/%s", args.grid_model, args.color_model)
        return 1

    input_image = load_image(args.image)

    input_width, input_height = input_image.size
    output_width = args.width or input_width
    output_height = args.height or input_height

    num_x = output_width // args.tile_size
    num_y = output_height // args.tile_size
    if num_x < 1 or num_y < 1:
        logging.error("Tile size %d too large for output %dx%d",
                      args.tile_size, output_width, output_height)
        return 1
    logging.info("Output %dx%d, grid %dx%d tiles of %dpx",
                 output_width, output_height, num_x, num_y, args.tile_size)

    output_image = Image.new("RGB", (output_width, output_height))
    positions = [(i, j) for j in range(num_y) for i in range(num_x)]
    occupied = set()
    use_counts = defaultdict(int)

    input_vecs = compute_input_vectors(input_image, num_x, num_y,
                                        args.grid_model, args.color_model)

    if easter_eggs:
        place_easter_eggs(easter_eggs, input_vecs, positions, occupied,
                          output_image, args.tile_size, args.grid_model, args.color_model)

    fill_main(lib_tiles, input_vecs, positions, occupied, use_counts,
              output_image, args.tile_size, args.reuse_penalty)

    output_image.save(args.outfile, "JPEG", quality=92)
    logging.info("Wrote mosaic to %s", args.outfile)
    return 0


if __name__ == "__main__":
    sys.exit(main())

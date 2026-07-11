#!/usr/bin/env python3
import os
import sys
import argparse
import json
import logging
import collections
import numpy as np
from PIL import Image

# Ensure project root is in the Python search path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from pmosaic.io import load_image
from pmosaic.color import extract_target_cell_vec
from pmosaic.utils import safe_resize
from pmosaic.logging_setup import setup_logging

def load_library_records(libfiles_str):
    """
    Load library image records from a comma-separated list of JSON/JSONL file paths.
    """
    records = []
    if not libfiles_str:
        return records
        
    paths = [p.strip() for p in libfiles_str.split(',') if p.strip()]
    for path in paths:
        if not os.path.exists(path):
            logging.error(f"Library file not found: {path}")
            continue
        logging.info(f"Loading library: {path}")
        with open(path, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    records.append(json.loads(line))
                except json.JSONDecodeError as e:
                    logging.error(f"Failed to parse JSON line in library {path}: {e}")
    return records

def parse_candidates(records, grid_model, color_model):
    """
    Flatten and validate candidate tiles from library records.
    Returns a list of candidate dicts.
    """
    candidates = []
    for record in records:
        filename = record.get("filename")
        if not filename:
            continue
            
        for tile in record.get("tiles", []):
            color_vecs = tile.get("color_vecs", {})
            grid_data = color_vecs.get(grid_model)
            if not grid_data:
                continue
                
            # Support case-insensitive key search for color model
            vec = None
            for key in [color_model, color_model.upper(), color_model.lower(), "OKlab"]:
                if key in grid_data:
                    vec = grid_data[key]
                    break
                    
            if vec is None:
                continue
                
            candidates.append({
                "filename": filename,
                "x": tile["x"],
                "y": tile["y"],
                "width": tile["width"],
                "height": tile["height"],
                "md5": tile["md5"],
                "weight": float(tile.get("weight", 1.0)),
                "vector": np.array(vec, dtype=np.float32)
            })
    return candidates

def main():
    parser = argparse.ArgumentParser(description="Create a photomosaic from a target image using a tile library.")
    parser.add_argument("image_file", metavar="image-file", help="The target image to convert to a photomosaic.")
    parser.add_argument("--libfiles", required=True, help="Comma-separated list of JSON/JSONL library files.")
    parser.add_argument("--outfile", required=True, help="Path to write the output JPEG image.")
    parser.add_argument("--grid-model", default="2x2", choices=["2x2", "3x3"], help="Grid model to use.")
    parser.add_argument("--color-model", default="RGB", choices=["RGB", "Oklab"], help="Color model to use.")
    parser.add_argument("--tile-size", type=int, default=200, help="Size of output tiles.")
    parser.add_argument("--width", type=int, help="Output image width (default: target image width).")
    parser.add_argument("--height", type=int, help="Output image height (default: target image height).")
    parser.add_argument("--reuse-penalty", type=float, default=0.0, help="Penalty applied to reused tiles.")
    parser.add_argument("--easter-eggs", "--easter_eggs", help="Comma-separated list of easter egg JSON/JSONL library files.")
    parser.add_argument("--log", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"], help="Set the logging level.")
    
    args = parser.parse_args()
    setup_logging("mkpic", level_name=args.log)
    logger = logging.getLogger("mkpic")
    
    # 1. Load library data
    lib_records = load_library_records(args.libfiles)
    candidates = parse_candidates(lib_records, args.grid_model, args.color_model)
    if not candidates:
        logger.error("No valid candidate tiles found in the provided library files.")
        sys.exit(1)
    logger.info(f"Loaded {len(candidates)} candidate tiles from the library.")
    
    # 2. Load easter eggs
    ee_records = load_library_records(args.easter_eggs) if args.easter_eggs else []
    ee_candidates = parse_candidates(ee_records, args.grid_model, args.color_model)
    logger.info(f"Loaded {len(ee_candidates)} easter egg tiles.")
    
    # 3. Read target image and calculate output size
    try:
        input_image = load_image(args.image_file)
    except Exception as e:
        logger.error(f"Failed to load target image: {e}")
        sys.exit(1)
        
    input_w, input_h = input_image.size
    output_width = args.width if args.width is not None else input_w
    output_height = args.height if args.height is not None else input_h
    
    logger.info(f"Target image size: {input_w}x{input_h}")
    logger.info(f"Requested output size: {output_width}x{output_height}")
    
    # Divide output into tiles
    cols = output_width // args.tile_size
    rows = output_height // args.tile_size
    
    if cols <= 0 or rows <= 0:
        logger.error(f"Output dimensions ({output_width}x{output_height}) are too small for tile size {args.tile_size}")
        sys.exit(1)
        
    actual_out_w = cols * args.tile_size
    actual_out_h = rows * args.tile_size
    logger.info(f"Tiled grid size: {cols} cols x {rows} rows ({actual_out_w}x{actual_out_h} pixels)")
    
    # Create empty output image
    output_image = Image.new("RGB", (output_width, output_height), (0, 0, 0))
    
    # 4. Prepare target cell grid vectors
    input_arr = np.array(input_image)
    row_edges = np.linspace(0, input_h, rows + 1, dtype=int)
    col_edges = np.linspace(0, input_w, cols + 1, dtype=int)
    
    grid_size = 2 if args.grid_model == "2x2" else 3
    
    logger.info("Extracting target cell color vectors...")
    target_cells = []
    for r in range(rows):
        for c in range(cols):
            r_start, r_end = row_edges[r], row_edges[r+1]
            c_start, c_end = col_edges[c], col_edges[c+1]
            cell_rgb = input_arr[r_start:r_end, c_start:c_end]
            
            vec = extract_target_cell_vec(cell_rgb, grid_size, args.color_model)
            target_cells.append({
                "r": r,
                "c": c,
                "vector": vec
            })
            
    # Vectorized structures for distance calculations
    # Target vectors matrix: (rows*cols, D)
    target_matrix = np.stack([cell["vector"] for cell in target_cells], axis=0)
    
    # Candidate vectors matrix: (N, D)
    candidate_matrix = np.stack([cand["vector"] for cand in candidates], axis=0)
    candidate_weights = np.array([cand["weight"] for cand in candidates], dtype=np.float32)
    candidate_md5s = [cand["md5"] for cand in candidates]
    
    # Initialize trackers
    use_counts = collections.defaultdict(int)
    occupied_cells = set()
    loaded_images = {}
    
    def fetch_and_resize_tile(cand):
        filepath = cand["filename"]
        if filepath not in loaded_images:
            try:
                loaded_images[filepath] = load_image(filepath)
            except Exception as e:
                logger.error(f"Could not load library image {filepath}: {e}")
                return None
        img = loaded_images[filepath]
        try:
            tile_crop = img.crop((cand["x"], cand["y"], cand["x"] + cand["width"], cand["y"] + cand["height"]))
            return safe_resize(tile_crop, (args.tile_size, args.tile_size))
        except Exception as e:
            logger.error(f"Error cropping/resizing tile from {filepath}: {e}")
            return None

    # 5. Easter Eggs Pass
    if ee_candidates:
        logger.info("Processing Easter Eggs...")
        for ee_idx, ee_cand in enumerate(ee_candidates):
            ee_vec = ee_cand["vector"]
            # Distance from this easter egg to all target cell vectors
            diff = target_matrix - ee_vec
            distances = np.linalg.norm(diff, axis=1)
            
            # Sort target cells by distance
            sorted_indices = np.argsort(distances)
            
            # Find the closest unoccupied target cell
            found = False
            for idx in sorted_indices:
                cell = target_cells[idx]
                coord = (cell["r"], cell["c"])
                if coord not in occupied_cells:
                    occupied_cells.add(coord)
                    
                    # Fetch and paste easter egg tile
                    ee_tile = fetch_and_resize_tile(ee_cand)
                    if ee_tile:
                        paste_x = cell["c"] * args.tile_size
                        paste_y = cell["r"] * args.tile_size
                        output_image.paste(ee_tile, (paste_x, paste_y))
                        use_counts[ee_cand["md5"]] += 1
                        logger.info(f"Placed Easter Egg {ee_idx+1} at grid cell {coord} (distance: {distances[idx]:.4f})")
                        found = True
                    break
                    
            if not found:
                logger.warning(f"Could not place Easter Egg {ee_idx+1}: no unoccupied tiles left.")

    # 6. Main Match Pass
    logger.info("Running main matching pass...")
    placed_count = 0
    
    # Iterate through remaining target cells
    for cell_idx, cell in enumerate(target_cells):
        coord = (cell["r"], cell["c"])
        if coord in occupied_cells:
            continue
            
        # Target cell vector (D,)
        cell_vec = cell["vector"]
        
        # Euclidean distances to all candidates (N,)
        diff = candidate_matrix - cell_vec
        vec_distances = np.linalg.norm(diff, axis=1)
        
        # Weighted distances
        # distance = (1 + use_counts[md5] * reuse_penalty) / tile_weight * vec_distance
        reuse_penalties = 1.0 + np.array([use_counts[md5] for md5 in candidate_md5s], dtype=np.float32) * args.reuse_penalty
        weighted_distances = (reuse_penalties / candidate_weights) * vec_distances
        
        # Find best match
        best_idx = np.argmin(weighted_distances)
        best_cand = candidates[best_idx]
        
        # Fetch, resize, and paste tile
        matched_tile = fetch_and_resize_tile(best_cand)
        if matched_tile:
            paste_x = cell["c"] * args.tile_size
            paste_y = cell["r"] * args.tile_size
            output_image.paste(matched_tile, (paste_x, paste_y))
            use_counts[best_cand["md5"]] += 1
            placed_count += 1
        else:
            logger.error(f"Failed to place matched tile for cell {coord}")
            
        if (placed_count % 100 == 0 or cell_idx == len(target_cells) - 1) and placed_count > 0:
            logger.info(f"Placed {placed_count} library tiles...")

    # Crop the final output image to fit the exact tiled grid if the output dimensions 
    # were not a perfect multiple of tile_size (to prevent black edges).
    if output_width != actual_out_w or output_height != actual_out_h:
        logger.info(f"Cropping output image to actual tiled area: {actual_out_w}x{actual_out_h}")
        output_image = output_image.crop((0, 0, actual_out_w, actual_out_h))

    # 7. Write the output image
    logger.info(f"Writing output image to {args.outfile}")
    out_dir = os.path.dirname(os.path.abspath(args.outfile))
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
        
    try:
        output_image.save(args.outfile, format="JPEG", quality=95)
        logger.info("Photomosaic creation complete!")
    except Exception as e:
        logger.error(f"Failed to save output image: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
import os
import sys
import argparse
import json
import logging
import glob
import numpy as np

# Ensure project root is in the Python search path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from pmosaic.io import load_image
from pmosaic.color import extract_grid_vectors
from pmosaic.utils import crop_to_square, compute_tile_md5

def setup_logging(level_name):
    level = getattr(logging, level_name.upper(), logging.INFO)
    logging.basicConfig(
        level=level,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)]
    )

def resolve_files(patterns):
    """
    Resolve a list of files, directories, or glob patterns into a list of image files.
    """
    resolved = []
    supported_exts = ('.jpg', '.jpeg', '.png', '.heic', '.cr2')
    
    for pattern in patterns:
        if os.path.isdir(pattern):
            # Recursively walk directory
            for root, _, files in os.walk(pattern):
                for file in files:
                    if os.path.splitext(file)[1].lower() in supported_exts:
                        resolved.append(os.path.join(root, file))
        else:
            # Resolve as glob
            globbed = glob.glob(pattern, recursive=True)
            if globbed:
                for path in globbed:
                    if os.path.isfile(path) and os.path.splitext(path)[1].lower() in supported_exts:
                        resolved.append(path)
            elif os.path.isfile(pattern) and os.path.splitext(pattern)[1].lower() in supported_exts:
                resolved.append(pattern)
                
    return sorted(list(set(os.path.abspath(p) for p in resolved)))

def main():
    parser = argparse.ArgumentParser(description="Index an image library for photomosaic generation.")
    parser.add_argument("files", nargs="+", help="Image files, directories, or glob patterns to index.")
    parser.add_argument("--libfile", required=True, help="Path to the output JSON/JSONL library file.")
    parser.add_argument("--clear", action="store_true", help="Clear the library file before indexing.")
    parser.add_argument("--log", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"], help="Set the logging level.")
    
    args = parser.parse_args()
    setup_logging(args.log)
    logger = logging.getLogger("mklib")
    
    # Handle library clearing
    if args.clear and os.path.exists(args.libfile):
        logger.info(f"Clearing existing library file: {args.libfile}")
        try:
            os.remove(args.libfile)
        except Exception as e:
            logger.error(f"Failed to clear library file {args.libfile}: {e}")
            sys.exit(1)
            
    # Load already indexed filenames to prevent duplicate entries
    indexed_filenames = set()
    if os.path.exists(args.libfile):
        try:
            with open(args.libfile, "r") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        record = json.loads(line)
                        if "filename" in record:
                            indexed_filenames.add(os.path.abspath(record["filename"]))
                    except json.JSONDecodeError:
                        pass
        except Exception as e:
            logger.warning(f"Could not read existing library file for duplication check: {e}")

    # Resolve input files
    image_files = resolve_files(args.files)
    if not image_files:
        logger.error("No valid image files found to index.")
        sys.exit(1)
        
    logger.info(f"Found {len(image_files)} image files to process.")
    
    # Ensure parent directory for libfile exists
    lib_dir = os.path.dirname(os.path.abspath(args.libfile))
    if lib_dir:
        os.makedirs(lib_dir, exist_ok=True)
        
    indexed_count = 0
    skipped_count = 0
    
    with open(args.libfile, "a") as f_lib:
        for idx, filepath in enumerate(image_files):
            abs_path = os.path.abspath(filepath)
            
            if abs_path in indexed_filenames:
                logger.debug(f"Skipping already indexed file: {filepath}")
                skipped_count += 1
                continue
                
            logger.info(f"[{idx+1}/{len(image_files)}] Indexing: {filepath}")
            
            try:
                # Load image
                img = load_image(filepath)
                full_w, full_h = img.size
                
                # Center crop to square tile
                tile_img, x, y, tile_w, tile_h = crop_to_square(img)
                
                # Compute MD5 of raw uncompressed RGB pixel bytes
                md5_hash = compute_tile_md5(tile_img)
                
                # Extract color vectors
                tile_arr = np.array(tile_img)
                rgb_2x2, oklab_2x2 = extract_grid_vectors(tile_arr, 2)
                rgb_3x3, oklab_3x3 = extract_grid_vectors(tile_arr, 3)
                
                # Construct color vectors structure
                # Support both Oklab and OKlab keys for maximum compatibility
                color_vecs = {
                    "2x2": {
                        "RGB": rgb_2x2,
                        "Oklab": oklab_2x2,
                        "OKlab": oklab_2x2
                    },
                    "3x3": {
                        "RGB": rgb_3x3,
                        "Oklab": oklab_3x3,
                        "OKlab": oklab_3x3
                    }
                }
                
                # Tile record
                tile_record = {
                    "md5": md5_hash,
                    "x": x,
                    "y": y,
                    "width": tile_w,
                    "height": tile_h,
                    "color_vecs": color_vecs,
                    "weight": 1.0
                }
                
                # Image file record
                image_record = {
                    "filename": abs_path,
                    "width": full_w,
                    "height": full_h,
                    "tiles": [tile_record]
                }
                
                # Write to JSONL
                f_lib.write(json.dumps(image_record) + "\n")
                f_lib.flush()
                indexed_count += 1
                
            except Exception as e:
                logger.error(f"Error processing {filepath}: {e}", exc_info=True)
                
    logger.info(f"Indexing complete. Indexed: {indexed_count}, Skipped: {skipped_count}, Library size: {indexed_count + len(indexed_filenames)} records.")

if __name__ == "__main__":
    main()

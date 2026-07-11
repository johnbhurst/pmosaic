"""Reading and writing the JSON Lines library file.

Each line of a library file is a JSON object describing one source image and
the tile(s) extracted from it.
"""

import json
import logging


def append_record(libfile, record):
    """Append one image *record* to *libfile* as a JSON line."""
    with open(libfile, "a") as f:
        f.write(json.dumps(record) + "\n")


def load_library(paths):
    """Load and concatenate image records from one or more library files."""
    entries = []
    for path in paths:
        count = 0
        with open(path) as f:
            for lineno, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    entries.append(json.loads(line))
                    count += 1
                except json.JSONDecodeError as exc:
                    logging.error("%s:%d: skipping malformed record: %s", path, lineno, exc)
        logging.info("Loaded %d record(s) from %s", count, path)
    return entries

#!/usr/bin/env bash

# Exit immediately if a command exits with a non-zero status
set -euo pipefail

# Print usage information if directory argument is missing
if [ "$#" -ne 1 ]; then
    echo "Usage: $0 <directory>" >&2
    exit 1
fi

TARGET_DIR="$1"

# Check if target is a valid directory
if [ ! -d "$TARGET_DIR" ]; then
    echo "Error: '$TARGET_DIR' is not a directory." >&2
    exit 1
fi

# Determine the basename of the target directory to name the library file
LIB_NAME=$(basename "$TARGET_DIR")
LIB_FILE="${LIB_NAME}.json"

# Resolve the absolute path of mklib.py relative to this script's location
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MKLIB_PATH="${SCRIPT_DIR}/mklib.py"

# Verify that mklib.py exists and is executable
if [ ! -x "$MKLIB_PATH" ]; then
    echo "Error: '$MKLIB_PATH' not found or not executable." >&2
    exit 1
fi

echo "Scanning '$TARGET_DIR' for images to index into './$LIB_FILE'..."

# Find all files under the directory, filter for supported image extensions case-insensitively,
# and pass them robustly using null-terminated paths to mklib.py.
if command -v uv >/dev/null 2>&1; then
    find "$TARGET_DIR" -type f -print0 \
        | grep -z -i -E '\.(jpe?g|png|heic|cr2)$' \
        | xargs -r -0 uv run "$MKLIB_PATH" --libfile="$LIB_FILE"
else
    find "$TARGET_DIR" -type f -print0 \
        | grep -z -i -E '\.(jpe?g|png|heic|cr2)$' \
        | xargs -r -0 "$MKLIB_PATH" --libfile="$LIB_FILE"
fi

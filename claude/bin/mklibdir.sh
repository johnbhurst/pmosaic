#!/usr/bin/env bash
#
# Index every image under a directory into a library file.
#
# Usage:
#     bin/mklibdir.sh DIRECTORY
#
# Finds all image files (JPEG/JPG/PNG/HEIC/CR2, any case) under DIRECTORY and
# passes them to mklib.py.  The library file is named after the basename of
# DIRECTORY and written to the current working directory.

set -euo pipefail

if [[ $# -ne 1 ]]; then
    echo "Usage: $0 DIRECTORY" >&2
    exit 2
fi

dir=$1

if [[ ! -d $dir ]]; then
    echo "$0: not a directory: $dir" >&2
    exit 1
fi

# Library file named after the directory's basename, placed in the CWD.
libfile="$(basename -- "$dir").json"

# Locate mklib.py relative to this script and its uv project.
script_dir=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
project_dir=$(dirname -- "$script_dir")

# find    : emit every regular file, NUL-separated (robust to spaces/newlines).
# grep    : keep only recognised image extensions, case-insensitively (-z: NUL).
# xargs   : pass the matches as arguments to mklib.py (-0: NUL, -r: skip if empty).
find "$dir" -type f -print0 \
    | grep -z -i -E '\.(jpe?g|png|heic|cr2)$' \
    | xargs -0 -r uv run --project "$project_dir" "$script_dir/mklib.py" --libfile="$libfile"

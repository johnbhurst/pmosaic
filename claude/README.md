# Photomosaic (pmosaic)

Create a photomosaic of a target image using square tiles drawn from a library
of images. Works in two steps: **index the library**, then **build the mosaic**.

## Setup

Dependencies are managed with [uv](https://docs.astral.sh/uv/):

```bash
uv sync
```

CR2 (Canon raw) support requires `libraw` to be available for `rawpy`.

## 1. Index the library — `mklib.py`

```bash
uv run bin/mklib.py [--options] --libfile=library.json library-files...
```

For each image it crops a centered square tile, records an MD5 of the tile's
pixel data, and computes average-color vectors for every grid model
(`2x2`, `3x3`) and color model (`RGB`, `Oklab`). One JSON record is appended
per file to the library file (JSON Lines format).

Options:

- `-d`, `--debug` — enable debug logging.
- `--libfile` — library file to append to (required).

## 2. Build the mosaic — `mkpic.py`

```bash
uv run bin/mkpic.py [--options] --libfiles=library.json[,...] \
    --outfile=output.jpg image-file
```

Options:

- `--grid-model={2x2|3x3}` (default `2x2`)
- `--color-model={RGB|Oklab}` (default `RGB`)
- `--tile-size=N` (default `200`)
- `--width=N` / `--height=N` (default: input image dimensions)
- `--reuse-penalty=F` (default `0`) — weighted distance is
  `(1 + use_count * reuse_penalty) / weight * euclidean_distance`, so a tile is
  penalised each time it is reused and `weight > 1` encourages a tile's use.
- `--easter_eggs=library.json[,...]` — each easter-egg image is placed exactly
  once, at its best-matching position, before the main pass fills the rest.

Supported input formats: JPEG, PNG, HEIC, CR2 (case-insensitive extensions).
Output is always JPEG.

## Layout

```
bin/mklib.py          indexer CLI
bin/mkpic.py          mosaic-builder CLI
pmosaic/color.py      grid/color models and color vectors
pmosaic/tiles.py      square crop, geometry, MD5
pmosaic/imaging.py    format-agnostic image loading
pmosaic/library.py    JSON Lines read/write
pmosaic/logging_setup.py
```

# Simple Photo Mosaics in Python

This repo contains a couple of programs for creating a mosaic - an image composed of tiles from an image library.

## mklib.py

The first program analyzes a collection of images and writes their average quadrant RGB values into a library JSON file, which is used for later processing.

``` bash
bin/mklib.py [options] --libfile=library-file.json image-files
```

## mkpic.py

The second program takes a target image file and creates a mosaic of it, using best-matching tiles from the library.

``` bash
bin/mklib.py [options] --libfile=library-file.json --outfile=output.jpg image.jpg
```

`mkpic.py` supports options to control the size and makeup of the output image.

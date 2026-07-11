"""Square-tile extraction and geometry."""

import hashlib


def square_box(width, height):
    """Return the ``(x, y, size)`` of the centered square crop of a rectangle.

    Crops horizontally or vertically as needed so the result is square.
    """
    if width > height:
        size = height
        return (width - height) // 2, 0, size
    if height > width:
        size = width
        return 0, (height - width) // 2, size
    return 0, 0, width


def crop_square(image):
    """Center-crop *image* to a square ``PIL.Image``, returning it with its box.

    Returns ``(square_image, x, y, size)`` where ``x``/``y`` are the offset of
    the crop within the original image.
    """
    width, height = image.size
    x, y, size = square_box(width, height)
    square = image.crop((x, y, x + size, y + size))
    return square, x, y, size


def tile_md5(square_image):
    """MD5 hash (hex) of the raw pixel bytes of a square tile image."""
    return hashlib.md5(square_image.tobytes()).hexdigest()

"""Format-agnostic image loading.

Supports JPEG, PNG, HEIC and CR2 (Canon raw), with case-insensitive
extensions.  All images are returned as RGB ``PIL.Image`` objects with EXIF
orientation already applied.
"""

import logging
from pathlib import Path

from PIL import Image, ImageOps

try:
    import pillow_heif

    pillow_heif.register_heif_opener()
except Exception as exc:  # pragma: no cover - environment dependent
    logging.warning("HEIC support unavailable (pillow-heif failed to load): %s", exc)

RAW_EXTENSIONS = {".cr2"}


def load_image(path):
    """Load an image from *path* as an RGB ``PIL.Image``.

    Raw formats (CR2) are decoded with ``rawpy``; everything else goes through
    Pillow (HEIC handled via the registered pillow-heif opener).
    """
    ext = Path(path).suffix.lower()

    if ext in RAW_EXTENSIONS:
        import rawpy  # imported lazily; libraw only needed for raw files.

        with rawpy.imread(str(path)) as raw:
            rgb = raw.postprocess()
        return Image.fromarray(rgb)

    with Image.open(path) as img:
        img = ImageOps.exif_transpose(img)
        return img.convert("RGB")

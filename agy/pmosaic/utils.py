import hashlib
import numpy as np
from PIL import Image

def crop_to_square(img):
    """
    Extract a square tile from the rectangular PIL Image by cropping
    horizontally or vertically as necessary (centered crop).
    
    Returns:
        cropped_img: PIL Image of shape (S, S)
        x: x offset in original image
        y: y offset in original image
        w: width of cropped tile (S)
        h: height of cropped tile (S)
    """
    width, height = img.size
    
    if width > height:
        # Landcsape: Crop horizontally
        left = (width - height) // 2
        top = 0
        s = height
    elif height > width:
        # Portrait: Crop vertically
        left = 0
        top = (height - width) // 2
        s = width
    else:
        # Already square
        left = 0
        top = 0
        s = width
        
    cropped_img = img.crop((left, top, left + s, top + s))
    return cropped_img, left, top, s, s

def compute_tile_md5(tile_img):
    """
    Compute a MD5 hash for the binary square tile image data.
    The user selected to hash the raw, uncompressed RGB pixel bytes.
    """
    # Convert PIL Image to a numpy array of shape (S, S, 3)
    arr = np.array(tile_img)
    # Get raw contiguous byte representation
    data_bytes = arr.tobytes()
    return hashlib.md5(data_bytes).hexdigest()

def safe_resize(img, size):
    """
    Resize a PIL Image using Lanczos interpolation, compatible with
    both older and newer versions of Pillow.
    """
    try:
        return img.resize(size, Image.Resampling.LANCZOS)
    except AttributeError:
        return img.resize(size, Image.LANCZOS)


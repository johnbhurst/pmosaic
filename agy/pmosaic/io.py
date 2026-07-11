import os
import logging
from PIL import Image
import rawpy
from pillow_heif import register_heif_opener

# Register HEIF opener to let Pillow open .heic files transparently
register_heif_opener()

logger = logging.getLogger(__name__)

def load_image(filepath):
    """
    Load an image from filepath. Supports JPEG, PNG, HEIC, and CR2.
    Converts and returns a PIL Image in 'RGB' mode.
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
        
    ext = os.path.splitext(filepath)[1].lower()
    
    try:
        if ext == '.cr2':
            logger.debug(f"Loading raw CR2 image: {filepath}")
            with rawpy.imread(filepath) as raw:
                # postprocess returns a uint8 RGB numpy array
                rgb_array = raw.postprocess()
                return Image.fromarray(rgb_array)
        else:
            logger.debug(f"Loading image with Pillow: {filepath}")
            img = Image.open(filepath)
            # Ensure image is in RGB mode (e.g., convert RGBA or grayscale)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            return img
    except Exception as e:
        logger.error(f"Failed to load image {filepath}: {e}")
        raise

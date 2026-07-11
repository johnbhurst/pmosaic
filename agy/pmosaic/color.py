import numpy as np

def srgb_to_linear(srgb):
    """
    Convert sRGB values to linear RGB.
    srgb should be a numpy array with values in [0, 1].
    """
    limit = 0.04045
    return np.where(srgb <= limit, srgb / 12.92, ((srgb + 0.055) / 1.055) ** 2.4)

def linear_to_lms(linear_rgb):
    """
    Convert linear RGB to LMS color space.
    """
    r = linear_rgb[..., 0]
    g = linear_rgb[..., 1]
    b = linear_rgb[..., 2]
    
    l = 0.4122214708 * r + 0.5363113620 * g + 0.0514459919 * b
    m = 0.2119034982 * r + 0.6806995451 * g + 0.1073969166 * b
    s = 0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b
    
    return l, m, s

def lms_to_lms_prime(l, m, s):
    """
    Apply non-linear behavior (cube root) to LMS.
    Handles negative values safely using np.cbrt.
    """
    return np.cbrt(l), np.cbrt(m), np.cbrt(s)

def lms_prime_to_oklab(l_prime, m_prime, s_prime):
    """
    Convert LMS prime to Oklab coordinates (L, a, b).
    """
    L = 0.2104542553 * l_prime + 0.7936177850 * m_prime - 0.0040720468 * s_prime
    a = 1.9779984951 * l_prime - 2.4285922050 * m_prime + 0.4505937099 * s_prime
    b = 0.0259040371 * l_prime + 0.7827717662 * m_prime - 0.8086757660 * s_prime
    return L, a, b

def rgb_to_oklab(rgb_array):
    """
    Convert an RGB image (values in [0, 255]) to Oklab coordinates.
    Returns a numpy array of the same shape with Oklab values.
    """
    srgb = rgb_array.astype(np.float32) / 255.0
    linear = srgb_to_linear(srgb)
    l, m, s = linear_to_lms(linear)
    l_p, m_p, s_p = lms_to_lms_prime(l, m, s)
    L, a, b = lms_prime_to_oklab(l_p, m_p, s_p)
    return np.stack([L, a, b], axis=-1)

def extract_grid_vectors(tile_rgb, grid_size):
    """
    Divide tile_rgb (numpy array of shape (H, W, 3), values in [0, 255])
    into a grid_size x grid_size grid.
    Compute the average color of each grid cell.
    Returns:
        rgb_vector: a list of grid_size*grid_size*3 floats (normalized [0, 1])
        oklab_vector: a list of grid_size*grid_size*3 floats
    """
    H, W, _ = tile_rgb.shape
    row_edges = np.linspace(0, H, grid_size + 1, dtype=int)
    col_edges = np.linspace(0, W, grid_size + 1, dtype=int)
    
    # Pre-calculate Oklab representation of the whole tile
    tile_oklab = rgb_to_oklab(tile_rgb)
    
    rgb_vector = []
    oklab_vector = []
    
    for r in range(grid_size):
        for c in range(grid_size):
            r_start, r_end = row_edges[r], row_edges[r+1]
            c_start, c_end = col_edges[c], col_edges[c+1]
            
            # Slice cell
            cell_rgb = tile_rgb[r_start:r_end, c_start:c_end]
            cell_oklab = tile_oklab[r_start:r_end, c_start:c_end]
            
            # Average cell colors
            # RGB is converted to [0, 1] range for consistency with Oklab L channel
            mean_rgb = np.mean(cell_rgb, axis=(0, 1)) / 255.0
            mean_oklab = np.mean(cell_oklab, axis=(0, 1))
            
            rgb_vector.extend(mean_rgb.tolist())
            oklab_vector.extend(mean_oklab.tolist())
            
    return rgb_vector, oklab_vector

def extract_target_cell_vec(cell_rgb, grid_size, color_model):
    """
    Extract the color vector for a target cell.
    cell_rgb is a numpy array of shape (H, W, 3) (values in [0, 255]).
    grid_size is 2 or 3.
    color_model is 'RGB' or 'Oklab' (case-insensitive).
    """
    if color_model.lower() == 'oklab':
        cell_data = rgb_to_oklab(cell_rgb)
    else:
        cell_data = cell_rgb.astype(np.float32) / 255.0
        
    H, W, _ = cell_data.shape
    row_edges = np.linspace(0, H, grid_size + 1, dtype=int)
    col_edges = np.linspace(0, W, grid_size + 1, dtype=int)
    
    vec = []
    for r in range(grid_size):
        for c in range(grid_size):
            r_start, r_end = row_edges[r], row_edges[r+1]
            c_start, c_end = col_edges[c], col_edges[c+1]
            sub_cell = cell_data[r_start:r_end, c_start:c_end]
            if sub_cell.size > 0:
                mean_val = np.mean(sub_cell, axis=(0, 1))
            else:
                mean_val = np.zeros(3, dtype=np.float32)
            vec.extend(mean_val.tolist())
            
    return np.array(vec, dtype=np.float32)


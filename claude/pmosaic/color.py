"""Grid models, color models and average-color vectors.

A *color vector* summarises a square tile by dividing it into a grid of cells
and recording the average color of each cell.  Cells are visited in row-major
order and each cell contributes its channels contiguously, so a 2x2 grid yields
a 12-dimensional vector (2*2*3) and a 3x3 grid a 27-dimensional vector (3*3*3).
"""

import numpy as np

# Grid model name -> (rows, cols).
GRID_MODELS = {
    "2x2": (2, 2),
    "3x3": (3, 3),
}

# Supported color models.
COLOR_MODELS = ("RGB", "Oklab")


def _srgb_to_linear(c):
    """Convert sRGB channel values in [0, 1] to linear light."""
    return np.where(c <= 0.04045, c / 12.92, ((c + 0.055) / 1.055) ** 2.4)


def rgb_to_oklab(arr):
    """Convert an ``H x W x 3`` array of sRGB values (0-255) to Oklab.

    Uses Björn Ottosson's Oklab transform.  Returns a float64 array of the same
    leading shape with channels (L, a, b).
    """
    c = arr.astype(np.float64) / 255.0
    lin = _srgb_to_linear(c)
    r, g, b = lin[..., 0], lin[..., 1], lin[..., 2]

    l = 0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b
    m = 0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b
    s = 0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b

    l_ = np.cbrt(l)
    m_ = np.cbrt(m)
    s_ = np.cbrt(s)

    ok_l = 0.2104542553 * l_ + 0.7936177850 * m_ - 0.0040720468 * s_
    ok_a = 1.9779984951 * l_ - 2.4285922050 * m_ + 0.4505937099 * s_
    ok_b = 0.0259040371 * l_ + 0.7827717662 * m_ - 0.8086757660 * s_

    return np.stack([ok_l, ok_a, ok_b], axis=-1)


def _cell_means(data, rows, cols):
    """Average each cell of a ``rows x cols`` grid over an ``H x W x C`` array.

    Returns a ``(rows*cols, C)`` array in row-major cell order.
    """
    h, w = data.shape[:2]
    channels = data.shape[2]
    ys = np.linspace(0, h, rows + 1).astype(int)
    xs = np.linspace(0, w, cols + 1).astype(int)

    out = np.empty((rows * cols, channels), dtype=np.float64)
    k = 0
    for r in range(rows):
        for c in range(cols):
            cell = data[ys[r]:ys[r + 1], xs[c]:xs[c + 1]]
            if cell.size == 0:
                out[k] = 0.0
            else:
                out[k] = cell.reshape(-1, channels).mean(axis=0)
            k += 1
    return out


def color_vector(arr, grid_model, color_model):
    """Compute the color vector for image *arr* under a grid and color model.

    *arr* is an ``H x W x 3`` (or more) RGB array with values in 0-255.
    Returns a 1-D float64 NumPy array.
    """
    if grid_model not in GRID_MODELS:
        raise ValueError(f"Unknown grid model: {grid_model!r}")

    rows, cols = GRID_MODELS[grid_model]
    rgb = arr[..., :3]

    if color_model == "RGB":
        data = rgb.astype(np.float64)
    elif color_model == "Oklab":
        data = rgb_to_oklab(rgb)
    else:
        raise ValueError(f"Unknown color model: {color_model!r}")

    return _cell_means(data, rows, cols).reshape(-1)


def all_color_vecs(arr):
    """Compute vectors for every grid/color model, as ``dict[grid][color] = list``."""
    return {
        grid: {color: color_vector(arr, grid, color).tolist() for color in COLOR_MODELS}
        for grid in GRID_MODELS
    }


def vec_distance(a, b):
    """Euclidean distance between two vectors."""
    a = np.asarray(a, dtype=np.float64)
    b = np.asarray(b, dtype=np.float64)
    return float(np.linalg.norm(a - b))

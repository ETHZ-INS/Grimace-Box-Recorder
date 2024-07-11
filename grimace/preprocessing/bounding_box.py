import numpy as np


def square_bounding_box(bounding_box) -> np.ndarray:
    x1, y1, x2, y2 = bounding_box

    width = x2 - x1
    height = y2 - y1

    if width > height:
        delta = width - height
        y1 -= delta // 2
        y2 += delta - delta // 2
    else:
        delta = height - width
        x1 -= delta // 2
        x2 += delta - delta // 2

    return np.array([x1, y1, x2, y2])


def pad_bounding_box(bounding_box, padding) -> np.ndarray:
    x1, y1, x2, y2 = bounding_box

    width = x2 - x1
    height = y2 - y1

    x_padding = int(padding * width)
    y_padding = int(padding * height)
    x1 = x1 - x_padding
    y1 = y1 - y_padding
    x2 = x2 + x_padding
    y2 = y2 + y_padding

    return np.array([x1, y1, x2, y2])


def crop_image_to_bounding_box(image, bounding_box):
    """
    Crop the image to the bounding box, fill with black if the bounding box crosses the image borders
    """

    x1, y1, x2, y2 = bounding_box

    width = x2 - x1
    height = y2 - y1

    black_image = np.zeros((height, width, image.shape[2]), dtype=image.dtype)

    x1_in = max(0, x1)
    y1_in = max(0, y1)
    x2_in = min(image.shape[1], x2)
    y2_in = min(image.shape[0], y2)

    x1_out = max(0, -x1)
    y1_out = max(0, -y1)
    x2_out = x1_out + x2_in - x1_in
    y2_out = y1_out + y2_in - y1_in

    black_image[y1_out:y2_out, x1_out:x2_out] = image[y1_in:y2_in, x1_in:x2_in]

    return black_image

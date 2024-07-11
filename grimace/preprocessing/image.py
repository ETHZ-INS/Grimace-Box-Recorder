import math

import cv2
import numpy as np


def average_channels(image: np.ndarray) -> np.ndarray:
    # Convert to grayscale by averaging the channels
    # (height, width, num_channels) -> (height, width, 1)
    return np.mean(image, axis=2, keepdims=True)


def resize_image_keep_aspect_ratio(image, target_width, target_height, interpolation=cv2.INTER_LINEAR) -> np.ndarray:
    # Resize the image to the target size while keeping the aspect ratio
    # (height, width) -> (new_height, new_width) |
    # new_height <= target_height, new_width <= target_width |
    # new_height / new_width == height / width

    height = image.shape[0]
    width = image.shape[1]
    aspect_ratio = width / height

    if aspect_ratio > 1:
        new_width = target_width
        new_height = int(new_width / aspect_ratio)
    else:
        new_height = target_height
        new_width = int(new_height * aspect_ratio)

    return cv2.resize(image, (new_width, new_height), interpolation=interpolation)


def crop_image_to_square(image: np.ndarray) -> np.ndarray:
    # Crop the image to a square
    # (height, width) -> (min(height, width), min(height, width))

    height = image.shape[0]
    width = image.shape[1]

    if height == width:
        return image

    d = abs(height - width)
    dl = math.floor(d / 2)
    dr = math.ceil(d / 2)

    if height > width:
        return image[dl:height-dr, :]
    else:
        return image[:, dl:width-dr]


def pad_image_to_size(image: np.ndarray, target_width, target_height, value=0.0) -> np.ndarray:
    # Pad the image to the target size
    # (height, width) -> (target_height, target_width)

    height = image.shape[0]
    width = image.shape[1]

    if height > target_height:
        raise ValueError(f"Height of image is greater than target height: {height} > {target_height}")
    if width > target_width:
        raise ValueError(f"Width of image is greater than target width: {width} > {target_width}")

    top_pad = (target_height - height) // 2
    bottom_pad = target_height - height - top_pad
    left_pad = (target_width - width) // 2
    right_pad = target_width - width - left_pad

    return cv2.copyMakeBorder(image, top_pad, bottom_pad, left_pad, right_pad, cv2.BORDER_CONSTANT, value=[value])
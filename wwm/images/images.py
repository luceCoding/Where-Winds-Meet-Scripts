from importlib import resources
import numpy as np
import cv2 as cv


def get_gray_template_image(template_name):

    with resources.open_binary("wwm.images", template_name) as template_file:
        # Read the file into a numpy array
        file_bytes = np.frombuffer(template_file.read(), np.uint8)
        # decode as grayscale
        return cv.imdecode(file_bytes, cv.IMREAD_GRAYSCALE)


def has_bottom_black_letterbox(image, n_rows=75, min_black=1):
    arr = np.array(image)

    bottom_band = arr[-(n_rows + 25):-25, :, :]
    bottom_mean = bottom_band.mean()

    print(bottom_mean)

    if bottom_mean < min_black:  # Look for black pixels
        return True
    return False


def has_bottom_gray_letterbox(image, n_rows=75, min_gray=47, max_gray=53):
    arr = np.array(image)

    bottom_band = arr[-(n_rows + 25):-25, :, :]
    bottom_mean = bottom_band.mean()

    print(bottom_mean)

    if bottom_mean < max_gray and bottom_mean > min_gray:  # Look for grayish pixels
        return True
    return False


def has_bottom_white_letterbox(image, n_rows=75, min_white=200):
    arr = np.array(image)

    bottom_band = arr[-(n_rows + 25):-25, :, :]
    bottom_mean = bottom_band.mean()

    print(bottom_mean)

    if bottom_mean > min_white:  # Look for white pixels
        return True
    return False


def get_crop_around(img_gray, x, y, size=64):
    half = size // 2

    y1 = max(0, y - half)
    y2 = min(img_gray.shape[0], y + half)
    x1 = max(0, x - half)
    x2 = min(img_gray.shape[1], x + half)

    crop = img_gray[y1:y2, x1:x2].copy()
    return crop


def get_image_similarity(image_a, image_b):
    res = cv.matchTemplate(image_a, image_b, cv.TM_CCOEFF_NORMED)
    return float(res[0][0])  # single similarity value
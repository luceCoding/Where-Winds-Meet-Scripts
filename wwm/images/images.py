from importlib import resources
import numpy as np
import cv2 as cv


def get_gray_template_image(template_name):

    with resources.open_binary("wwm.images", template_name) as template_file:
        # Read the file into a numpy array
        file_bytes = np.frombuffer(template_file.read(), np.uint8)
        # decode as grayscale
        return cv.imdecode(file_bytes, cv.IMREAD_GRAYSCALE)


def has_bottom_letterbox(image, n_rows=100, min_black=5):
    arr = np.array(image)

    bottom_band = arr[-(n_rows + 25):-25, :, :]
    bottom_mean = bottom_band.mean()

    print(bottom_mean)

    if bottom_mean < min_black:  # Look for black pixels
        return True
    return False

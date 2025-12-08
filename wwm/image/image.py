import logging
from importlib import resources
import numpy as np
import cv2 as cv

logger = logging.getLogger(__name__)


def get_gray_template_image(template_name):
    search_paths = [
        "wwm.image.templates.materials",
        "wwm.image.templates.waypoints",
    ]

    for pkg in search_paths:
        if resources.files(pkg).joinpath(template_name).is_file():
            with resources.open_binary(pkg, template_name) as template_file:
                file_bytes = np.frombuffer(template_file.read(), np.uint8)
                return cv.imdecode(file_bytes, cv.IMREAD_GRAYSCALE)

    raise FileNotFoundError(
        f"Template '{template_name}' not found in materials or waypoints."
    )


def list_png_files(folder_name):
    """
    folder_name: e.g. "materials" or "waypoints"
    """
    package = resources.files(f"wwm.image.templates.{folder_name}")
    return [
        entry.name
        for entry in package.iterdir()
        if entry.suffix.lower() == ".png"
    ]


def has_bottom_black_letterbox(image, n_rows=75, min_black=1):
    arr = np.array(image)

    bottom_band = arr[-(n_rows + 25):-25, :, :]
    bottom_mean = bottom_band.mean()

    # print(bottom_mean)

    if bottom_mean < min_black:  # Look for black pixels
        return True
    return False


def has_center_gray_band(image, n_rows=100, min_gray=45, max_gray=50, threshold=0.18):
    """
    Checks if the horizontal center band of the image is mostly gray.

    image: np.array (H x W x C)
    n_rows: height of the band
    min_gray, max_gray: grayscale intensity range to consider as gray
    threshold: fraction of pixels that must be gray to return True
    """
    band = get_horizontal_center_band(image, n_rows=n_rows)

    # Convert to grayscale
    gray_band = cv.cvtColor(band, cv.COLOR_BGR2GRAY)

    # Count how many pixels fall in the gray range
    gray_pixels = ((gray_band >= min_gray) & (gray_band <= max_gray)).sum()
    total_pixels = gray_band.size

    fraction_gray = gray_pixels / total_pixels

    logger.debug(
        f"Gray fraction: {fraction_gray:.2f} | Mean intensity: {gray_band.mean():.2f}")

    return fraction_gray >= threshold


def get_horizontal_center_band(image, n_rows=100):
    """
    Returns a horizontal band (strip) across the center of the image.

    image: np.array (H x W x C)
    n_rows: number of rows to include in the band
    """
    arr = np.array(image)
    h = arr.shape[0]

    # Calculate start and end rows for center band
    start_row = h // 2 - n_rows // 2
    end_row = start_row + n_rows

    center_band = arr[start_row:end_row, :, :]
    return center_band


def has_bottom_white_letterbox(image, n_rows=75, min_white=200):
    arr = np.array(image)

    bottom_band = arr[-(n_rows):, :, :]
    bottom_mean = bottom_band.mean()

    # print(bottom_mean)

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


def blackout_roi(image, coord_a, coord_b):
    """
    Blacks out a rectangular region of an image in-place.

    Parameters:
        image (np.ndarray): The image array (H x W x 3).
        coord_a (tuple): (x1, y1) of one corner.
        coord_b (tuple): (x2, y2) of the opposite corner.

    Returns:
        np.ndarray: The modified image (same object).
    """

    # Extract coordinates
    x1, y1 = coord_a
    x2, y2 = coord_b

    # Normalize coordinates so (x1,y1) is top-left,
    # (x2,y2) is bottom-right regardless of input order
    x_min, x_max = sorted([x1, x2])
    y_min, y_max = sorted([y1, y2])

    # Clip to image boundaries to avoid errors
    h, w = image.shape[:2]
    x_min = max(0, min(x_min, w))
    x_max = max(0, min(x_max, w))
    y_min = max(0, min(y_min, h))
    y_max = max(0, min(y_max, h))

    # Blackout the region
    image[y_min:y_max, x_min:x_max] = 0

    return image


def apply_map_mask(image):
    # Only works on 1600x900 resolution
    image = blackout_roi(image, (0, 550), (450, 750))
    image = blackout_roi(image, (0, 750), (600, 900))
    image = blackout_roi(image, (1367, 181), (1618, 430))
    return image


def get_coords_template_match(img_gray, template_name, threshold=0.75, nms_thresh=0.3):

    template_gray = get_gray_template_image(template_name)
    assert template_gray is not None, "template file could not be read"
    h, w = template_gray.shape

    # Template matching
    res = cv.matchTemplate(img_gray, template_gray, cv.TM_CCOEFF_NORMED)
    loc = np.where(res >= threshold)

    # Build boxes for NMS
    boxes = []
    scores = []
    for pt in zip(*loc[::-1]):  # (x, y)
        boxes.append([pt[0], pt[1], w, h])  # x, y, width, height
        scores.append(res[pt[1], pt[0]])

    if not boxes:
        return [], img_gray

    boxes = np.array(boxes).tolist()
    scores = np.array(scores).tolist()

    # OpenCV NMS
    indices = cv.dnn.NMSBoxes(
        boxes, scores, score_threshold=threshold, nms_threshold=nms_thresh)

    coords = []
    for i in indices:
        i = i[0] if isinstance(i, (list, np.ndarray)) else i
        x, y, w_box, h_box = boxes[i]
        cx = x + w_box // 2
        cy = y + h_box // 2
        coords.append((cx, cy))

    return coords, img_gray

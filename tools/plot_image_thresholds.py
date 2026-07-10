import os
import cv2 as cv
import matplotlib.pyplot as plt
import argparse
import glob
import math
import numpy as np


def preprocess_blur_and_color(bgr_img, lower_color, upper_color):
    """Blur → HSV mask → grayscale."""
    img_blur = cv.GaussianBlur(bgr_img, (3, 3), 0)
    hsv = cv.cvtColor(img_blur, cv.COLOR_BGR2HSV)
    mask = cv.inRange(hsv, np.array(lower_color), np.array(upper_color))
    masked = cv.bitwise_and(img_blur, img_blur, mask=mask)
    return cv.cvtColor(masked, cv.COLOR_BGR2GRAY)


def preprocess_color_only(bgr_img, lower_color, upper_color):
    """HSV mask only → grayscale."""
    hsv = cv.cvtColor(bgr_img, cv.COLOR_BGR2HSV)
    mask = cv.inRange(hsv, np.array(lower_color), np.array(upper_color))
    masked = cv.bitwise_and(bgr_img, bgr_img, mask=mask)
    return cv.cvtColor(masked, cv.COLOR_BGR2GRAY)


def load_image_from_folder(images_dir, filename):
    """Load an image by name or most recent."""
    if filename:
        path = os.path.join(images_dir, filename)
        if not os.path.exists(path):
            raise FileNotFoundError(f"{filename} not found in images/")
        return path

    files = glob.glob(os.path.join(images_dir, "*.*"))
    if not files:
        raise FileNotFoundError("No images found in images/ folder")

    return max(files, key=os.path.getmtime)


def pixel_percent_white(img):
    white = cv.countNonZero(img)
    return (white / img.size) * 100


def plot_image_thresholds(filename, threshold, lower_color, upper_color):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    images_dir = os.path.join(script_dir, "images")

    image_path = load_image_from_folder(images_dir, filename)
    img = cv.imread(image_path)
    if img is None:
        raise RuntimeError("Failed to load image")

    # Preprocessed versions
    gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)
    gray_pre = preprocess_blur_and_color(img, lower_color, upper_color)
    gray_color_only = preprocess_color_only(img, lower_color, upper_color)

    # Histogram plot
    hist = cv.calcHist([gray], [0], None, [256], [0, 256])
    plt.figure()
    plt.plot(hist)
    plt.title("Grayscale Histogram")
    plt.xlabel("Bins")
    plt.ylabel("Pixels")
    plt.show()

    # Threshold operations
    threshold_ops = [
        ("Binary",       cv.THRESH_BINARY,          threshold),
        ("BinaryInv",    cv.THRESH_BINARY_INV,      threshold),
        ("ToZero",       cv.THRESH_TOZERO,          threshold),
        ("ToZeroInv",    cv.THRESH_TOZERO_INV,      threshold),
        ("Trunc",        cv.THRESH_TRUNC,           threshold),
        ("Otsu",         cv.THRESH_BINARY + cv.THRESH_OTSU, 0),
    ]

    # Build a list of plots to display
    plots = [
        ("Original", cv.cvtColor(img, cv.COLOR_BGR2RGB)),
        ("Grayscale", gray),
        (f"Color Filter ({pixel_percent_white(gray_color_only):.3f}%)",
         gray_color_only)
    ]

    # Add thresholded images
    for name, opt, th in threshold_ops:
        _, processed = cv.threshold(gray_pre, th, 255, opt)
        plots.append((f"{name} ({pixel_percent_white(processed):.3f}%)",
                      processed))

    # Calculate grid
    cols = 3
    rows = math.ceil(len(plots) / cols)

    plt.figure(figsize=(12, rows * 4))

    # Draw each plot
    for i, (title, img_data) in enumerate(plots, start=1):
        plt.subplot(rows, cols, i)
        if len(img_data.shape) == 2:
            plt.imshow(img_data, cmap="gray")
        else:
            plt.imshow(img_data)
        plt.title(title)
        plt.axis("off")

    plt.tight_layout()
    plt.show()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Plot image thresholds")
    parser.add_argument("--filename", type=str, default=None)
    parser.add_argument("--threshold", type=int, required=True)
    parser.add_argument("--lower_color", type=int, nargs=3, default=[0, 0, 0])
    parser.add_argument("--upper_color", type=int,
                        nargs=3, default=[255, 255, 255])
    args = parser.parse_args()

    plot_image_thresholds(args.filename, args.threshold,
                          args.lower_color, args.upper_color)

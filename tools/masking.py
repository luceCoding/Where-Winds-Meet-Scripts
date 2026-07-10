import cv2 as cv
from wwm.window import Window
from wwm.image import image


def blackout_region(img, x1, y1, x2, y2):
    """Black out a rectangular region."""
    x_min, x_max = sorted([x1, x2])
    y_min, y_max = sorted([y1, y2])
    img[y_min:y_max, x_min:x_max] = 0
    return img


# -----------------------------
# Load Screenshot
# -----------------------------
window = Window()
orig = window.get_screenshot()
assert orig is not None, "Screenshot could not be captured."

h, w = orig.shape[:2]

# Create window for trackbars
cv.namedWindow("Mask Adjuster")


# -----------------------------
# Create Trackbars
# -----------------------------
cv.createTrackbar("x1", "Mask Adjuster", 0, w, lambda x: None)
cv.createTrackbar("y1", "Mask Adjuster", 0, h, lambda x: None)
cv.createTrackbar("x2", "Mask Adjuster", w, w, lambda x: None)
cv.createTrackbar("y2", "Mask Adjuster", h, h, lambda x: None)


# -----------------------------
# Live Update Loop
# -----------------------------
while True:
    img = orig.copy()

    # Read trackbar values
    x1 = cv.getTrackbarPos("x1", "Mask Adjuster")
    y1 = cv.getTrackbarPos("y1", "Mask Adjuster")
    x2 = cv.getTrackbarPos("x2", "Mask Adjuster")
    y2 = cv.getTrackbarPos("y2", "Mask Adjuster")

    # Apply the mask
    blackout_region(img, x1, y1, x2, y2)

    # Show the updated image
    cv.imshow("Mask Adjuster", img)

    # Press ESC to exit
    if cv.waitKey(10) == 27:
        break

cv.destroyAllWindows()

final_img = image.apply_map_mask(orig)

cv.imshow("Final masked image.", final_img)
cv.waitKey(0)  # Wait until any key is pressed
cv.destroyAllWindows()

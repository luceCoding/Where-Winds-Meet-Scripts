import cv2
import numpy as np
import os

def nothing(x):
    pass

def main():
    # ---- Paths ----
    IMAGE_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "images")
    IMAGE_WINDOW = "Image"
    TRACK_WINDOW = "Controls"

    # ---- Get image files ----
    files = [f for f in os.listdir(IMAGE_FOLDER)
             if f.lower().endswith((".png", ".jpg", ".jpeg", ".bmp"))]
    if not files:
        print("No images found in the 'images' folder!")
        return
    index = 0

    # ---- Trackbar setup ----
    trackbars = {
        "H low": 0,
        "H high": 179,
        "S low": 0,
        "S high": 255,
        "V low": 0,
        "V high": 255
    }

    # ---- Create windows ----
    cv2.namedWindow(IMAGE_WINDOW)
    cv2.namedWindow(TRACK_WINDOW, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(TRACK_WINDOW, 400, 300)

    # Position windows
    cv2.moveWindow(IMAGE_WINDOW, 100, 100)
    cv2.moveWindow(TRACK_WINDOW, 900, 100)

    # Create trackbars
    for name, val in trackbars.items():
        max_val = 179 if "H" in name else 255
        cv2.createTrackbar(name, TRACK_WINDOW, val, max_val, nothing)

    # ---- User instructions ----
    print("Controls:")
    print("  ESC       - Quit")
    print("  A         - Previous image")
    print("  D         - Next image")
    print("  Use the sliders in the 'Controls' window to adjust HSV values")

    # ---- Main loop ----
    while True:
        # Load image
        path = os.path.join(IMAGE_FOLDER, files[index])
        img = cv2.imread(path)
        hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

        # Read trackbar positions
        h_low  = cv2.getTrackbarPos("H low", TRACK_WINDOW)
        h_high = cv2.getTrackbarPos("H high", TRACK_WINDOW)
        s_low  = cv2.getTrackbarPos("S low", TRACK_WINDOW)
        s_high = cv2.getTrackbarPos("S high", TRACK_WINDOW)
        v_low  = cv2.getTrackbarPos("V low", TRACK_WINDOW)
        v_high = cv2.getTrackbarPos("V high", TRACK_WINDOW)

        # Mask and overlay
        mask = cv2.inRange(hsv, np.array([h_low, s_low, v_low]), np.array([h_high, s_high, v_high]))
        result = cv2.bitwise_and(img, img, mask=mask)

        # Show image
        cv2.imshow(IMAGE_WINDOW, result)

        # Keyboard control
        key = cv2.waitKey(20) & 0xFF
        if key == 27:  # ESC
            break
        elif key == ord('d'):  # next image
            index = (index + 1) % len(files)
        elif key == ord('a'):  # previous image
            index = (index - 1) % len(files)

    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()

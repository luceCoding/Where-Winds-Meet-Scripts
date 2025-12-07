import logging
import mss
import cv2 as cv
import numpy as np
from pywinauto.application import Application
from wwm.image import get_gray_template_image


class Window:

    def __init__(self, window_title="Where Winds Meet"):

        try:
            app = Application().connect(title=window_title, found_index=0)
            self.window = app[window_title]
            logger = logging.getLogger(__name__)
            logger.info(f"Connected to '{window_title}' window.")
        except Exception:
            raise RuntimeError(f"Window '{window_title}' not found.")

    def get_window_dimensions(self):

        rect = self.window.rectangle()
        dimensions = {
            "top": rect.top,
            "left": rect.left,
            "width": rect.width(),
            "height": rect.height(),
        }
        return dimensions

    def get_center(self):

        rect = self.window.rectangle()

        center_x = rect.left + rect.width() // 2
        center_y = rect.top + rect.height() // 2

        return center_x, center_y

    def get_screenshot(self, dimensions=None, letterbox_size=0, pillarbox_size=0):
        """
        Take a screenshot and replace the sides with black pixels.

        letterbox_size: number of pixels to black out at top and bottom
        pillarbox_size: number of pixels to black out at left and right
        """
        self.window.set_focus()
        with mss.mss() as sct:
            if dimensions is None:
                dimensions = self.get_window_dimensions()
            raw_screenshot = np.array(sct.grab(dimensions))
            screenshot = cv.cvtColor(raw_screenshot, cv.COLOR_BGRA2BGR)

        h, w, c = screenshot.shape

        # Black out top and bottom (letterbox)
        if letterbox_size > 0:
            screenshot[:letterbox_size, :, :] = 0           # top
            screenshot[h - letterbox_size:, :, :] = 0      # bottom

        # Black out left and right (pillarbox)
        if pillarbox_size > 0:
            screenshot[:, :pillarbox_size, :] = 0         # left
            screenshot[:, w - pillarbox_size:, :] = 0     # right

        return screenshot

    def send_keystrokes(self, keystrokes):
        self.window.send_keystrokes(keystrokes)

    def minimize(self):
        self.window.minimize()

    def send_left_mouse_click(self, x, y):
        self.window.set_focus()
        self.window.click_input(coords=(x, y))

    def get_coords_template_match(self, template_name, threshold=0.75, nms_thresh=0.3):
        img_rgb = self.get_screenshot(pillarbox_size=400) # TODO: Make this dynamic, 400 is enough to cover the sides on a 1600x900
        assert img_rgb is not None, "Screenshot could not be captured."
        img_gray = cv.cvtColor(img_rgb, cv.COLOR_BGR2GRAY)

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

    def set_focus(self):
        self.window.set_focus()

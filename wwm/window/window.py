import mss
import cv2 as cv
import numpy as np
from pywinauto.application import Application
from wwm.images import get_gray_template_image


class Window:

    def __init__(self, window_title="Where Winds Meet"):

        try:
            app = Application().connect(title=window_title, found_index=0)
            self.window = app[window_title]
            print(f"Connected to '{window_title}' window.")
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

    def get_screenshot(self, dimensions=None):

        with mss.mss() as sct:
            if dimensions is None:
                dimensions = self.get_window_dimensions()
            raw_screenshot = np.array(sct.grab(dimensions))
            screenshot = cv.cvtColor(raw_screenshot, cv.COLOR_BGRA2BGR)
            return screenshot

    def send_keystrokes(self, keystrokes):
        self.window.send_keystrokes(keystrokes)

    def minimize(self):
        self.window.minimize()

    def send_left_mouse_click(self, x, y):
        self.window.set_focus()
        self.window.click_input(coords=(x, y))

    def get_coords_template_match(self, template_name, threshold=0.75):
        img_rgb = self.get_screenshot()
        assert img_rgb is not None, "Screenshot could not be captured."
        img_gray = cv.cvtColor(img_rgb, cv.COLOR_BGR2GRAY)

        template_gray = get_gray_template_image(template_name)
        w, h = template_gray.shape[::-1]
        res = cv.matchTemplate(img_gray, template_gray, cv.TM_CCOEFF_NORMED)

        loc = np.where(res >= threshold)
        coords = []
        for pt in zip(*loc[::-1]):  # Get center coords
            x = pt[0] + w // 2
            y = pt[1] + h // 2
            coords.append((x, y))

        return coords

    def set_focus(self):
        self.window.set_focus()
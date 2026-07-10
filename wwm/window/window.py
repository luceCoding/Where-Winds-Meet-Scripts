import logging
from pywinauto import mouse
from pywinauto.application import Application
import win32gui
import mss
import cv2 as cv
import numpy as np


class Window:

    def __init__(self, window_title="Where Winds Meet"):

        try:
            app = Application().connect(title=window_title, found_index=0)
            self.window = app[window_title]
            self.hwnd = self.window.handle
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
        """Return the center of the client window."""
        client_dims = self.get_client_dimensions()
        center_x = client_dims["left"] + client_dims["width"] // 2
        center_y = client_dims["top"] + client_dims["height"] // 2
        return center_x, center_y

    def get_client_dimensions(self):
        """Return the screen coordinates of the client area (no borders/title)."""
        client_rect = win32gui.GetClientRect(self.hwnd)
        client_width = client_rect[2] - client_rect[0]
        client_height = client_rect[3] - client_rect[1]

        # Convert top-left client coordinates to screen coordinates
        client_left_top = win32gui.ClientToScreen(self.hwnd, (0, 0))
        left, top = client_left_top

        return {"top": top, "left": left, "width": client_width, "height": client_height}

    def get_screenshot(self, letterbox_size=0, pillarbox_size=0):
        self.window.set_focus()
        dimensions = self.get_client_dimensions()
        with mss.mss() as sct:
            raw = np.array(sct.grab(dimensions))
            screenshot = cv.cvtColor(raw, cv.COLOR_BGRA2BGR)

        h, w, _ = screenshot.shape
        if letterbox_size > 0:
            screenshot[:letterbox_size, :, :] = 0
            screenshot[h - letterbox_size:, :, :] = 0
        if pillarbox_size > 0:
            screenshot[:, :pillarbox_size, :] = 0
            screenshot[:, w - pillarbox_size:, :] = 0

        return screenshot

    def get_gray_screenshot(self, dimensions=None, letterbox_size=0, pillarbox_size=0):
        img_rgb = self.get_screenshot(letterbox_size=letterbox_size,
                                      pillarbox_size=pillarbox_size,
                                      )
        assert img_rgb is not None, "Screenshot could not be captured."
        return cv.cvtColor(img_rgb, cv.COLOR_BGR2GRAY)

    def send_keystrokes(self, keystrokes):
        self.window.send_keystrokes(keystrokes)

    def minimize(self):
        self.window.minimize()

    def client_to_screen_coords(self, x, y):
        top_left = win32gui.ClientToScreen(self.window.handle, (0, 0))
        return top_left[0] + x, top_left[1] + y

    def send_left_mouse_click(self, x, y):
        self.window.set_focus()
        screen_x, screen_y = self.client_to_screen_coords(x, y)
        self.window.click_input(coords=(screen_x, screen_y), absolute=True)

    def send_mouse_scroll_wheel(self, x, y, wheel_dist=1):
        self.window.set_focus()
        mouse.scroll(coords=(x, y), wheel_dist=wheel_dist)

    def set_focus(self):
        self.window.set_focus()

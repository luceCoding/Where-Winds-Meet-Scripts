import sys
sys.path.append("..")

import os
import time
import argparse
from pynput import keyboard as pynput_keyboard
from pynput import mouse as pynput_mouse
import threading
from wwm.window import Window
import cv2 as cv

def main():
    # Directory to save screenshots
    SAVE_DIR = os.path.join(os.path.dirname(
        os.path.abspath(__file__)), "images")
    os.makedirs(SAVE_DIR, exist_ok=True)

    # Parse command-line arguments
    parser = argparse.ArgumentParser(
        description="Capture a window on a hotkey press.")
    parser.add_argument("--hotkey", type=str, default='l',
                        help="Key to trigger screenshot (keyboard key or mouse side button: x1, x2)")
    parser.add_argument("--app_title", type=str, default="Where Winds Meet",
                        help="Window title of the application (default: 'Where Winds Meet')")
    args = parser.parse_args()
    hotkey = args.hotkey.lower()
    APP_TITLE = args.app_title

    # Connect to the app window
    window = Window(window_title=APP_TITLE)

    # Capture function
    def capture():
        img = window.get_screenshot()
        filename = os.path.join(
            SAVE_DIR, f"screenshot_{int(time.time())}.png")
        cv.imwrite(filename, img)
        print(f"Saved {filename}")

    # Event for clean exit
    exit_event = threading.Event()

    # Mouse buttons mapping
    mouse_buttons = {'x1': pynput_mouse.Button.x1,
                     'x2': pynput_mouse.Button.x2}

    # Start listener depending on hotkey type
    if hotkey in mouse_buttons:
        print(f"Hotkey set to side mouse button: {hotkey.upper()}")

        def on_click(x, y, button, pressed):
            if pressed and button == mouse_buttons[hotkey]:
                capture()

        listener = pynput_mouse.Listener(on_click=on_click)
    else:
        print(f"Hotkey set to keyboard key: {hotkey}")

        def on_press(key):
            try:
                if hasattr(key, 'char') and key.char == hotkey:
                    capture()
            except AttributeError:
                # handle special keys like space
                if str(key).lower() == f"'{hotkey}'":
                    capture()

        listener = pynput_keyboard.Listener(on_press=on_press)

    # Start listener in a separate thread
    listener.start()
    print(
        f"Press '{hotkey}' to capture the window '{APP_TITLE}'. Press Ctrl+C to exit.")

    try:
        while not exit_event.is_set():
            time.sleep(1)
    except KeyboardInterrupt:
        print("Exiting...")
        listener.stop()
        exit_event.set()


if __name__ == "__main__":
    main()

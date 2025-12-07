import os
import yaml
import keyboard
import random
import time
import logging
from wwm.window import Window
from image import image
from collections import deque
from datetime import datetime, timedelta


def main():

    # ------------------------------
    # Load config
    # ------------------------------
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, "config.yaml")

    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    log_level_str = config.get("log_level", "INFO").upper()
    log_level = getattr(logging, log_level_str, logging.INFO)

    # Configure logger
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    logger = logging.getLogger(__name__)

    app_title = config["app_title"]
    material_match_threshold = config["material_match_threshold"]
    waypoint_match_threshold = config["waypoint_match_threshold"]
    top_n_closest = config["top_n_closest"]
    seconds_till_revisit = config["seconds_till_revisit"]
    seconds_for_loading_screen = config["seconds_for_loading_screen"]
    key_stop_script = config["key_stop_script"]
    key_wayfinder = config["key_wayfinder"]
    key_confirm = config["key_confirm"]
    key_map = config["key_map"]
    key_pickup_material = config["key_pickup_material"]
    sleep_timer = 2

    # ------------------------------
    # Connect to app
    # ------------------------------
    window = Window(window_title=app_title)

    # ------------------------------
    # Stop flag + hotkey
    # ------------------------------
    stop_flag = {"stop": False}

    def stop():
        stop_flag["stop"] = True
        logger.info("Stop key pressed — stopping program...")

    keyboard.add_hotkey(key_stop_script, stop)

    visited_queue = deque()

    def unstuck():
        waypoint_coords = []
        for png in image.list_png_files('waypoints'):
            found_coords, _ = window.get_coords_template_match(
                png,
                threshold=waypoint_match_threshold,
            )
            waypoint_coords += found_coords

        if len(waypoint_coords):  # we are stuck, map still open
            logger.info("Stuck detected, taking waypoint.")
            waypoint_coords = random.choice(waypoint_coords)
            x, y = waypoint_coords
            window.send_left_mouse_click(int(x), int(y))
            time.sleep(sleep_timer)
            window.send_keystrokes(key_confirm)
            # Wait for loading screen
            time.sleep(seconds_for_loading_screen)

    while not stop_flag["stop"]:

        # Close "Select a new destination?" dialog
        window.send_keystrokes("{ESC}")
        time.sleep(sleep_timer+1)

        # Open map
        window.send_keystrokes(key_map)
        time.sleep(sleep_timer)

        now = datetime.now()
        cutoff = now - timedelta(seconds=seconds_till_revisit)
        # Remove any past visited areas older then X seconds
        while visited_queue and visited_queue[0][0] < cutoff:
            visited_queue.popleft()
            logger.debug("Queue popped.")

        # Select destination
        coords = []
        for png in image.list_png_files('materials'):
            found_coords, last_img_gray = window.get_coords_template_match(
                png,
                threshold=material_match_threshold,
            )
            coords += found_coords

        center_x, center_y = window.get_center()
        # Sort all waypoint coords by distance to the center of the window
        coords_sorted = sorted(
            coords,
            key=lambda p: (p[0] - center_x) ** 2 + (p[1] - center_y) ** 2
        )

        crop_64 = None
        for idx, _ in enumerate(coords_sorted):
            coord = random.choice(coords_sorted[idx:idx+top_n_closest])
            x, y = coord
            crop_64 = image.get_crop_around(last_img_gray, x, y, size=64)
            has_similar = any(image.get_image_similarity(
                img[1], crop_64) >= 0.9 for img in visited_queue)
            if not has_similar:
                logger.debug("Image is not similar.")
                window.send_left_mouse_click(int(x), int(y))
                time.sleep(sleep_timer)
                break
            else:
                logger.debug("Image is similar.")

        window.send_keystrokes(key_wayfinder)  # Auto Path
        time.sleep(sleep_timer)

        # Check if stuck
        waypoint_coords = []
        for png in image.list_png_files('waypoints'):
            found_coords, _ = window.get_coords_template_match(
                png,
                threshold=waypoint_match_threshold,
            )
            waypoint_coords += found_coords

        if len(waypoint_coords):  # Stuck, map still open
            logger.info("Stuck detected, taking waypoint.")
            waypoint_coords = random.choice(waypoint_coords)
            x, y = waypoint_coords
            window.send_left_mouse_click(int(x), int(y))
            time.sleep(sleep_timer)
            window.send_keystrokes(key_confirm)
            time.sleep(seconds_for_loading_screen)  # Wait for loading screen

        else:  # Continue as normal
            has_black_letterbox, has_white_letterbox = True, False
            while has_black_letterbox is True or has_white_letterbox is True:
                time.sleep(sleep_timer)
                screenshot = window.get_screenshot()
                has_black_letterbox = image.has_bottom_black_letterbox(
                    screenshot)
                has_white_letterbox = image.has_bottom_white_letterbox(
                    screenshot)
                logger.debug("Black letterbox: %s | White letterbox: %s",
                             has_black_letterbox, has_white_letterbox)

        screenshot = window.get_screenshot()
        has_gray_letterbox = image.has_bottom_gray_letterbox(screenshot)
        if has_gray_letterbox:
            logger.debug("Gray letterbox detected.")
            window.send_keystrokes(key_confirm)
            time.sleep(sleep_timer)
            waypoint_coords = []
            for png in image.list_png_files('waypoints'):
                found_coords, _ = window.get_coords_template_match(
                    png,
                    threshold=waypoint_match_threshold,
                )
                waypoint_coords += found_coords

            if len(waypoint_coords):  # we are stuck, map still open
                logger.info("Stuck detected, taking waypoint.")
                waypoint_coords = random.choice(waypoint_coords)
                x, y = waypoint_coords
                window.send_left_mouse_click(int(x), int(y))
                time.sleep(sleep_timer)
                window.send_keystrokes(key_confirm)
                # Wait for loading screen
                time.sleep(seconds_for_loading_screen)

        time.sleep(0.5)
        window.send_keystrokes(key_pickup_material)
        time.sleep(0.5)
        window.send_keystrokes(key_pickup_material)
        time.sleep(0.5)
        window.send_keystrokes(key_pickup_material)
        if crop_64 is not None:
            visited_queue.append((datetime.now(), crop_64))


if __name__ == "__main__":
    main()

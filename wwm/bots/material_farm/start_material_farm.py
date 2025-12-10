import os
import keyboard
import random
import time
import logging
from wwm.image import image
from collections import deque
from datetime import timedelta, datetime
from wwm import wwm_config
from wwm.window import Window
import sys
from wwm import authentication as auth


def get_app_dir():
    # Running as PyInstaller bundle?
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)  # Folder with the .exe
    # Running from source
    return os.path.dirname(os.path.abspath(__file__))


def main():

    # ------------------------------
    # Load config
    # ------------------------------
    app_dir = get_app_dir()
    config_path = os.path.join(app_dir, "config.yaml")

    config = wwm_config.load_config(path=config_path)

    # ------------------------------
    # Configure logger
    # ------------------------------
    IS_EXE = getattr(sys, "frozen", False)
    logging.basicConfig(
        level=logging.INFO if IS_EXE else logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    logger = logging.getLogger(__name__)

    # ------------------------------
    # Connect to app
    # ------------------------------
    window = Window(window_title=config.app_title)

    # ------------------------------
    # Stop flag + hotkey
    # ------------------------------
    stop_flag = {"stop": False}

    def stop():
        stop_flag["stop"] = True
        logger.info("Stop key pressed — stopping program...")

    keyboard.add_hotkey(config.key_stop_script, stop)

    # ------------------------------
    # Reset for pre-session state
    # ------------------------------
    for _ in range(4):
        window.send_keystrokes(config.key_escape)

    # ------------------------------
    # License Check
    # ------------------------------
    if not auth.is_license_good(window, config):
        return

    visited_queue = deque()
    unreachable_materials = deque(maxlen=100)

    while not stop_flag["stop"]:

        # Close "Select a new destination?" dialog
        window.send_keystrokes(config.key_escape)
        time.sleep(config.seconds_between_actions+1)

        # Open map
        window.send_keystrokes(config.key_map)
        time.sleep(config.seconds_between_actions)

        now = datetime.now()
        cutoff = now - timedelta(seconds=config.seconds_till_revisit)
        # Remove any past visited areas older then X seconds
        while visited_queue and visited_queue[0][0] < cutoff:
            visited_queue.popleft()
            logger.debug("Queue popped.")

        # Select destination
        coords = []
        screenshot = window.get_gray_screenshot()
        screenshot = image.apply_map_mask(screenshot)
        for png in image.list_png_files('materials'):
            found_coords, last_img_gray = image.get_coords_template_match(
                screenshot,
                png,
                threshold=config.material_match_threshold,
            )
            coords += found_coords

        if last_img_gray is not None:
            center_x = last_img_gray.shape[1] // 2
            center_y = last_img_gray.shape[0] // 2
            # Sort all waypoint coords by distance to the center of the window
            coords_sorted = sorted(
                coords,
                key=lambda p: (p[0] - center_x) ** 2 + (p[1] - center_y) ** 2
            )

        crop_64 = None
        path_found = False
        for idx, _ in enumerate(coords_sorted):
            coord = random.choice(coords_sorted[idx:idx+config.top_n_closest])
            x, y = coord
            crop_64 = image.get_crop_around(last_img_gray, x, y, size=64)
            has_similar = any(image.get_image_similarity(
                img[1], crop_64) >= config.visited_match_threshold for img in visited_queue)
            if not has_similar:
                is_unreachable = any(image.get_image_similarity(
                    img, crop_64) >= config.visited_match_threshold for img in unreachable_materials)
                if is_unreachable:
                    logger.debug("Image is unreachable.")
                    continue
                logger.debug("Image is not similar.")
                window.send_left_mouse_click(int(x), int(y))
                time.sleep(config.seconds_between_actions)
                # Auto Path to destination
                window.send_keystrokes(config.key_wayfinder)
                logger.info("Path started...")
                time.sleep(config.seconds_between_actions)
                path_found = True
                break
            else:
                logger.debug("Image is similar.")
        if path_found is False:
            logger.info("No path found.")  # TODO: Expand search area

        # Check if stuck
        waypoint_coords = []
        screenshot = window.get_gray_screenshot()
        screenshot = image.apply_map_mask(screenshot)
        for png in image.list_png_files('waypoints'):
            found_coords, _ = image.get_coords_template_match(
                screenshot,
                png,
                threshold=config.waypoint_match_threshold,
            )
            waypoint_coords += found_coords

        if len(waypoint_coords):  # Stuck, map still open
            logger.info("Stuck detected, taking waypoint.")
            waypoint_coords = random.choice(waypoint_coords)
            x, y = waypoint_coords
            window.send_left_mouse_click(int(x), int(y))
            time.sleep(config.seconds_between_actions)
            window.send_keystrokes(config.key_confirm)
            # Wait for loading screen
            time.sleep(config.seconds_for_loading_screen)

        else:  # Continue as normal
            time_till_expired = datetime.now() + timedelta(seconds=config.seconds_for_each_material)

            has_black_letterbox = True
            has_white_letterbox = False

            while has_black_letterbox or has_white_letterbox:

                if datetime.now() >= time_till_expired:
                    logger.info("Timed out, attempting reset.")
                    window.send_keystrokes(config.key_escape)
                    break

                time.sleep(config.seconds_between_actions)

                screenshot = window.get_screenshot()

                has_black_letterbox = image.has_bottom_black_letterbox(
                    screenshot)

                if not has_black_letterbox:
                    has_white_letterbox = image.has_bottom_white_letterbox(
                        screenshot)
                else:
                    has_white_letterbox = False

                logger.debug(
                    "Black letterbox: %s | White letterbox: %s",
                    has_black_letterbox,
                    has_white_letterbox,
                )

        screenshot = window.get_screenshot()
        has_gray_letterbox = image.has_center_gray_band(screenshot)
        if has_gray_letterbox:
            logger.debug("Gray letterbox detected.")
            if crop_64 is not None:
                unreachable_materials.append(crop_64)
                logger.info("Destination unreachable.")
            window.send_keystrokes(config.key_escape)
            time.sleep(config.seconds_between_actions)
            window.send_keystrokes(config.key_spirited_courser_pickup)
            window.send_keystrokes(config.key_map)
            time.sleep(config.seconds_between_actions)

            waypoint_coords = []
            screenshot = window.get_gray_screenshot()
            screenshot = image.apply_map_mask(screenshot)
            for png in image.list_png_files('waypoints'):
                found_coords, _ = image.get_coords_template_match(
                    screenshot,
                    png,
                    threshold=config.waypoint_match_threshold,
                )
                waypoint_coords += found_coords

            if len(waypoint_coords):  # we are stuck, map still open
                logger.info("Stuck detected, taking waypoint.")
                waypoint_coords = random.choice(waypoint_coords)
                x, y = waypoint_coords
                window.send_left_mouse_click(int(x), int(y))
                time.sleep(config.seconds_between_actions)
                window.send_keystrokes(config.key_confirm)
                # Wait for loading screen
                time.sleep(config.seconds_for_loading_screen)

        time.sleep(0.5)
        window.send_keystrokes(config.key_spirited_courser_pickup)
        window.send_keystrokes(config.key_character_pickup)
        time.sleep(0.5)
        window.send_keystrokes(config.key_character_pickup)
        time.sleep(0.5)
        window.send_keystrokes(config.key_character_pickup)
        window.send_keystrokes(config.key_spirited_courser_pickup)
        if crop_64 is not None:
            visited_queue.append((datetime.now(), crop_64))
            logger.info("Destination reached.")


if __name__ == "__main__":
    main()

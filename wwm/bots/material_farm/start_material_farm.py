import os
import keyboard
import random
import time
import logging
import win32clipboard
from wwm.image import image
from collections import deque
from datetime import timedelta, datetime, timezone
from wwm import wwm_config
from wwm.cryptography import verify_id
from wwm.window import Window
from wwm.constants import PUBLIC_KEY, SIGNATURE, EXPIRATION_DATE_UTC
import requests
import sys
import re


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
    # Check character id
    # ------------------------------
    def get_character_id():
        time.sleep(1)
        window.send_keystrokes(config.key_escape)
        time.sleep(config.seconds_between_actions)
        waypoint_coords = []
        screenshot = window.get_gray_screenshot()
        for png in image.list_png_files('char'):
            found_coords, _ = image.get_coords_template_match(
                screenshot,
                png,
                threshold=0.9,
            )
            waypoint_coords += found_coords
        if len(waypoint_coords) == 1:
            x, y = waypoint_coords[0]
            window.send_left_mouse_click(int(x), int(y))
            win32clipboard.OpenClipboard()
            character_id = win32clipboard.GetClipboardData()
            win32clipboard.CloseClipboard()
            logger.info(f"Character ID: {character_id}")
            return character_id
        return -1

    # ------------------------------
    # Lifetime check
    # ------------------------------

    def parse_timeapi_datetime(dt_str: str) -> datetime:
        """
        Parse timeapi.io 'dateTime' string to a datetime object.
        Truncate microseconds to 6 digits for Python compatibility.
        """
        # Truncate fractional seconds to max 6 digits
        dt_str = re.sub(r"(\.\d{6})\d+", r"\1", dt_str)
        dt = datetime.fromisoformat(dt_str)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt

    def get_current_unix_time():
        """
        Get current UTC Unix timestamp using multiple fallback APIs.
        Returns:
            int: current UTC Unix timestamp
        Raises:
            RuntimeError: if all APIs fail
        """
        apis = [
            "https://worldtimeapi.org/api/timezone/Etc/UTC",
            "https://timeapi.io/api/Time/current/zone?timeZone=UTC",
        ]

        for api in apis:
            try:
                resp = requests.get(api, timeout=5)
                resp.raise_for_status()
                data = resp.json()

                # worldtimeapi.org
                if "unixtime" in data:
                    return int(data["unixtime"])

                # timeapi.io
                if "dateTime" in data:
                    dt = parse_timeapi_datetime(data["dateTime"])
                    return int(dt.timestamp())

            except Exception as e:
                # logger.debug(f"{e}")
                continue

        return None

    def has_expired_utc(target_dt: datetime):
        """
        Returns True if the given UTC datetime has expired.
        """
        # Ensure the datetime is timezone-aware
        if target_dt.tzinfo is None:
            target_dt = target_dt.replace(tzinfo=timezone.utc)

        target_ts = int(target_dt.timestamp())
        current_ts = get_current_unix_time()

        # Treat as expired if current time is unavailable
        if current_ts is None:
            return True

        return current_ts > target_ts

    # ------------------------------
    # License Check
    # ------------------------------

    def character_id_match():

        before_seq_number = win32clipboard.GetClipboardSequenceNumber()
        character_id = get_character_id()
        if character_id == -1:
            character_id = get_character_id()
        after_seq_number = win32clipboard.GetClipboardSequenceNumber()
        is_character_id_match = verify_id(character_id,
                                          public_key_pem=PUBLIC_KEY,
                                          signature=SIGNATURE)
        is_clipboard_untampered = (before_seq_number+5 == after_seq_number)
        return is_clipboard_untampered and is_character_id_match

    if has_expired_utc(EXPIRATION_DATE_UTC) is True:
        logger.info("License has expired.")
        return
    if character_id_match() is False:
        logger.info("License rejected.")
        return
    logger.info("License accepted.")

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

import os
import yaml
import keyboard
import random
import time
from wwm.window import Window
from wwm.images import images
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

    app_title = config["app_title"]
    material_match_threshold = config["material_match_threshold"]
    waypoint_match_threshold = config["waypoint_match_threshold"]
    key_stop_script = config["key_stop_script"]
    key_wayfinder = config["key_wayfinder"]
    key_confirm = config["key_confirm"]
    key_map = config["key_map"]
    key_pickup_material = config["key_pickup_material"]

    sleep_timer = 2
    loading_timer = 10

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
        print("Stop key pressed — stopping program...")

    keyboard.add_hotkey(key_stop_script, stop)

    visited_queue = deque()

    while not stop_flag["stop"]:

        # Close "Select a new destination?" dialog
        window.send_keystrokes("{ESC}")
        time.sleep(sleep_timer+1)

        # Open map
        window.send_keystrokes(key_map)
        time.sleep(sleep_timer)

        # remove items older than 5 minutes
        now = datetime.now()
        cutoff = now - timedelta(minutes=5)

        while visited_queue and visited_queue[0][0] < cutoff:
            visited_queue.popleft()
            print("pop")

        # Select destination
        coords = []
        for png in [#"template_buddhas_tear.png",
                    #"template_refined_iron_ore.png",
                    "template_jade_tower_peony.png",
                    ]:
            found_coords, last_img_gray = window.get_coords_template_match(
                png,
                threshold=material_match_threshold,
            )
            coords += found_coords

        crop_64 = None
        for _ in coords:
            coord = random.choice(coords)
            x, y = coord
            crop_64 = images.get_crop_around(last_img_gray, x, y, size=64)
            has_similar = any(images.get_image_similarity(
                img[1], crop_64) >= 0.9 for img in visited_queue)
            if not has_similar:
                print("Not similar")
                window.send_left_mouse_click(int(x), int(y))
                time.sleep(sleep_timer)
                break
            else:
                print("Similar!")

        window.send_keystrokes(key_wayfinder)  # Auto Path
        time.sleep(sleep_timer)

        # Check if stuck
        waypoint_coords = []
        for png in ["template_waypoint.png",
                    ]:
            found_coords, _ = window.get_coords_template_match(
                png,
                threshold=waypoint_match_threshold,
            )
            waypoint_coords += found_coords
        if len(waypoint_coords):  # we are stuck, map still open
            print("Stuck detected, taking waypoint.")
            waypoint_coords = random.choice(waypoint_coords)
            x, y = waypoint_coords
            window.send_left_mouse_click(int(x), int(y))
            time.sleep(sleep_timer)
            window.send_keystrokes(key_confirm)
            time.sleep(loading_timer)  # Wait for loading screen

        else:  # continue as normal
            has_black_letterbox, has_white_letterbox = True, False
            while has_black_letterbox is True or has_white_letterbox is True:
                time.sleep(sleep_timer)
                screenshot = window.get_screenshot()
                has_black_letterbox = images.has_bottom_black_letterbox(
                    screenshot)
                has_white_letterbox = images.has_bottom_white_letterbox(
                    screenshot)
                print(has_black_letterbox, has_white_letterbox)

        screenshot = window.get_screenshot()
        has_gray_letterbox = images.has_bottom_gray_letterbox(screenshot)
        if has_gray_letterbox:
            print("gray letterbox")
            window.send_keystrokes(key_confirm)
            time.sleep(sleep_timer)
            waypoint_coords = []
            for png in ["template_waypoint.png",
                        ]:
                found_coords, _ = window.get_coords_template_match(
                    png,
                    threshold=waypoint_match_threshold,
                )
                waypoint_coords += found_coords
            if len(waypoint_coords):  # we are stuck, map still open
                print("Stuck detected, taking waypoint.")
                waypoint_coords = random.choice(waypoint_coords)
                x, y = waypoint_coords
                window.send_left_mouse_click(int(x), int(y))
                time.sleep(sleep_timer)
                window.send_keystrokes(key_confirm)
                time.sleep(loading_timer)  # Wait for loading screen

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

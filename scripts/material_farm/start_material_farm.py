import os
import yaml
import keyboard
import random
import time
from wwm.window import Window
from wwm.images.images import has_bottom_letterbox


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

    while not stop_flag["stop"]:

        window.set_focus()
        # close "Select a new destination?"
        window.send_keystrokes(key_confirm)
        time.sleep(3)
        # open map
        window.send_keystrokes(key_map)
        time.sleep(2)

        coords = window.get_coords_template_match(
            "template_jade_tower_peony.png",
            threshold=material_match_threshold,
        )
        if len(coords):
            coord = random.choice(coords)
            x, y = coord
            window.send_left_mouse_click(int(x), int(y))

        time.sleep(2)
        window.send_keystrokes(key_wayfinder)  # Auto Path

        time.sleep(2)
        # Check if stuck
        coords = window.get_coords_template_match(
            "template_jade_tower_peony.png",
            threshold=material_match_threshold,
        )
        if len(coords):  # we are stuck, map still open
            print("Stuck detected.")
            waypoint_coords = window.get_coords_template_match(
                "template_waypoint.png",
                threshold=waypoint_match_threshold,
            )
            if len(waypoint_coords):  # unstuck ourselves
                print("Unstucking ourselves. Taking waypoint.")
                waypoint_coords = random.choice(waypoint_coords)
                x, y = waypoint_coords
                window.send_left_mouse_click(int(x), int(y))
                time.sleep(2)
                window.send_keystrokes(key_confirm)
                time.sleep(10) # Wait for loading screen

        else:  # continue as normal
            print("Continue.")
            has_letterbox = True
            while has_letterbox:
                time.sleep(2)
                screenshot = window.get_screenshot()
                has_letterbox = has_bottom_letterbox(screenshot)
                print(has_letterbox)

    time.sleep(2)
    window.send_keystrokes(key_pickup_material)
    window.send_keystrokes(key_pickup_material)
    window.send_keystrokes(key_pickup_material)


if __name__ == "__main__":
    main()

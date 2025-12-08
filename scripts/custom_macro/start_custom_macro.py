from pywinauto.application import Application
import random
import keyboard
import yaml
import time
import os
import sys


def run_step(game, actions, min_delay, max_delay, stop_flag):
    """Send keystrokes safely."""
    if stop_flag["stop"]:
        return False

    random_delay = random.uniform(1.0, 5.0)

    for a in actions:
        game.send_keystrokes(a)
        if stop_flag["stop"]:
            return False

    if random_delay:
        time.sleep(random_delay)
        if stop_flag["stop"]:
            return False

    return True


def main():

    # ------------------------------
    # Load config
    # ------------------------------
    script_dir = os.path.dirname(os.path.abspath(__file__))
    config_path = os.path.join(script_dir, "config.yaml")

    with open(config_path, "r") as f:
        config = yaml.safe_load(f)

    app_title = config["app_title"]
    minimize_window_at_startup = config["minimize_window_at_startup"]
    key_stop_script = config["key_stop_script"]
    steps = config["steps"]

    # ------------------------------
    # Connect to app
    # ------------------------------
    try:
        app = Application().connect(title=app_title, found_index=0)
        game = app[app_title]
        print("Game application found. Starting script.")
    except Exception as e:
        print(f"Error: Game application not found: {e}")
        sys.exit(1)

    # ------------------------------
    # Stop flag + hotkey
    # ------------------------------
    stop_flag = {"stop": False}

    def stop():
        stop_flag["stop"] = True
        print("Stop key pressed — stopping program...")

    keyboard.add_hotkey(key_stop_script, stop)

    # ------------------------------
    # Minimize the window
    # ------------------------------
    if minimize_window_at_startup:
        game.minimize()

    # ------------------------------
    # Main loop
    # ------------------------------
    n_rotations = 0

    while not stop_flag["stop"]:
        for actions, min_delay, max_delay in steps:
            if not run_step(game, actions, min_delay, max_delay, stop_flag):
                return

        n_rotations += 1
        #print(f"Run {n_rotations} completed.")


if __name__ == "__main__":
    main()

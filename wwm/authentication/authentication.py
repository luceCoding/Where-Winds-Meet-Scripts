import requests
import re
import win32clipboard
import logging
import time
from wwm.image import image
from datetime import datetime, timezone
from wwm.window import Window
from wwm import wwm_config
from wwm.cryptography import verify_id
from wwm.constants import PUBLIC_KEY, SIGNATURE, EXPIRATION_DATE_UTC
import random


logger = logging.getLogger(__name__)


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
            resp = requests.get(api, timeout=60)
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
            logger.debug(f"{e}")
            continue
    logger.debug(f"Could not contact server.")
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

def has_clipboard_been_tampered():
    # Generate known random text
    rdm_10_digit_num = str(random.randint(10**9, 10**10 - 1))

    # 1. Read sequence before touching clipboard
    before_seq = win32clipboard.GetClipboardSequenceNumber()

    # 2. Write our known value
    win32clipboard.OpenClipboard()
    win32clipboard.EmptyClipboard()
    win32clipboard.SetClipboardText(rdm_10_digit_num)
    win32clipboard.CloseClipboard()

    # EmptyClipboard (+1), SetClipboardText (+1)
    expected_after_seq = before_seq + 2

    time.sleep(0.05)  # small delay

    # 3. Read clipboard and read new sequence
    win32clipboard.OpenClipboard()
    try:
        after_text = win32clipboard.GetClipboardData(win32clipboard.CF_UNICODETEXT)
    finally:
        win32clipboard.CloseClipboard()

    after_seq = win32clipboard.GetClipboardSequenceNumber()

    # 4. Validation
    content_ok = after_text == rdm_10_digit_num
    sequence_ok = after_seq == expected_after_seq

    return not(content_ok and sequence_ok)

def get_character_id(window: Window, config: wwm_config):

    for _ in range(4):
        window.send_keystrokes(config.key_escape)
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
        logger.debug(f"Character ID: {character_id}")
        return character_id
    return -1


def is_character_id_match(window: Window, config: wwm_config):

    before_seq_number = win32clipboard.GetClipboardSequenceNumber()
    character_id = get_character_id(window, config)
    if character_id == -1:
        character_id = get_character_id(window, config)
    after_seq_number = win32clipboard.GetClipboardSequenceNumber()
    is_character_id_match = verify_id(character_id,
                                      public_key_pem=PUBLIC_KEY,
                                      signature=SIGNATURE)
    is_clipboard_untampered = (before_seq_number+5 == after_seq_number)
    return is_clipboard_untampered and is_character_id_match


def is_license_good(window: Window, config: wwm_config):

    if has_expired_utc(EXPIRATION_DATE_UTC) is True:
        logger.debug("License has expired.")
        return False
    if is_character_id_match(window, config) is False:
        logger.debug("License rejected.")
        return False
    logger.debug("License accepted.")
    return True

import win32clipboard
import time


def safe_open_clipboard(retries=20, delay=0.01):
    for _ in range(retries):
        try:
            win32clipboard.OpenClipboard()
            return
        except:
            time.sleep(delay)
    raise RuntimeError("Could not open clipboard after retries")


while True:
    try:
        safe_open_clipboard()
        win32clipboard.EmptyClipboard()
        win32clipboard.SetClipboardText("ATTACK!!!")
        win32clipboard.CloseClipboard()
    except:
        pass  # ignore any failure
    time.sleep(0.01)
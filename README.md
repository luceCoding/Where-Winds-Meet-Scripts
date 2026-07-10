# Where Winds Meet Scripts
Lightweight collection of simple to advanced Python scripts for the game Where Winds Meet.

Depending on the script, it will allow you to minimize the game window and have this running in the background.
Scripts that utilize computer vision will not be able to be minimized while activate.
It is recommended to lower your graphics/resolution/fps settings for long sessions. 

## WARNING
These macros simulate keyboard presses and screenshots and do NOT inject or manipulate anything in memory. Therefore, it will be very difficult to detect. Either way, it may break terms of service so USE AT YOUR OWN RISK.

## Requirements
- Where Winds Meet game
- Windows 10+
- Python 3.10+

## Setup (Do this first)
1. Clone repo into a folder.
2. Open command prompt as admin.
3. Use the command to move to the project root folder, where the files requirements.txt and pyproject.toml are. Replace the path with where your project folder is.
    ```
    cd "root\folder\path\here"
    ```
    Once you are in the project root folder, run the follow commands:
    ```
    pip install -r requirements.txt
    pip install -e .
    ```
4. Select a script folder and continue to follow their README.
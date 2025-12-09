import os
from datetime import datetime, timezone, timedelta
import argparse

# -----------------------------
# Parse command-line arguments
# -----------------------------
parser = argparse.ArgumentParser(
    description="Generate constants.py with expiration date.")
parser.add_argument(
    "--days", type=int,
    help="Number of days from now until expiration."
)
args = parser.parse_args()
days_until_expiry = args.days

# -----------------------------
# Paths
# -----------------------------
# Absolute path to the directory containing this script
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))

# Path to src/ (where constants.py will be written)
SRC_DIR = os.path.abspath(os.path.join(SCRIPT_DIR, "../wwm"))

# Paths to build artifacts
PUBLIC_KEY_PATH = os.path.abspath(
    os.path.join(SCRIPT_DIR, "../build/public_key.pem"))
SIGNATURE_PATH = os.path.abspath(
    os.path.join(SCRIPT_DIR, "../build/signature.bin"))

# -----------------------------
# Generate expiration datetime
# -----------------------------
expiry_date = datetime.now(timezone.utc) + timedelta(days=days_until_expiry)

# -----------------------------
# Read build artifacts
# -----------------------------
with open(PUBLIC_KEY_PATH, "r") as f:
    public_key = f.read().strip()

with open(SIGNATURE_PATH, "rb") as f:
    signature_bytes = f.read()

# -----------------------------
# Write constants.py
# -----------------------------
constants_path = os.path.join(SRC_DIR, "constants.py")
with open(constants_path, "w") as f:
    f.write('from datetime import datetime, timezone\n\n')
    f.write(f'PUBLIC_KEY = """{public_key}"""\n\n')
    f.write(f'SIGNATURE = bytes.fromhex("{signature_bytes.hex()}")\n\n')
    f.write(
        f'EXPIRATION_DATE_UTC = datetime({expiry_date.year}, {expiry_date.month}, '
        f'{expiry_date.day}, {expiry_date.hour}, {expiry_date.minute}, '
        f'{expiry_date.second}, tzinfo=timezone.utc)\n'
    )

print(
    f"constants.py successfully written to {constants_path} with expiration in {days_until_expiry} day(s).")

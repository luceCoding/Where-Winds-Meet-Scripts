import os
import argparse
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

# Build folder
BUILD_DIR = os.path.join(os.path.dirname(__file__), "../build")
os.makedirs(BUILD_DIR, exist_ok=True)

# Parse ID from command line
parser = argparse.ArgumentParser(description="Sign a game ID.")
parser.add_argument("--id", required=True, help="Game ID to sign")
args = parser.parse_args()

ID = args.id.encode()

# Load private key
private_key_path = os.path.join(BUILD_DIR, "private_key.pem")
with open(private_key_path, "rb") as f:
    private_key = serialization.load_pem_private_key(f.read(), password=None)

# Sign the ID
signature = private_key.sign(
    ID,
    padding.PKCS1v15(),
    hashes.SHA256()
)

# Save signature
signature_path = os.path.join(BUILD_DIR, "signature.bin")
with open(signature_path, "wb") as f:
    f.write(signature)

print(f"Signature file created: {signature_path}")

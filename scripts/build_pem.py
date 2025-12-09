import os
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

# Build directory
BUILD_DIR = os.path.join(os.path.dirname(__file__), "../build")
os.makedirs(BUILD_DIR, exist_ok=True)

# 1. Generate RSA private key
private_key = rsa.generate_private_key(
    public_exponent=65537,
    key_size=2048,
)

# 2. Save private key
private_path = os.path.join(BUILD_DIR, "private_key.pem")
with open(private_path, "wb") as f:
    f.write(
        private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )

# 3. Save public key
public_key = private_key.public_key()
public_path = os.path.join(BUILD_DIR, "public_key.pem")
with open(public_path, "wb") as f:
    f.write(
        public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
    )

print(f"Created keys in {BUILD_DIR}")

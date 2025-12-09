from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding


def verify_id(id_from_game: str, public_key_pem: str, signature: bytes) -> bool:
    public_key = serialization.load_pem_public_key(
        public_key_pem.encode("utf-8"))

    try:
        public_key.verify(
            signature,
            id_from_game.encode("utf-8"),
            padding.PKCS1v15(),
            hashes.SHA256()
        )
        return True
    except Exception:
        return False

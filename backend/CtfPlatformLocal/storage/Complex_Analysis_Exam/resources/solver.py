import json
import hashlib
from pathlib import Path

from ecdsa import SECP256k1
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


BASE = Path(".")
ECDSA_JSON = BASE / "ecdsa_data.json"
ENC_EXAM = BASE / "exam.pdf.enc"
OUT_EXAM = BASE / "recovered_exam.pdf"

N = SECP256k1.order


def modinv(a: int, n: int) -> int:
    return pow(a, -1, n)


def derive_exam_password_from_private_key(d: int) -> str:
    raw = d.to_bytes(32, "big")
    return hashlib.sha256(raw).hexdigest()[:16]


def derive_aes_key(password: str, salt: bytes) -> bytes:
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=200_000,
    )
    return kdf.derive(password.encode("utf-8"))


def recover_private_key(z1: int, z2: int, r: int, s1: int, s2: int) -> tuple[int, int]:
    k = 
    d = 
    return k, d


def decrypt_exam(password: str) -> None:
    blob = json.loads(ENC_EXAM.read_text(encoding="utf-8"))
    salt = bytes.fromhex(blob["salt_hex"])
    nonce = bytes.fromhex(blob["nonce_hex"])
    ciphertext = bytes.fromhex(blob["ciphertext_hex"])

    key = derive_aes_key(password, salt)
    aesgcm = AESGCM(key)
    plaintext = aesgcm.decrypt(nonce, ciphertext, None)
    OUT_EXAM.write_bytes(plaintext)


def main() -> None:
    data = json.loads(ECDSA_JSON.read_text(encoding="utf-8"))

    z1 = int(data["z1_hex"], 16)
    z2 = int(data["z2_hex"], 16)
    r = int(data["r_hex"], 16)
    s1 = int(data["s1_hex"], 16)
    s2 = int(data["s2_hex"], 16)

    k, d = recover_private_key(z1, z2, r, s1, s2)
    password = derive_exam_password_from_private_key(d)
    decrypt_exam(password)


if __name__ == "__main__":
    main()
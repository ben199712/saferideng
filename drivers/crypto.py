import base64
import hashlib

from Crypto.Cipher import AES
from django.conf import settings


ENCRYPTION_PREFIX = "enc1:"


def get_driver_pii_encryption_key():
    source = getattr(settings, "DRIVER_PII_ENCRYPTION_KEY", settings.SECRET_KEY)
    if isinstance(source, str):
        source = source.encode("utf-8")
    return hashlib.sha256(source).digest()


def encrypt_value(value):
    if value in (None, ""):
        return value
    if isinstance(value, str) and value.startswith(ENCRYPTION_PREFIX):
        return value

    cipher = AES.new(get_driver_pii_encryption_key(), AES.MODE_SIV)
    ciphertext, tag = cipher.encrypt_and_digest(str(value).encode("utf-8"))
    payload = base64.urlsafe_b64encode(tag + ciphertext).decode("ascii")
    return f"{ENCRYPTION_PREFIX}{payload}"


def decrypt_value(value):
    if value in (None, ""):
        return value
    if not isinstance(value, str) or not value.startswith(ENCRYPTION_PREFIX):
        return value

    decoded = base64.urlsafe_b64decode(value[len(ENCRYPTION_PREFIX):].encode("ascii"))
    tag, ciphertext = decoded[:16], decoded[16:]
    cipher = AES.new(get_driver_pii_encryption_key(), AES.MODE_SIV)
    return cipher.decrypt_and_verify(ciphertext, tag).decode("utf-8")

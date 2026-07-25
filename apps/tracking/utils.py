from Crypto.PublicKey import RSA
from Crypto.Cipher import AES, PKCS1_OAEP
from Crypto.Random import get_random_bytes
import base64


def generate_rsa_key_pair():
    key = RSA.generate(2048)
    private_key = key.export_key()
    public_key = key.publickey().export_key()
    return private_key.decode('utf-8'), public_key.decode('utf-8')


def encrypt_data(data: str, public_key_pem: str) -> str:
    aes_key = get_random_bytes(32)
    recipient_key = RSA.import_key(public_key_pem)
    cipher_rsa = PKCS1_OAEP.new(recipient_key)
    encrypted_aes_key = cipher_rsa.encrypt(aes_key)
    cipher_aes = AES.new(aes_key, AES.MODE_EAX)
    ciphertext, tag = cipher_aes.encrypt_and_digest(data.encode('utf-8'))
    return base64.b64encode(encrypted_aes_key + cipher_aes.nonce + tag + ciphertext).decode('utf-8')


def decrypt_data(encrypted_data: str, private_key_pem: str) -> str:
    encrypted_bytes = base64.b64decode(encrypted_data)
    private_key = RSA.import_key(private_key_pem)
    encrypted_aes_key = encrypted_bytes[:private_key.size_in_bytes()]
    nonce = encrypted_bytes[private_key.size_in_bytes():private_key.size_in_bytes()+16]
    tag = encrypted_bytes[private_key.size_in_bytes()+16:private_key.size_in_bytes()+32]
    ciphertext = encrypted_bytes[private_key.size_in_bytes()+32:]
    cipher_rsa = PKCS1_OAEP.new(private_key)
    aes_key = cipher_rsa.decrypt(encrypted_aes_key)
    cipher_aes = AES.new(aes_key, AES.MODE_EAX, nonce=nonce)
    return cipher_aes.decrypt_and_verify(ciphertext, tag).decode('utf-8')

from Cryptodome.Hash import MD5
import json
import base64
from Cryptodome.PublicKey import RSA
from Cryptodome.Cipher import PKCS1_v1_5


def md5_encrypt(text):
    md5 = MD5.new()
    md5.update(text.encode('utf-8'))
    encrypted_text = md5.hexdigest()
    return encrypted_text


def encrypt_data_with_public_key(pubkey_str: str, data: dict) -> str:
    rsa_key = RSA.import_key(pubkey_str)
    cipher = PKCS1_v1_5.new(rsa_key)
    encrypted_password = cipher.encrypt(json.dumps(data).encode('utf-8'))
    return base64.b64encode(encrypted_password).decode('utf-8')


if __name__ == "__main__":
    print(md5_encrypt("xs123456"))

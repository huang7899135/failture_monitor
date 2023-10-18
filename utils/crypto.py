from Cryptodome.Hash import SHA256, MD5


def md5_encrypt(text):
    md5 = MD5.new()
    md5.update(text.encode('utf-8'))
    encrypted_text = md5.hexdigest()
    return encrypted_text


if __name__ == "__main__":
    print(md5_encrypt("xs123456"))

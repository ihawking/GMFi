import hashlib
import hmac
import secrets
import string
from base64 import b64encode, b64decode, urlsafe_b64encode

from cryptography.fernet import Fernet
from django.conf import settings


def get_message_str(message_dict: dict[str, str | int]) -> str:
    """将字典类型的数据，按照 key 升序，中间用 & 拼接生成字符串"""
    message_str = "&".join([f"{k}={v}" for k, v in sorted(message_dict.items()) if v is not None and str(v)])
    return message_str


def create_hmac_sign(message_dict: dict, key: str) -> str:
    message_str = get_message_str(message_dict)
    return hmac.new(key.encode(), message_str.encode(), hashlib.sha256).hexdigest()


def validate_hmac(message_dict: dict, key: str, received_hmac: str) -> bool:
    calculated_hmac = create_hmac_sign(message_dict, key)
    return hmac.compare_digest(received_hmac, calculated_hmac)


class AESCipher:
    def __init__(self, key: str):
        self.fernet = Fernet(self.generate_key(key=key))

    def encrypt(self, message: str) -> str:
        """加密数据"""
        encrypted_text = self.fernet.encrypt(message.encode())
        return b64encode(encrypted_text).decode()

    def decrypt(self, message: str) -> str:
        """解密数据"""
        decrypted_text = self.fernet.decrypt(b64decode(message.encode()))
        return decrypted_text.decode()

    @staticmethod
    def generate_key(key: str):
        """生成密钥"""
        # 使用SHA-256确保得到32字节输出
        digest = hashlib.sha256(key.encode()).digest()

        # 使用URL安全的base64编码
        key = urlsafe_b64encode(digest)  # type: ignore
        return key


def generate_random_code(length=16):
    # 使用字母和数字的组合
    alphabet = string.ascii_letters + string.digits
    key = "".join(secrets.choice(alphabet) for _ in range(length))
    return key


if __name__ != "__main__":
    aes_cipher = AESCipher(settings.SECRET_KEY)

else:
    pass

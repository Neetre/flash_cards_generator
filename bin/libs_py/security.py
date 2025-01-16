'''
This is an enhanced security module that provides functions for generating keypairs, signing transactions, verifying signatures,
and additional security features like password strength checking, TOTP for 2FA, and secure key management.

Neetre 2025
'''

import json
import logging
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.backends import default_backend
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import serialization
import pyotp


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()

class Security:
    def __init__(self) -> None:
        pass

    # Base operations on password
    @staticmethod
    def generate(password):
        if not Security.is_password_strong(password):
            raise ValueError("Password does not meet strength requirements")
        
        key = Security.generate_key()
        Security.save_key(key)
        
        enc_pwd = Security.encrypt_password(password, key)
        
        return enc_pwd

    @staticmethod
    def generate_key():
        return Fernet.generate_key()

    @staticmethod
    def encrypt_password(password: str, key: bytes) -> bytes:
        f = Fernet(key)
        encrypted_password = f.encrypt(password.encode("utf-8"))
        logger.info("Password encrypted successfully")
        return encrypted_password
    
    @staticmethod
    def decrypt_password(enc_password, key) -> str:
        f = Fernet(key)
        dec_password = f.decrypt(enc_password).decode("utf-8")
        logger.info("Password decrypted successfully")
        return dec_password
    
    @staticmethod
    def verify_password(provided_password: str, stored_encrypted_password: bytes, key: bytes) -> bool:
        """
        Verify if the provided password matches the stored encrypted password
        """
        try:
            f = Fernet(key)
            decrypted_stored = f.decrypt(stored_encrypted_password).decode("utf-8")
            return decrypted_stored == provided_password
        except Exception as e:
            logger.error(f"Password verification failed: {e}")
            return False
    
    @staticmethod
    def save_key(key: bytes, filename="secret.key") -> None:
        with open(filename, 'wb') as key_file:
            key_file.write(key)
        logger.info("Key saved to secret.key")
            
    @staticmethod
    def load_key(filename="secret.key") -> bytes:
        try:
            key = open(filename, 'rb').read()
            logger.info("Key loaded from secret.key")
            return key
        except FileNotFoundError:
            logger.error("Key file not found")
            raise

    @staticmethod
    def is_password_strong(password):
        if len(password) < 8:
            return False
        if not any(char.isdigit() for char in password):
            return False
        if not any(char.isupper() for char in password):
            return False
        if not any(char.islower() for char in password):
            return False
        return True

    # Stuff for transactions
    @staticmethod
    def generate_key_pair(password):
        private_key = rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend()
        )
        public_key = private_key.public_key()
        
        pem = private_key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.BestAvailableEncryption(password.encode('utf-8'))
        )
        
        logger.info("Key pair generated successfully")
        return pem, public_key

    @staticmethod
    def decode_pem(pem_data, password):
        try:
            private_key = serialization.load_pem_private_key(
                pem_data,
                password=password.encode("utf-8"),
                backend=default_backend()
            )
            logger.info("PEM decoded successfully")
            return private_key
        except Exception as e:
            logger.error(f"Failed to decode PEM: {e}")
            raise

    @staticmethod
    def sign_transaction(transaction, pem, password):
        transaction_bytes = json.dumps(transaction, sort_keys=True).encode("utf-8")
        private_key = Security.decode_pem(pem, password)
        signature = private_key.sign(
            transaction_bytes,
            padding.PSS(
                mgf=padding.MGF1(hashes.SHA256()),
                salt_length=padding.PSS.MAX_LENGTH
            ),
            hashes.SHA256()
        )
        logger.info("Transaction signed successfully")
        return signature

    @staticmethod
    def verify_signature(transaction, signature, public_key):
        transaction_bytes = json.dumps(transaction, sort_keys=True).encode("utf-8")
        try:
            public_key.verify(
                signature,
                transaction_bytes,
                padding.PSS(
                    mgf=padding.MGF1(hashes.SHA256()),
                    salt_length=padding.PSS.MAX_LENGTH
                ),
                hashes.SHA256()
            )
            logger.info("Signature verified successfully")
            return True
        except Exception as e:
            logger.error(f"Signature verification failed: {e}")
            return False

    # 2FA
    @staticmethod
    def generate_2FA_code():
        secret = pyotp.random_base32()
        totp = pyotp.TOTP(secret)
        code = totp.now()
        logger.info("2FA code generated successfully")
        return code, secret

    @staticmethod
    def verify_2FA_code(code, secret):
        totp = pyotp.TOTP(secret)
        is_valid = totp.verify(code)
        logger.info(f"2FA code verification: {is_valid}")
        return is_valid

    # Key Rotation
    @staticmethod
    def rotate_key(old_key):
        '''
        Rotate the encryption key by generating a new key and securely archiving the old key.
        Args:
            old_key: The old encryption key to be retired.
        Returns:
            new_key: The newly generated encryption key.
        '''
        new_key = Security.generate_key()
        Security.save_key(new_key)
        Security.save_key(old_key, "old_secret.key")
        logger.info("Old key archived securely")
        
        logger.info("Key rotated successfully")
        return new_key
    
    @staticmethod
    def re_encrypt_data(old_key, new_key, encrypted_data):
        '''
        Re-encrypt data using the new key after decrypting it with the old key.
        Args:
            old_key: The old encryption key.
            new_key: The new encryption key.
            encrypted_data: Data encrypted with the old key.
        Returns:
            Re-encrypted data using the new key.
        '''
        decrypted_data = Security.decrypt_password(encrypted_data, old_key)
        re_encrypted_data = Security.encrypt_password(decrypted_data, new_key)

        logger.info("Data re-encrypted successfully")
        return re_encrypted_data


if __name__ == "__main__":
    security = Security()
    password = "StrongPassword123"
    enc_pwd = security.generate(password)
    print(f"Encrypted Password: {enc_pwd}")

    # Example of 2FA
    code, secret = security.generate_2FA_code()
    print(f"2FA Code: {code}")
    print(f"2FA Secret: {secret}")
    is_valid = security.verify_2FA_code(code, secret)
    print(f"2FA Code Valid: {is_valid}")

"""
aes_encryption.py — Dynamic Key Pool and AES-128 GCM Re-Keying Controller
Team 181 | Hybrid Cryptographic Systems
"""

import hashlib
import numpy as np
from Crypto.Cipher import AES


class DynamicAESCipherController:
    """Manages secure key buffers, SHA-256 KDF key derivation, and payload re-keying."""

    def __init__(self):
        self.key_pool = []
        self.current_key = None
        self.key_id = 0

    def add_distilled_bits(self, bits):
        self.key_pool.extend(bits)

    def rotate_key_if_ready(self, min_bits=128):
        if len(self.key_pool) >= min_bits:
            raw_bits_bytes = np.packbits(self.key_pool[:min_bits]).tobytes()
            # Deriving 128-bit AES key via SHA-256 KDF
            self.current_key = hashlib.sha256(raw_bits_bytes).digest()[:16]
            self.key_pool = self.key_pool[min_bits:]
            self.key_id += 1
            return True
        return False

    def sanitize_memory(self):
        """Flushes key memory buffers immediately upon security abort."""
        self.key_pool.clear()
        self.current_key = None

    def encrypt_payload(self, plaintext: bytes) -> dict:
        if self.current_key is None:
            raise SecurityError("No active AES session key available.")
        cipher = AES.new(self.current_key, AES.MODE_GCM)
        ciphertext, tag = cipher.encrypt_and_digest(plaintext)
        return {"nonce": cipher.nonce, "ciphertext": ciphertext, "tag": tag, "key_id": self.key_id}

    def decrypt_payload(self, encrypted_data: dict) -> bytes:
        if self.current_key is None:
            raise SecurityError("No active AES session key available.")
        cipher = AES.new(self.current_key, AES.MODE_GCM, nonce=encrypted_data["nonce"])
        return cipher.decrypt_and_verify(encrypted_data["ciphertext"], encrypted_data["tag"])


class SecurityError(Exception):
    pass
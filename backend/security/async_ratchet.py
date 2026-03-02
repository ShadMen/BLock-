"""Криптографические примитивы для E2E-мессенджера.

Модуль показывает учебную реализацию:
- derivation root/chain keys через HKDF-подобный механизм на HMAC-SHA256;
- отправку/приём сообщений с одноразовыми message keys;
- асинхронность (получатель может расшифровать позже без онлайн-сессии).

Важно: это reference-реализация для архитектурного старта, а не готовая
продакшн-криптобиблиотека. Для релиза следует использовать libsignal/MLS.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import hmac
from typing import Tuple


def _hmac_sha256(key: bytes, data: bytes) -> bytes:
    """Возвращает HMAC-SHA256(key, data)."""
    return hmac.new(key, data, hashlib.sha256).digest()


def kdf_root(root_key: bytes, dh_out: bytes) -> Tuple[bytes, bytes]:
    """Обновляет root key и выводит новую chain key.

    Args:
        root_key: Текущий root key (32 байта).
        dh_out: Выход DH/X25519-операции (32 байта).

    Returns:
        Tuple[new_root_key, new_chain_key].
    """
    material = _hmac_sha256(root_key, b"rk" + dh_out)
    new_root = _hmac_sha256(material, b"root")
    new_chain = _hmac_sha256(material, b"chain")
    return new_root, new_chain


def kdf_chain(chain_key: bytes) -> Tuple[bytes, bytes]:
    """Derive next chain key + message key.

    Args:
        chain_key: Текущий chain key.

    Returns:
        Tuple[next_chain_key, message_key].
    """
    next_chain = _hmac_sha256(chain_key, b"ck")
    message_key = _hmac_sha256(chain_key, b"mk")
    return next_chain, message_key


def xor_stream_encrypt(key: bytes, plaintext: bytes, nonce: bytes) -> bytes:
    """Учебный stream cipher на HMAC-потоке.

    Для продакшна заменяется на AES-GCM или ChaCha20-Poly1305.
    """
    out = bytearray()
    counter = 0
    while len(out) < len(plaintext):
        block = _hmac_sha256(key, nonce + counter.to_bytes(4, "big"))
        out.extend(block)
        counter += 1
    return bytes(a ^ b for a, b in zip(plaintext, out[: len(plaintext)]))


@dataclass
class RatchetState:
    """Состояние Double Ratchet стороны диалога.

    Attributes:
        root_key: Корневой ключ сессии.
        send_chain_key: Цепочка отправки.
        recv_chain_key: Цепочка приёма.
        send_counter: Номер исходящего сообщения.
        recv_counter: Номер входящего сообщения.
    """

    root_key: bytes
    send_chain_key: bytes
    recv_chain_key: bytes
    send_counter: int = 0
    recv_counter: int = 0

    def encrypt_message(self, plaintext: bytes) -> tuple[int, bytes, bytes]:
        """Шифрует сообщение и продвигает send-chain.

        Returns:
            (message_index, nonce, ciphertext)
        """
        self.send_chain_key, mk = kdf_chain(self.send_chain_key)
        nonce = hashlib.sha256(self.send_counter.to_bytes(8, "big")).digest()[:12]
        ciphertext = xor_stream_encrypt(mk, plaintext, nonce)
        msg_no = self.send_counter
        self.send_counter += 1
        return msg_no, nonce, ciphertext

    def decrypt_message(self, message_index: int, nonce: bytes, ciphertext: bytes) -> bytes:
        """Расшифровывает сообщение по порядковому номеру.

        Поддерживает асинхронность: можно догнать пропущенные индексы,
        продвигая recv-chain до нужного сообщения.
        """
        while self.recv_counter <= message_index:
            self.recv_chain_key, mk = kdf_chain(self.recv_chain_key)
            if self.recv_counter == message_index:
                plaintext = xor_stream_encrypt(mk, ciphertext, nonce)
                self.recv_counter += 1
                return plaintext
            self.recv_counter += 1
        raise ValueError("message index already processed")

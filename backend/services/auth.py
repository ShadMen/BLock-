"""Сервис авторизации: Google email + TOTP.

Модель:
1) Пользователь вводит email.
2) Система разрешает только домены Google.
3) После OAuth подтверждения email включается второй фактор (TOTP).
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import struct
import time

ALLOWED_DOMAINS = {"gmail.com", "googlemail.com"}


def is_google_email(email: str) -> bool:
    """Проверяет, что email относится к Google-домену."""
    if "@" not in email:
        return False
    domain = email.rsplit("@", 1)[1].lower().strip()
    return domain in ALLOWED_DOMAINS


def _totp_counter(timestamp: int, step_seconds: int = 30) -> int:
    """Возвращает moving factor TOTP."""
    return int(timestamp // step_seconds)


def generate_totp(secret_b32: str, timestamp: int | None = None, digits: int = 6) -> str:
    """Генерирует TOTP код по RFC 6238 (HMAC-SHA1).

    Args:
        secret_b32: Base32 секрет.
        timestamp: Unix timestamp (если None — текущее время).
        digits: Кол-во цифр в коде.
    """
    if timestamp is None:
        timestamp = int(time.time())

    key = base64.b32decode(secret_b32.upper())
    counter = _totp_counter(timestamp)
    msg = struct.pack(">Q", counter)
    digest = hmac.new(key, msg, hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    binary = struct.unpack(">I", digest[offset : offset + 4])[0] & 0x7FFFFFFF
    code = binary % (10**digits)
    return str(code).zfill(digits)


def verify_totp(secret_b32: str, code: str, timestamp: int | None = None, window: int = 1) -> bool:
    """Проверяет TOTP с окном допуска.

    Args:
        secret_b32: Base32 секрет пользователя.
        code: Введённый код.
        timestamp: Текущее время.
        window: Допуск +/- window шагов по 30 сек.
    """
    if timestamp is None:
        timestamp = int(time.time())

    for drift in range(-window, window + 1):
        candidate = generate_totp(secret_b32, timestamp + drift * 30)
        if hmac.compare_digest(candidate, code):
            return True
    return False

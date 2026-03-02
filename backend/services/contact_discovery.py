"""Приватное сопоставление телефонной книги и пользователей.

Идея: клиент отправляет HMAC(pepper, normalized_phone),
а сервер хранит такие же токены для уже зарегистрированных номеров.
Сырые номера не передаются в discovery-API.
"""

from __future__ import annotations

import hashlib
import hmac
import re
from typing import Iterable


def normalize_phone(phone: str) -> str:
    """Нормализует номер в E.164-like формат (только + и цифры)."""
    phone = phone.strip()
    if not phone.startswith("+"):
        raise ValueError("phone must start with '+'")
    digits = re.sub(r"\D", "", phone)
    return f"+{digits}"


def phone_token(phone: str, pepper: bytes) -> str:
    """Создаёт приватный токен телефона для поиска контактов."""
    normalized = normalize_phone(phone).encode("utf-8")
    digest = hmac.new(pepper, normalized, hashlib.sha256).hexdigest()
    return digest


def discover_contacts(local_book: Iterable[str], pepper: bytes, known_tokens: set[str]) -> list[str]:
    """Возвращает список телефонов, которые найдены среди пользователей."""
    matches = []
    for raw in local_book:
        token = phone_token(raw, pepper)
        if token in known_tokens:
            matches.append(normalize_phone(raw))
    return matches

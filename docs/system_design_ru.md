# Архитектура мессенджера (Windows + Android)

## 1. Цели продукта

- Приватный мессенджер с каналами, звонками и видеоконференциями.
- Авторизация: только Google email + TOTP.
- Поиск людей: телефонная книга + username.
- Лента каналов: единая «стенка» по времени публикации.

## 2. Технологический стек (рекомендуемый)

- **Клиенты**:
  - Android: Kotlin + Jetpack Compose.
  - Windows: Kotlin Multiplatform Desktop (Compose Multiplatform) или C#/.NET + WebRTC SDK.
- **Backend**:
  - API Gateway: gRPC/HTTP.
  - Auth service, User service, Messaging service, Channel service, Media service, Call signaling service.
- **Хранилища**:
  - PostgreSQL (пользователи, каналы, metadata).
  - Redis (presence, short-lived tokens, ratelimits).
  - Object Storage (голос/видео сообщения, вложения).
  - Kafka/NATS (события, fan-out, async обработка).

## 3. Безопасность

### 3.1 E2E модель

Использовать схему как в Signal:
- **X3DH** для асинхронного установления сессии (когда получатель оффлайн).
- **Double Ratchet** для forward secrecy и post-compromise security.

В репозитории есть reference-реализация key-деривации и ratchet logic:
- `backend/security/async_ratchet.py`

### 3.2 Практические правила безопасности

1. TLS 1.3 между клиентом и сервером.
2. Ключи устройства хранятся в Android Keystore / Windows DPAPI.
3. Сервер не хранит plaintext сообщений.
4. Для вложений: отдельный key per attachment + encrypt-then-upload.
5. Для звонков: SRTP + DTLS (WebRTC), E2EE insertable streams при необходимости.

## 4. Аутентификация

### Поток

1. Пользователь вводит email.
2. Проверяем домен (`gmail.com` / `googlemail.com`).
3. Google OAuth2 login.
4. Обязательный TOTP (MFA).
5. Выдача access + refresh токенов (short TTL + rotation).

Реализация TOTP и валидации домена:
- `backend/services/auth.py`

## 5. Контакты и username-поиск

- Username-поиск: индекс в БД (case-insensitive unique).
- Телефонная книга: приватное сопоставление через HMAC-токены телефонов.

Reference-файл:
- `backend/services/contact_discovery.py`

## 6. Каналы и общая стенка новостей

Каждый канал хранит посты по убыванию timestamp.
Для общей ленты пользователя объединяем N каналов через k-way merge.

Reference-файл:
- `backend/services/news_feed.py`

## 7. Голосовые/видео сообщения

- Клиент кодирует медиа (Opus/AAC/H.264/VP9/AV1 по платформе).
- Шифрует симметричным ключом на клиенте.
- Загружает в object storage, в сообщение отправляет только encrypted metadata + URI.

## 8. Видеозвонки и screen sharing

- Сигналинг через ваш backend (WebSocket/gRPC stream).
- Media plane: WebRTC (STUN/TURN обязательно).
- Групповые созвоны: SFU (например, mediasoup/LiveKit/Jitsi stack).
- Screen share: отдельный видеотрек в WebRTC с permission/UI-индикацией.

## 9. Документация алгоритмов из кода

### `kdf_root(root_key, dh_out)`
Обновляет корневой ключ сессии и порождает новую цепочку.

### `kdf_chain(chain_key)`
Порождает ключ сообщения и следующий ключ цепочки.

### `RatchetState.encrypt_message(...)`
Берёт следующий message key, шифрует payload, увеличивает send counter.

### `RatchetState.decrypt_message(...)`
Догоняет recv chain до нужного индекса сообщения и расшифровывает его.

### `generate_totp(secret_b32, timestamp, digits)`
Реализация TOTP по RFC 6238 через HMAC-SHA1 + dynamic truncation.

### `verify_totp(secret_b32, code, window)`
Проверка TOTP с временным окном (обычно ±1 шаг).

### `phone_token(phone, pepper)`
Считает HMAC SHA-256 от нормализованного номера телефона.

### `merge_channel_feeds(feeds, limit)`
Объединяет ленты каналов в общий поток через heap (сложность O(L log K)).

## 10. Этапы разработки (roadmap)

1. MVP чат + auth + username search.
2. Контакт-дискавери и каналы.
3. Голосовые/видео сообщения.
4. 1:1 звонки.
5. Групповые видеоконференции + screen share.
6. Усиление криптоаудита и нагрузочное тестирование.

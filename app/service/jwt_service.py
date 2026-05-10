from datetime import datetime, timedelta, timezone
from typing import Any

import jwt

from app.exceptions.email_verification_exception import EmailVerificationException


class JWTService:
    """Генерация и верификация JWT-токенов для подтверждения email."""

    def __init__(self, secret: str) -> None:
        self.__secret = secret

    def generate_verification_token(self, application_id: int, email: str) -> str:
        """Генерирует JWT-токен для подтверждения email. Срок действия — 1 час."""
        now = datetime.now(timezone.utc)
        payload = {
            'sub': 'email_verification',
            'app_id': application_id,
            'email': email,
            'iat': now,
            'exp': now + timedelta(hours=1)
        }
        token = jwt.encode(payload, self.__secret, algorithm='HS256')
        if isinstance(token, bytes):
            token = token.decode('utf-8')
        return token

    def verify_token(self, token: str) -> dict[str, Any]:
        """Декодирует и валидирует токен. Выбрасывает EmailVerificationException при невалидном токене.

        Returns:
            Payload токена с ключами: ``app_id`` (int), ``email`` (str), ``sub``, ``iat``, ``exp``.
        """
        try:
            payload = jwt.decode(
                token,
                self.__secret,
                algorithms=['HS256'],
                options={'require': ['sub', 'app_id', 'email', 'iat', 'exp']}
            )
            if payload.get('sub') != 'email_verification':
                raise jwt.InvalidTokenError("Неверный тип токена")
            return payload
        except jwt.ExpiredSignatureError:
            raise EmailVerificationException("Срок действия ссылки истек")
        except jwt.InvalidTokenError:
            raise EmailVerificationException("Недействительная ссылка подтверждения")

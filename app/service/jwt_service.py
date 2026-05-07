from datetime import datetime, timedelta, timezone

import jwt

from app.exceptions.email_verification_exception import EmailVerificationException


class JWTService:
    def __init__(self, secret):
        self.__secret = secret

    def generate_verification_token(self, application_id, email):
        now = datetime.now(timezone.utc)

        payload = {
            'sub': 'email_verification',
            'app_id': application_id,
            'email': email,
            'iat': now,
            'exp': now + timedelta(minutes=10)
        }

        token = jwt.encode(payload, self.__secret, algorithm='HS256')

        if isinstance(token, bytes):
            token = token.decode('utf-8')

        return token

    def verify_token(self, token):
        try:
            payload = jwt.decode(
                token,
                self.__secret,
                algorithms=['HS256'],
                options={
                    'require': ['sub', 'app_id', 'email', 'iat', 'exp']
                }
            )

            if payload.get('sub') != 'email_verification':
                raise jwt.InvalidTokenError("Неверный тип токена")
            return payload
        except jwt.ExpiredSignatureError as e:
            raise EmailVerificationException("Срок действия ссылки истек")
        except jwt.InvalidTokenError as e:
            raise EmailVerificationException("Недействительная ссылка подтверждения")
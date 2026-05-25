"""
Безопасность JWT-токенов подтверждения email.

Покрывает JWTService:
  - HS256, подпись секретом приложения;
  - exp=1 час, iat — фиксируются;
  - sub='email_verification', другие sub не принимаются;
  - require=[sub, app_id, email, iat, exp];
  - токен с подписью другим секретом отклоняется;
  - токен с алгоритмом 'none' отклоняется (CVE-класса 2015 года);
  - истёкший токен → EmailVerificationException.
"""
from datetime import datetime, timedelta, timezone

import jwt as pyjwt
import pytest
from freezegun import freeze_time

from app.exceptions.email_verification_exception import EmailVerificationException
from app.service.jwt_service import JWTService


SECRET = "jwt-test-secret-key-32-chars-min!"
OTHER_SECRET = "another-secret-not-the-real-one!"


@pytest.fixture
def svc():
    return JWTService(SECRET)


class TestGenerateToken:

    def test_returns_string_three_parts(self, svc):
        token = svc.generate_verification_token(42, "u@test.com")
        assert isinstance(token, str)
        assert token.count(".") == 2  # header.payload.signature

    def test_payload_contains_required_claims(self, svc):
        token = svc.generate_verification_token(42, "u@test.com")
        payload = pyjwt.decode(token, SECRET, algorithms=["HS256"])
        assert payload["sub"] == "email_verification"
        assert payload["app_id"] == 42
        assert payload["email"] == "u@test.com"
        assert "iat" in payload and "exp" in payload

    def test_token_uses_hs256_algorithm(self, svc):
        """Заголовок токена должен быть HS256, не none и не RS256."""
        token = svc.generate_verification_token(1, "x@x.ru")
        header = pyjwt.get_unverified_header(token)
        assert header["alg"] == "HS256"

    def test_exp_one_hour_after_iat(self, svc):
        with freeze_time("2026-05-19 10:00:00"):
            token = svc.generate_verification_token(1, "x@x.ru")
            payload = pyjwt.decode(token, SECRET, algorithms=["HS256"])
            assert payload["exp"] - payload["iat"] == 3600


class TestVerifyToken:

    def test_valid_token_returns_payload(self, svc):
        token = svc.generate_verification_token(7, "alice@test.com")
        payload = svc.verify_token(token)
        assert payload["app_id"] == 7
        assert payload["email"] == "alice@test.com"

    def test_token_signed_with_other_secret_rejected(self, svc):
        forged = pyjwt.encode(
            {
                "sub": "email_verification", "app_id": 1, "email": "x@x.ru",
                "iat": datetime.now(timezone.utc),
                "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            },
            OTHER_SECRET,
            algorithm="HS256",
        )
        with pytest.raises(EmailVerificationException):
            svc.verify_token(forged)

    def test_token_with_alg_none_rejected(self, svc):
        """Классическая уязвимость JWT — попытка пройти проверку с alg='none'."""
        forged = pyjwt.encode(
            {
                "sub": "email_verification", "app_id": 1, "email": "x@x.ru",
                "iat": datetime.now(timezone.utc),
                "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            },
            None,
            algorithm="none",
        )
        with pytest.raises(EmailVerificationException):
            svc.verify_token(forged)

    def test_token_with_wrong_sub_rejected(self, svc):
        """Только sub='email_verification' допускается."""
        forged = pyjwt.encode(
            {
                "sub": "password_reset", "app_id": 1, "email": "x@x.ru",
                "iat": datetime.now(timezone.utc),
                "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            },
            SECRET,
            algorithm="HS256",
        )
        with pytest.raises(EmailVerificationException):
            svc.verify_token(forged)

    def test_token_missing_claim_rejected(self, svc):
        """options={'require': [...]} — все обязательные поля должны быть."""
        # без 'app_id'
        forged = pyjwt.encode(
            {
                "sub": "email_verification", "email": "x@x.ru",
                "iat": datetime.now(timezone.utc),
                "exp": datetime.now(timezone.utc) + timedelta(hours=1),
            },
            SECRET,
            algorithm="HS256",
        )
        with pytest.raises(EmailVerificationException):
            svc.verify_token(forged)

    def test_expired_token_rejected(self, svc):
        with freeze_time("2026-05-19 10:00:00"):
            token = svc.generate_verification_token(1, "x@x.ru")
        # +2 часа — токен протух (exp=1ч)
        with freeze_time("2026-05-19 12:00:01"):
            with pytest.raises(EmailVerificationException) as ei:
                svc.verify_token(token)
            assert "истек" in ei.value.message.lower() or "истёк" in ei.value.message.lower()

    def test_garbage_token_rejected(self, svc):
        for bad in ("", "not.a.jwt", "abc.def.ghi", "x" * 200):
            with pytest.raises(EmailVerificationException):
                svc.verify_token(bad)

    def test_tampered_payload_rejected(self, svc):
        """Изменение payload без знания секрета → подпись не сходится."""
        token = svc.generate_verification_token(1, "x@x.ru")
        header, payload, sig = token.split(".")
        # подменяем середину на другой base64
        import base64, json
        decoded = json.loads(base64.urlsafe_b64decode(payload + "==").decode())
        decoded["app_id"] = 999
        new_payload = base64.urlsafe_b64encode(
            json.dumps(decoded).encode()
        ).decode().rstrip("=")
        tampered = f"{header}.{new_payload}.{sig}"
        with pytest.raises(EmailVerificationException):
            svc.verify_token(tampered)

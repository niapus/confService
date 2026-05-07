from datetime import datetime, timedelta, timezone

import jwt
import pytest

from app.exceptions.email_verification_exception import EmailVerificationException
from app.service.jwt_service import JWTService


@pytest.fixture
def jwt_service():
    return JWTService(secret="test_secret_key")


class TestGenerateVerificationToken:

    def test_generates_valid_token(self, jwt_service):
        token = jwt_service.generate_verification_token(1, "test@test.com")

        payload = jwt.decode(token, "test_secret_key", algorithms=['HS256'])
        assert payload['sub'] == 'email_verification'
        assert payload['app_id'] == 1
        assert payload['email'] == 'test@test.com'
        assert 'iat' in payload
        assert 'exp' in payload

    def test_token_expires_in_10_minutes(self, jwt_service):
        token = jwt_service.generate_verification_token(1, "test@test.com")

        payload = jwt.decode(token, "test_secret_key", algorithms=['HS256'])
        exp = datetime.fromtimestamp(payload['exp'], tz=timezone.utc)
        iat = datetime.fromtimestamp(payload['iat'], tz=timezone.utc)

        diff = exp - iat
        assert diff == timedelta(minutes=10)

    def test_token_is_string(self, jwt_service):
        token = jwt_service.generate_verification_token(1, "test@test.com")
        assert isinstance(token, str)

    def test_token_handles_bytes_return(self, jwt_service):
        from unittest.mock import patch
        with patch('app.service.jwt_service.jwt.encode', return_value=b'bytes_token'):
            token = jwt_service.generate_verification_token(1, "test@test.com")
            assert isinstance(token, str)
            assert token == "bytes_token"


class TestVerifyToken:

    def test_verify_valid_token(self, jwt_service):
        token = jwt_service.generate_verification_token(42, "user@test.com")

        payload = jwt_service.verify_token(token)

        assert payload['sub'] == 'email_verification'
        assert payload['app_id'] == 42
        assert payload['email'] == 'user@test.com'

    def test_verify_expired_token(self, jwt_service):
        now = datetime.now(timezone.utc)
        payload = {
            'sub': 'email_verification',
            'app_id': 1,
            'email': 'test@test.com',
            'iat': now - timedelta(minutes=20),
            'exp': now - timedelta(minutes=10)
        }
        token = jwt.encode(payload, "test_secret_key", algorithm='HS256')

        with pytest.raises(EmailVerificationException):
            jwt_service.verify_token(token)

    def test_verify_invalid_token(self, jwt_service):
        with pytest.raises(EmailVerificationException):
            jwt_service.verify_token("invalid_token_string")

    def test_verify_token_wrong_subject(self, jwt_service):
        now = datetime.now(timezone.utc)
        payload = {
            'sub': 'wrong_subject',
            'app_id': 1,
            'email': 'test@test.com',
            'iat': now,
            'exp': now + timedelta(minutes=10)
        }
        token = jwt.encode(payload, "test_secret_key", algorithm='HS256')

        with pytest.raises(EmailVerificationException):
            jwt_service.verify_token(token)

    def test_verify_token_missing_required_fields(self, jwt_service):
        now = datetime.now(timezone.utc)
        payload = {
            'sub': 'email_verification',
            'iat': now,
            'exp': now + timedelta(minutes=10)
        }
        token = jwt.encode(payload, "test_secret_key", algorithm='HS256')

        with pytest.raises(EmailVerificationException):
            jwt_service.verify_token(token)

    def test_verify_token_wrong_secret(self, jwt_service):
        now = datetime.now(timezone.utc)
        payload = {
            'sub': 'email_verification',
            'app_id': 1,
            'email': 'test@test.com',
            'iat': now,
            'exp': now + timedelta(minutes=10)
        }
        token = jwt.encode(payload, "wrong_secret", algorithm='HS256')

        with pytest.raises(EmailVerificationException):
            jwt_service.verify_token(token)

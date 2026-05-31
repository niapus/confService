from functools import wraps
from typing import Callable, Any

from flask import jsonify, current_app, session as flask_session

from app import AppException


def handle_api_errors(f: Callable) -> Callable:
    """Декоратор для API-роутов. Перехватывает AppException - JSON с нужным статусом,
    все остальные исключения - JSON 500 с логированием."""
    @wraps(f)
    def decorated(*args: Any, **kwargs: Any) -> Any:
        try:
            return f(*args, **kwargs)
        except AppException as e:
            return jsonify({
                'error': e.message,
                'status_code': e.status_code
            }), e.status_code
        except Exception as e:
            current_app.logger.error(
                f"Необработанная ошибка API: {e}",
                exc_info=True
            )
            return jsonify({
                'error': 'Внутренняя ошибка сервера',
                'status_code': 500
            }), 500
    return decorated


def require_admin_api(f: Callable) -> Callable:
    """Декоратор для API-роутов. Возвращает JSON 403, если администратор не авторизован."""
    @wraps(f)
    def decorated(*args: Any, **kwargs: Any) -> Any:
        if not flask_session.get("admin_id"):
            return jsonify({
                'error': 'Доступ запрещен',
                'status_code': 403
            }), 403
        return f(*args, **kwargs)
    return decorated

from functools import wraps
from typing import Callable, Any

from flask import render_template, request, g

from app.exceptions.conversion_exception import ConversionException
from app.exceptions.file_exception import FileException
from app.exceptions.validation_exception import ValidationException


def handle_form_errors(template_name: str, pass_conf_id: bool = False) -> Callable:
    """Декоратор для форм. При ValidationException, ConversionException или FileException
    повторно рендерит шаблон с данными формы и сообщением об ошибке.

    Args:
        template_name: Имя шаблона для повторного рендера при ошибке.
        pass_conf_id: Передавать ли conf_id из kwargs в контекст шаблона.
    """
    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated(*args: Any, **kwargs: Any) -> Any:
            try:
                return f(*args, **kwargs)
            except (ValidationException, ConversionException, FileException) as e:
                g._has_error = True
                context = {
                    'form_data': request.form,
                    'error': str(e)
                }
                if pass_conf_id:
                    context['conf_id'] = kwargs.get('conf_id')
                return render_template(template_name, **context)
        return decorated
    return decorator

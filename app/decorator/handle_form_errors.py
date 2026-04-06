from functools import wraps

from flask import render_template, request

from app.exceptions.conflict_exception import ConflictException
from app.exceptions.conversion_exception import ConversionException
from app.exceptions.file_exception import FileException
from app.exceptions.validation_exception import ValidationException


def handle_form_errors(template_name, pass_conf_id=False):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            try:
                return f(*args, **kwargs)
            except (ValidationException, ConversionException, ConflictException, FileException) as e:

                context = {
                    'form_data': request.form,
                    'error': str(e)
                }

                if pass_conf_id:
                    context['conf_id'] = kwargs.get('conf_id')

                return render_template(template_name, **context)
        return decorated
    return decorator
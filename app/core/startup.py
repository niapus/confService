import logging
import os
from logging.handlers import RotatingFileHandler

from app.core import database
from app.core.database import init_db
from app.exceptions.startup_exception import AdminConfigException, DatabaseSetupException, StartupException, \
    LoggingSetupException, EnvironmentValidationException


def init_app(app):
    try:
        __setup_logging(app)
        app.logger.info("✅ Логирование настроено")
        __validate_environment(app)
        app.logger.info("✅ Окружение проверено")

        __init_database()
        app.logger.info("✅ База данных создана")

        __create_admin(app)
        app.logger.info("✅ Админы созданы")
    except StartupException as e:
        e.exit()

def __validate_environment(app):

    errors = []
    secret_key = app.config.get('SECRET_KEY')
    if not secret_key:
        errors.append('SECRET_KEY не задан в переменных окружения')
    elif len(secret_key) < 32:
        errors.append(f'SECRET_KEY слишком короткий: минимальная длина - 32, поступило - {len(secret_key)}')

    admin_data = app.config.get('ADMIN_DATA')

    if not admin_data:
        errors.append('ADMIN_DATA не задан в переменных окружения')
    else:
        admin_errors = __validate_admin_data_format(admin_data)
        errors.extend(admin_errors)

    mail_enabled = app.config.get('MAIL_ENABLED')
    verification_enabled = app.config.get('EMAIL_VERIFICATION_ENABLED')

    if verification_enabled and not mail_enabled:
        errors.append(
            'EMAIL_VERIFICATION_ENABLED=true, но MAIL_ENABLED=false. '
            'Верификация почты требует включенной отправки сообщений.'
        )

    if mail_enabled:
        mail_server = app.config.get('MAIL_SERVER')
        mail_port = app.config.get('MAIL_PORT')
        mail_use_tls = app.config.get('MAIL_USE_TLS')
        mail_username = app.config.get('MAIL_USERNAME')
        mail_password = app.config.get('MAIL_PASSWORD')
        mail_default_sender = app.config.get('MAIL_DEFAULT_SENDER')

        missing_mail = []
        if not mail_server: missing_mail.append('MAIL_SERVER')
        if not mail_port: missing_mail.append('MAIL_PORT')
        if not mail_use_tls: missing_mail.append('MAIL_USE_TLS')
        if not mail_username: missing_mail.append('MAIL_USERNAME')
        if not mail_password: missing_mail.append('MAIL_PASSWORD')
        if not mail_default_sender: missing_mail.append('MAIL_DEFAULT_SENDER')

        if missing_mail:
            errors.append(
                f'Почта включена (MAIL_ENABLED=true), но настройки заданы не полностью. '
                f'Отсутствуют: {", ".join(missing_mail)}.'
            )

    if errors:
        raise EnvironmentValidationException(errors)



def __validate_admin_data_format(admin_data: str) -> list:
    """Проверяет формат ADMIN_DATA. Возвращает список ошибок."""
    errors = []
    seen_logins = set()

    for i, item in enumerate(admin_data.split(','), 1):
        item = item.strip()

        if ':' not in item:
            errors.append(f'ADMIN_DATA: запись #{i} имеет неверный формат. Ожидается "логин:пароль"')
            continue

        login, password = item.split(':', 1)
        login = login.strip()
        password = password.strip()

        if not login:
            errors.append(f'ADMIN_DATA: запись #{i} — пустой логин')
        elif len(login) < 4:
            errors.append(f'ADMIN_DATA: запись #{i} — логин "{login}" слишком короткий (минимум 4 символа)')
        elif login in seen_logins:
            errors.append(f'ADMIN_DATA: запись #{i} — повторяющийся логин "{login}"')

        if not password:
            errors.append(f'ADMIN_DATA: запись #{i} — пустой пароль для логина "{login}"')
        elif len(password) < 8:
            errors.append(f'ADMIN_DATA: запись #{i} — пароль для "{login}" слишком короткий (минимум 8 символа)')

        seen_logins.add(login)

    return errors

def __setup_logging(app):
    try:
        os.makedirs(app.config['LOGS_FOLDER'], exist_ok=True)

        app.logger.handlers.clear()

        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')

        file_handler = RotatingFileHandler(
            filename=os.path.join(app.config['LOGS_FOLDER'], 'app.log'),
            maxBytes=1024*1024*5,
            backupCount=5,
            encoding='utf-8'
        )

        file_handler.setFormatter(formatter)
        app.logger.addHandler(file_handler)

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        app.logger.addHandler(console_handler)

        app.logger.setLevel(logging.INFO)
    except Exception as e:
        raise LoggingSetupException(str(e)) from e

def __init_database():
    try:
        init_db()
    except Exception as e:
        raise DatabaseSetupException(e)

def __create_admin(app):
    session = database.Session()
    try:
        app.extensions['services'].admin.create_admins_from_env(
            env_admin_data=app.config['ADMIN_DATA'],
            session=session
        )
        session.commit()
    except AdminConfigException as e:
        session.rollback()
        raise

    except Exception as e:
        session.rollback()
        raise StartupException(f"Ошибка создания администраторов: {e}") from e
    finally:
        session.close()
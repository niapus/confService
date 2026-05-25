import os


# Количество воркеров
workers = int(os.environ.get("GUNICORN_WORKERS", 4))

# worker_class = "gevent"

# Максимум одновременных соединений на один gevent-воркер.
# worker_connections = 1000

# Привязка к порту
bind = "0.0.0.0:5000"

# Логи
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Перезапуск после 10 000 запросов (защита от утечек)
max_requests = 10000
max_requests_jitter = 1000

# Таймауты
timeout = 30
graceful_timeout = 10

preload_app = True


def pre_fork(server, worker):
    os.environ["WORKER_ID"] = str(worker.age)
    print(f"[pre_fork] Воркер {worker.age} готовится к запуску")

def post_fork(server, worker):
    from app.core import database
    if database.engine is not None:
        database.engine.dispose()

    worker_id = os.environ.get('WORKER_ID', '?')
    print(f"[post_fork] Воркер {worker_id} запущен (PID: {worker.pid})")

def post_worker_init(worker):
    app = worker.app.callable
    if app.config.get('MAIL_ENABLED'):
        from app import _try_start_scheduler
        worker_id = os.environ.get('WORKER_ID', str(worker.age))
        _try_start_scheduler(app, worker_id)

def worker_exit(server, worker):
    worker_id = os.environ.get('WORKER_ID', '?')
    print(f"[worker_exit] Воркер {worker_id} завершился (PID: {worker.pid})")
from app import create_app, _try_start_scheduler

app = create_app()

if app.config.get('MAIL_ENABLED'):
    _try_start_scheduler(app, worker_id='local')

if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)

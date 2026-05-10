import os
from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

Base = declarative_base()

engine = None
Session = None
def init_engine(app):
    global engine, Session

    database_url = app.config.get('SQLALCHEMY_DATABASE_URL')

    if database_url.startswith('sqlite:///'):
        db_path = database_url[len('sqlite:///'):]
        db_dir = os.path.dirname(os.path.abspath(db_path))
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)

    engine = create_engine(database_url, echo=app.config.get('SQLALCHEMY_ECHO', False))
    if engine.url.drivername == 'sqlite':
        @event.listens_for(engine, "connect")
        def set_sqlite_pragma(dbapi_connection, _):
            cursor = dbapi_connection.cursor()
            cursor.execute("PRAGMA journal_mode=WAL")
            cursor.close()

    Session = sessionmaker(bind=engine)

def init_db():
    Base.metadata.create_all(engine)
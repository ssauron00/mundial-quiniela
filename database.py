import sqlite3
import os
from pathlib import Path
from flask import g, current_app

def get_db():
    if 'db' not in g:
        # En Railway usar PostgreSQL, en local usar SQLite
        db_url = os.environ.get('DATABASE_URL')
        if db_url:
            import psycopg2
            g.db = psycopg2.connect(db_url, sslmode='require')
        else:
            DATABASE = Path(__file__).parent / 'data' / 'mundial.db'
            DATABASE.parent.mkdir(exist_ok=True)
            g.db = sqlite3.connect(DATABASE)
            g.db.row_factory = sqlite3.Row
            g.db.execute("PRAGMA foreign_keys = ON")
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    db = get_db()
    with current_app.open_resource('schema.sql', mode='r') as f:
        db.executescript(f.read())
    db.commit()

def init_app(app):
    app.teardown_appcontext(close_db)
    @app.cli.command('init-db')
    def init_db_command():
        init_db()
        print('Initialized the database.')

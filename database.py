import sqlite3
import os
from pathlib import Path
from flask import g, current_app

# Detectar si estamos en Railway
IS_RAILWAY = os.environ.get('RAILWAY_ENVIRONMENT') is not None

# En Railway usar /tmp para escritura, en local usar data/
if IS_RAILWAY:
    DB_DIR = Path('/tmp')
else:
    DB_DIR = Path(__file__).parent / 'data'
    DB_DIR.mkdir(exist_ok=True)

DATABASE = DB_DIR / 'mundial.db'

def get_db():
    if 'db' not in g:
        if os.environ.get('DATABASE_URL'):
            import psycopg2
            g.db = psycopg2.connect(os.environ['DATABASE_URL'], sslmode='require')
            g.db.autocommit = False
        else:
            conn = sqlite3.connect(DATABASE)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            g.db = conn
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    get_db()
    if os.environ.get('DATABASE_URL'):
        cursor = get_db().cursor()
        with current_app.open_resource('schema.sql', mode='r') as f:
            schema = f.read()
        statements = schema.split(';')
        for stmt in statements:
            stmt = stmt.strip()
            if stmt and not stmt.startswith('--'):
                try:
                    cursor.execute(stmt)
                except Exception as e:
                    print(f"Warning: {e}")
        get_db().commit()
    else:
        with current_app.open_resource('schema.sql', mode='r') as f:
            get_db().executescript(f.read())
        get_db().commit()

def init_app(app):
    app.teardown_appcontext(close_db)
    @app.cli.command('init-db')
    def init_db_command():
        init_db()
        print('DB initialized.')

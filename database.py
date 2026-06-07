import sqlite3
import os
from pathlib import Path
from flask import g, current_app

def get_db():
    if 'db' not in g:
        db_url = os.environ.get('DATABASE_URL')
        if db_url:
            import psycopg2
            g.db = psycopg2.connect(db_url, sslmode='require')
            g.db.autocommit = False
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

def execute_query(query, params=()):
    db = get_db()
    if hasattr(db, 'execute'):
        return db.execute(query, params)
    else:
        cursor = db.cursor()
        cursor.execute(query, params)
        return cursor

def init_db():
    db = get_db()
    with current_app.open_resource('schema.sql', mode='r') as f:
        schema = f.read()
    
    db_url = os.environ.get('DATABASE_URL')
    if db_url:
        statements = schema.split(';')
        cursor = db.cursor()
        for stmt in statements:
            stmt = stmt.strip()
            if stmt and not stmt.startswith('--'):
                try:
                    cursor.execute(stmt)
                except Exception as e:
                    print(f"Warning: {e}")
        db.commit()
    else:
        db.executescript(schema)
        db.commit()

def init_app(app):
    app.teardown_appcontext(close_db)
    @app.cli.command('init-db')
    def init_db_command():
        init_db()
        print('Initialized the database.')

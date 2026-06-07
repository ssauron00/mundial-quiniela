import sqlite3
import os
from pathlib import Path
from flask import g, current_app

_is_postgres = None

def is_postgres():
    global _is_postgres
    if _is_postgres is None:
        _is_postgres = os.environ.get('DATABASE_URL') is not None
    return _is_postgres

class DBWrapper:
    """Wrapper que convierte ? a %s para PostgreSQL automáticamente"""
    def __init__(self, conn):
        self._conn = conn
    
    def execute(self, query, params=()):
        if is_postgres():
            query = query.replace('?', '%s')
        if hasattr(self._conn, 'execute'):
            return self._conn.execute(query, params)
        else:
            cursor = self._conn.cursor()
            cursor.execute(query, params)
            return cursor
    
    def commit(self):
        self._conn.commit()
    
    def cursor(self):
        return self._conn.cursor()
    
    def __getattr__(self, name):
        return getattr(self._conn, name)

def get_db():
    if 'db' not in g:
        if is_postgres():
            import psycopg2
            conn = psycopg2.connect(os.environ['DATABASE_URL'], sslmode='require')
            conn.autocommit = False
            g.db = DBWrapper(conn)
        else:
            DATABASE = Path(__file__).parent / 'data' / 'mundial.db'
            DATABASE.parent.mkdir(exist_ok=True)
            g.db = DBWrapper(sqlite3.connect(DATABASE))
            g.db._conn.row_factory = sqlite3.Row
            g.db.execute("PRAGMA foreign_keys = ON")
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db._conn.close()

def init_db():
    db = get_db()
    with current_app.open_resource('schema.sql', mode='r') as f:
        schema = f.read()
    
    if is_postgres():
        cursor = db.cursor()
        statements = schema.split(';')
        for stmt in statements:
            stmt = stmt.strip()
            if stmt and not stmt.startswith('--'):
                try:
                    cursor.execute(stmt)
                except Exception as e:
                    print(f"Warning: {e}")
        db.commit()
    else:
        db._conn.executescript(schema)
        db.commit()

def init_app(app):
    app.teardown_appcontext(close_db)
    @app.cli.command('init-db')
    def init_db_command():
        init_db()
        print('Initialized the database.')

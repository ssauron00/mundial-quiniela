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

class CursorWrapper:
    """Wrapper para cursor que funciona con SQLite y PostgreSQL"""
    def __init__(self, cursor, is_pg):
        self._cursor = cursor
        self._is_pg = is_pg
    
    def fetchall(self):
        rows = self._cursor.fetchall()
        if self._is_pg:
            return rows
        return rows
    
    def fetchone(self):
        return self._cursor.fetchone()
    
    def __iter__(self):
        return iter(self._cursor)
    
    @property
    def description(self):
        return self._cursor.description

class DBWrapper:
    def __init__(self, conn):
        self._conn = conn
    
    def execute(self, query, params=()):
        if is_postgres():
            query = query.replace('?', '%s')
        cursor = self._conn.cursor()
        cursor.execute(query, params)
        return CursorWrapper(cursor, is_postgres())
    
    def commit(self):
        self._conn.commit()
    
    def cursor(self):
        return self._conn.cursor()
    
    def close(self):
        self._conn.close()

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
            conn = sqlite3.connect(DATABASE)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA foreign_keys = ON")
            g.db = DBWrapper(conn)
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    db = get_db()
    cursor = db.cursor()
    with current_app.open_resource('schema.sql', mode='r') as f:
        schema = f.read()
    
    if is_postgres():
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
        cursor.executescript(schema)
        db.commit()

def init_app(app):
    app.teardown_appcontext(close_db)
    @app.cli.command('init-db')
    def init_db_command():
        init_db()
        print('Initialized the database.')

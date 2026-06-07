import sqlite3
import os
from pathlib import Path
from flask import g, current_app

DB_PATH = Path('/tmp/mundial.db')
_initialized = False

def _ensure_db():
    global _initialized
    if _initialized:
        return
    
    print(f"Checking database at {DB_PATH}")
    
    if not DB_PATH.exists():
        print("Database does not exist, creating...")
        conn = sqlite3.connect(DB_PATH)
        conn.execute("PRAGMA foreign_keys = ON")
        
        schema_path = Path(__file__).parent / 'schema.sql'
        if schema_path.exists():
            with open(schema_path, 'r') as f:
                conn.executescript(f.read())
            print("Schema executed")
        
        conn.commit()
        conn.close()
        _initialized = True
        print("Database created successfully")
    else:
        print("Database already exists")
        _initialized = True

# Ejecutar al importar
_ensure_db()

def get_db():
    if 'db' not in g:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        g.db = conn
    return g.db

def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    _ensure_db()

def init_app(app):
    app.teardown_appcontext(close_db)
    @app.cli.command('init-db')
    def init_db_command():
        _ensure_db()
        print('DB initialized.')

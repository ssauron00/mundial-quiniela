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

def init_db():
    db = get_db()
    with current_app.open_resource('schema.sql', mode='r') as f:
        schema = f.read()
    
    # Detectar si es PostgreSQL o SQLite
    db_url = os.environ.get('DATABASE_URL')
    if db_url:
        # PostgreSQL: ejecutar statement por statement
        statements = schema.split(';')
        for stmt in statements:
            stmt = stmt.strip()
            if stmt and not stmt.startswith('--'):
                # Adaptar sintaxis SQLite a PostgreSQL
                stmt = stmt.replace('INTEGER PRIMARY KEY AUTOINCREMENT', 'SERIAL PRIMARY KEY')
                stmt = stmt.replace('BOOLEAN', 'BOOLEAN')
                stmt = stmt.replace('DATETIME', 'TIMESTAMP')
                stmt = stmt.replace("NOT NULL DEFAULT CURRENT_TIMESTAMP", "DEFAULT CURRENT_TIMESTAMP")
                try:
                    db.execute(stmt)
                except Exception as e:
                    print(f"Warning executing statement: {e}")
    else:
        # SQLite: executescript funciona bien
        db.executescript(schema)
    
    db.commit()

def init_app(app):
    app.teardown_appcontext(close_db)
    @app.cli.command('init-db')
    def init_db_command():
        init_db()
        print('Initialized the database.')

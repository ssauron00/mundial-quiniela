import sqlite3
import os
from pathlib import Path
from flask import g, current_app

DB_PATH = Path('/tmp/mundial.db')

def _ensure_db():
    """Crear BD y tablas si no existen"""
    if not DB_PATH.exists():
        print(f"Creating database at {DB_PATH}")
        conn = sqlite3.connect(DB_PATH)
        conn.execute("PRAGMA foreign_keys = ON")
        schema_path = Path(__file__).parent / 'schema.sql'
        if schema_path.exists():
            with open(schema_path, 'r') as f:
                conn.executescript(f.read())
        conn.commit()
        
        # Crear admin
        from werkzeug.security import generate_password_hash
        pw_hash = generate_password_hash('admin123')
        conn.execute('INSERT INTO usuarios (email, password_hash, nombre, rol) VALUES (?, ?, ?, ?)',
                     ('admin@example.com', pw_hash, 'Administrador', 'admin'))
        conn.execute('INSERT INTO settings (key, value) VALUES (?, ?)', ('quinielas_activas', '1'))
        conn.commit()
        
        # Cargar CSV
        csv_path = Path(__file__).parent / 'data' / 'partidos.csv'
        if csv_path.exists():
            import csv
            with open(csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    local = row['equipo_local'].strip()
                    visitante = row['equipo_visitante'].strip()
                    cur = conn.execute('INSERT OR IGNORE INTO equipos (nombre) VALUES (?)', (local,))
                    local_id = cur.lastrowid or conn.execute('SELECT id FROM equipos WHERE nombre = ?', (local,)).fetchone()[0]
                    cur = conn.execute('INSERT OR IGNORE INTO equipos (nombre) VALUES (?)', (visitante,))
                    visitante_id = cur.lastrowid or conn.execute('SELECT id FROM equipos WHERE nombre = ?', (visitante,)).fetchone()[0]
                    conn.execute('INSERT OR IGNORE INTO partidos (fase, fecha, equipo_local_id, equipo_visitante_id) VALUES (?, ?, ?, ?)',
                                (row['fase'].strip(), row['fecha'].strip(), local_id, visitante_id))
            conn.commit()
        
        conn.close()
        print("Database initialized")

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

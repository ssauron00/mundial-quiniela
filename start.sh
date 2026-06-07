#!/bin/bash
set -e

cd /app
export FLASK_APP=app.py
mkdir -p /tmp

# Crear BD y tablas si no existen
python3 -c "
import sqlite3
from pathlib import Path

DB_PATH = Path('/tmp/mundial.db')
print(f'Database: {DB_PATH}')

conn = sqlite3.connect(DB_PATH)
conn.execute('PRAGMA foreign_keys = ON')

# Create tables
with open('schema.sql', 'r') as f:
    conn.executescript(f.read())
conn.commit()

# Fix column name if old schema
cursor = conn.execute('PRAGMA table_info(selecciones)')
columns = [row[1] for row in cursor.fetchall()]
if 'elección' in columns and 'eleccion' not in columns:
    conn.execute('ALTER TABLE selecciones RENAME COLUMN \"elección\" TO eleccion')
    conn.commit()
    print('Column renamed to eleccion')

conn.close()
print('DB ready')
"

# Cargar partidos
python3 seed.py

# Crear admin
python3 setup_admin.py

# Iniciar - Railway asigna PORT automáticamente
echo "Starting gunicorn on port $PORT"
gunicorn app:app --bind "0.0.0.0:$PORT" --workers 2 --timeout 120

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
print('Tables created/verified')
conn.close()
"

# Cargar partidos desde CSV
echo "Loading partidos..."
python3 seed.py

# Crear admin
echo "Creating admin..."
python3 setup_admin.py

# Iniciar
echo "Starting gunicorn on port ${PORT:-5000}"
exec gunicorn app:app --bind "0.0.0.0:${PORT:-5000}" --workers 2 --timeout 120

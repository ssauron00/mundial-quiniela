#!/bin/bash
set -e

cd /app
export FLASK_APP=app.py

# Inicializar BD con Python
mkdir -p /tmp
python3 -c "
import sqlite3
from pathlib import Path

DB_PATH = Path('/tmp/mundial.db')
print(f'Creating DB at {DB_PATH}')

conn = sqlite3.connect(DB_PATH)
conn.execute('PRAGMA foreign_keys = ON')

# Leer y ejecutar schema
with open('schema.sql', 'r') as f:
    schema = f.read()

conn.executescript(schema)
conn.commit()
print('Schema created successfully')

# Verificar tablas
tables = conn.execute(\"SELECT name FROM sqlite_master WHERE type='table'\").fetchall()
print(f'Tables: {[t[0] for t in tables]}')
conn.close()
"

# Crear admin
python3 -c "
import sqlite3
from pathlib import Path
from werkzeug.security import generate_password_hash

DB_PATH = Path('/tmp/mundial.db')
conn = sqlite3.connect(DB_PATH)

# Verificar si admin existe
existing = conn.execute('SELECT id FROM usuarios WHERE email = ?', ('admin@example.com',)).fetchone()
if not existing:
    pw_hash = generate_password_hash('admin123')
    conn.execute('INSERT INTO usuarios (email, password_hash, nombre, rol) VALUES (?, ?, ?, ?)',
                 ('admin@example.com', pw_hash, 'Administrador', 'admin'))
    conn.commit()
    print('Admin created')
else:
    print('Admin already exists')

# Crear settings si no existe
existing = conn.execute('SELECT key FROM settings WHERE key = ?', ('quinielas_activas',)).fetchone()
if not existing:
    conn.execute('INSERT INTO settings (key, value) VALUES (?, ?)', ('quinielas_activas', '1'))
    conn.commit()
    print('Settings created')

conn.close()
"

# Cargar partidos desde CSV si hay
python3 -c "
import sqlite3
import csv
from pathlib import Path

DB_PATH = Path('/tmp/mundial.db')
conn = sqlite3.connect(DB_PATH)

# Verificar si hay partidos
count = conn.execute('SELECT COUNT(*) FROM partidos').fetchone()[0]
if count == 0 and Path('data/partidos.csv').exists():
    with open('data/partidos.csv', 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            fase = row['fase'].strip()
            fecha = row['fecha'].strip()
            local = row['equipo_local'].strip()
            visitante = row['equipo_visitante'].strip()
            
            # Crear equipos si no existen
            local_id = conn.execute('SELECT id FROM equipos WHERE nombre = ?', (local,)).fetchone()
            if not local_id:
                cur = conn.execute('INSERT INTO equipos (nombre) VALUES (?)', (local,))
                local_id = cur.lastrowid
            else:
                local_id = local_id[0]
                
            visitante_id = conn.execute('SELECT id FROM equipos WHERE nombre = ?', (visitante,)).fetchone()
            if not visitante_id:
                cur = conn.execute('INSERT INTO equipos (nombre) VALUES (?)', (visitante,))
                visitante_id = cur.lastrowid
            else:
                visitante_id = visitante_id[0]
            
            conn.execute('INSERT OR IGNORE INTO partidos (fase, fecha, equipo_local_id, equipo_visitante_id) VALUES (?, ?, ?, ?)',
                        (fase, fecha, local_id, visitante_id))
    conn.commit()
    print(f'Partidos cargados desde CSV')
else:
    print(f'Ya existen {count} partidos, saltando seed')

conn.close()
" 2>/dev/null || true

# Verificar PORT
PORT=\${PORT:-5000}
echo "Starting gunicorn on port \$PORT"
exec gunicorn app:app --bind "0.0.0.0:\$PORT" --workers 2 --timeout 120

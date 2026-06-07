#!/bin/bash
cd /app
export FLASK_APP=app.py
mkdir -p data/img

# Descargar banderas
python3 -c "
import sqlite3, urllib.request
from pathlib import Path
db = sqlite3.connect('data/mundial.db')
rows = db.execute('SELECT bandera_url FROM equipos WHERE bandera_url IS NOT NULL').fetchall()
for (url,) in rows:
    try:
        codigo = url.split('/w40/')[1].replace('.png', '')
        path = Path(f'data/img/{codigo}.png')
        if not path.exists():
            urllib.request.urlretrieve(url, str(path))
    except: pass
db.close()
print('Banderas OK')
"

mkdir -p data
flask init-db 2>/dev/null
python3 migrate.py 2>/dev/null
python3 create_admin.py
python3 seed.py 2>/dev/null

# Usar PORT de Railway o 5000 por defecto
PORT=\${PORT:-5000}
echo "Starting on port \$PORT"
gunicorn app:app --bind 0.0.0.0:\$PORT --workers 2

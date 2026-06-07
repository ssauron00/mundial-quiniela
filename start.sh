#!/bin/bash
set -e

cd /app
export FLASK_APP=app.py

# Inicializar
mkdir -p data
flask init-db 2>/dev/null || true
python3 migrate.py 2>/dev/null || true
python3 create_admin.py
python3 seed.py 2>/dev/null || true

# Verificar PORT
if [ -z "$PORT" ]; then
    echo "WARNING: PORT not set, using 5000"
    PORT=5000
fi

echo "Starting gunicorn on port $PORT"
exec gunicorn app:app --bind "0.0.0.0:$PORT" --workers 2 --timeout 120

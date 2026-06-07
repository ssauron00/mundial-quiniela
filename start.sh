#!/bin/bash
cd /app
export FLASK_APP=app.py
mkdir -p data
flask init-db 2>/dev/null
python3 migrate.py 2>/dev/null
python3 create_admin.py
python3 seed.py 2>/dev/null
gunicorn app:app --bind 0.0.0.0:$PORT --workers 2

#!/bin/bash
# start_all.sh - Mundial Quiniela
# Inicializa BD (solo si no existe), migra, crea admin, carga seed (solo si no hay partidos) y levanta Flask

PROJECT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$PROJECT_DIR"

echo "=== Mundial Quiniela - Start All ==="

# Crear directorio data si no existe
mkdir -p data

export FLASK_APP=app.py

# Matar proceso existente en el puerto 5000
PID=$(lsof -ti:5000 2>/dev/null)
if [ -n "$PID" ]; then
    echo "Proceso existente en puerto 5000 (PID: $PID), deteniendo..."
    kill $PID 2>/dev/null
    sleep 1
    # Forzar si no respondió
    kill -9 $PID 2>/dev/null
    sleep 1
fi

# Inicializar BD solo si no existe
if [ ! -f data/mundial.db ]; then
    echo "[1/4] Inicializando base de datos (primera vez)..."
    flask init-db
else
    echo "[1/4] Base de datos ya existe, saltando inicialización."
fi

# Ejecutar migraciones (agrega columnas nuevas si faltan)
echo "[2/4] Ejecutando migraciones..."
python3 migrate.py

# Crear/reset admin
echo "[3/4] Verificando admin (admin@example.com / admin123)..."
python3 create_admin.py

# Cargar seed solo si no hay partidos
PARTIDOS=$(sqlite3 data/mundial.db "SELECT COUNT(*) FROM partidos;" 2>/dev/null || echo "0")
if [ "$PARTIDOS" -eq "0" ]; then
    echo "[4/4] Cargando partidos desde CSV..."
    python3 seed.py
else
    echo "[4/4] Ya existen $PARTIDOS partidos, saltando seed."
fi

# Levantar Flask
echo ""
echo "=== Iniciando Flask en http://127.0.0.1:5000 ==="
flask run --host=0.0.0.0 --port=5000

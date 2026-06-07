#!/bin/bash
# deploy.sh - Script de despliegue para Mundial Quiniela
# Ejecutar en la VM de Oracle Cloud como ubuntu

set -e

APP_DIR="/home/ubuntu/mundial"
SERVICE_NAME="mundial"

echo "=== Mundial Quiniela - Deploy ==="

# 1. Actualizar sistema
echo "[1/7] Actualizando sistema..."
sudo apt update && sudo apt upgrade -y

# 2. Instalar dependencias del sistema
echo "[2/7] Instalando dependencias..."
sudo apt install -y python3 python3-pip python3-venv nginx sqlite3

# 3. Crear entorno virtual
echo "[3/7] Creando entorno virtual..."
cd "$APP_DIR"
python3 -m venv venv
source venv/bin/activate

# 4. Instalar dependencias de Python
echo "[4/7] Instalando dependencias de Python..."
pip install --upgrade pip
pip install -r requirements.txt

# 5. Inicializar BD
echo "[5/7] Inicializando base de datos..."
mkdir -p data
export FLASK_APP=app.py
flask init-db
python3 migrate.py
python3 create_admin.py
python3 seed.py

# 6. Configurar systemd
echo "[6/7] Configurando servicio..."
sudo tee /etc/systemd/system/${SERVICE_NAME}.service > /dev/null << EOF
[Unit]
Description=Mundial Quiniela
After=network.target

[Service]
User=ubuntu
WorkingDirectory=${APP_DIR}
Environment="PATH=${APP_DIR}/venv/bin"
ExecStart=${APP_DIR}/venv/bin/gunicorn --workers 2 --bind 127.0.0.1:5000 app:app
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable ${SERVICE_NAME}
sudo systemctl start ${SERVICE_NAME}

# 7. Configurar Nginx
echo "[7/7] Configurando Nginx..."
sudo tee /etc/nginx/sites-available/${SERVICE_NAME} > /dev/null << EOF
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }

    location /static {
        alias ${APP_DIR}/static;
        expires 7d;
    }
}
EOF

sudo ln -sf /etc/nginx/sites-available/${SERVICE_NAME} /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl restart nginx

echo ""
echo "=== Deploy completado ==="
echo "La app debería estar corriendo en: http://$(curl -s ifconfig.me)"
echo ""
echo "Comandos útiles:"
echo "  Ver logs:        sudo journalctl -u ${SERVICE_NAME} -f"
echo "  Reiniciar:       sudo systemctl restart ${SERVICE_NAME}"
echo "  Ver estado:      sudo systemctl status ${SERVICE_NAME}"
echo "  Reiniciar Nginx: sudo systemctl restart nginx"

#!/usr/bin/env python3
"""Migration: agrega tablas/columnas nuevas si no existen."""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "mundial.db"

def migrate():
    if not DB_PATH.exists():
        print("No existe BD, no hay nada que migrar.")
        return

    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row

    # 1. Agregar columna finalizada a quinielas
    cols = db.execute("PRAGMA table_info(quinielas)").fetchall()
    col_names = [c["name"] for c in cols]

    if "finalizada" not in col_names:
        db.execute("ALTER TABLE quinielas ADD COLUMN finalizada BOOLEAN NOT NULL DEFAULT 0")
        print("Columna 'finalizada' agregada a quinielas.")
    else:
        print("Columna 'finalizada' ya existe.")

    if "finalizada_en" not in col_names:
        db.execute("ALTER TABLE quinielas ADD COLUMN finalizada_en DATETIME")
        print("Columna 'finalizada_en' agregada a quinielas.")
    else:
        print("Columna 'finalizada_en' ya existe.")

    # 2. Crear tabla settings si no existe
    tables = db.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
    table_names = [t["name"] for t in tables]

    if "settings" not in table_names:
        db.execute("""
            CREATE TABLE settings (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL DEFAULT '',
                updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        db.execute("INSERT INTO settings (key, value) VALUES ('quinielas_activas', '1')")
        print("Tabla 'settings' creada con quinielas_activas=1.")
    else:
        print("Tabla 'settings' ya existe.")

    # 3. Agregar opción de menú Configuración si no existe
    existing = db.execute("SELECT id FROM menu_opciones WHERE ruta = '/admin/settings'").fetchone()
    if not existing:
        grupo = db.execute("SELECT id FROM menu_grupos WHERE nombre = 'Admin'").fetchone()
        if grupo:
            db.execute(
                "INSERT INTO menu_opciones (nombre, ruta, grupo_id, orden) VALUES (?, ?, ?, ?)",
                ('Configuración', '/admin/settings', grupo['id'], 2)
            )
            # Agregar permiso para admin
            opcion_id = db.execute("SELECT id FROM menu_opciones WHERE ruta = '/admin/settings'").fetchone()['id']
            db.execute("INSERT OR IGNORE INTO rol_menu_permisos (rol, opcion_id) VALUES ('admin', ?)", (opcion_id,))
            print("Opción de menú 'Configuración' agregada.")
        else:
            print("Grupo 'Admin' no encontrado, saltando menú.")
    else:
        print("Opción de menú 'Configuración' ya existe.")

    db.commit()
    db.close()
    print("\nMigración completada.")

if __name__ == "__main__":
    migrate()

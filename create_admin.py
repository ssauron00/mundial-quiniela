#!/usr/bin/env python3
"""Create or reset admin user. Usage: python3 create_admin.py [email] [password] [nombre]"""
import sys
from pathlib import Path
from werkzeug.security import generate_password_hash
import sqlite3

DB_PATH = Path(__file__).parent / "data" / "mundial.db"

def create_admin(email="admin@example.com", password="admin123", nombre="Administrador"):
    DB_PATH.parent.mkdir(exist_ok=True)
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")

    password_hash = generate_password_hash(password)

    # Check if user exists
    existing = db.execute("SELECT id FROM usuarios WHERE email = ?", (email,)).fetchone()
    if existing:
        db.execute("UPDATE usuarios SET password_hash=?, nombre=?, rol='admin' WHERE email=?",
                   (password_hash, nombre, email))
        db.commit()
        print(f"Admin actualizado: {email} / {password}")
    else:
        cur = db.execute(
            "INSERT INTO usuarios (email, password_hash, nombre, rol) VALUES (?, ?, ?, 'admin')",
            (email, password_hash, nombre)
        )
        db.execute("INSERT INTO quinielas (usuario_id) VALUES (?)", (cur.lastrowid,))
        db.commit()
        print(f"Admin creado: {email} / {password}")

    db.close()

if __name__ == "__main__":
    email = sys.argv[1] if len(sys.argv) > 1 else "admin@example.com"
    password = sys.argv[2] if len(sys.argv) > 2 else "admin123"
    nombre = sys.argv[3] if len(sys.argv) > 3 else "Administrador"
    create_admin(email, password, nombre)

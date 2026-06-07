#!/usr/bin/env python3
"""Create or reset admin user with quiniela."""
import sqlite3
from pathlib import Path
from werkzeug.security import generate_password_hash
import sys

DB_PATH = Path('/tmp/mundial.db')
if not DB_PATH.exists():
    DB_PATH = Path('data/mundial.db')

if not DB_PATH.exists():
    print("ERROR: Database not found")
    sys.exit(1)

print(f"Using database: {DB_PATH}")

conn = sqlite3.connect(DB_PATH)

# Check if admin exists
existing = conn.execute('SELECT id, nombre, rol FROM usuarios WHERE email = ?', ('admin@example.com',)).fetchone()

pw_hash = generate_password_hash('admin123')

if existing:
    # Update password
    conn.execute('UPDATE usuarios SET password_hash=?, nombre=?, rol=? WHERE email=?',
                 (pw_hash, 'Administrador', 'admin', 'admin@example.com'))
    conn.commit()
    user_id = existing[0]
    print("Admin password reset")
else:
    # Create new admin
    cur = conn.execute('INSERT INTO usuarios (email, password_hash, nombre, rol) VALUES (?, ?, ?, ?)',
                       ('admin@example.com', pw_hash, 'Administrador', 'admin'))
    user_id = cur.lastrowid
    conn.commit()
    print(f"Admin created with ID: {user_id}")

# Create quiniela for admin if not exists
existing_quiniela = conn.execute('SELECT id FROM quinielas WHERE usuario_id = ?', (user_id,)).fetchone()
if not existing_quiniela:
    conn.execute('INSERT INTO quinielas (usuario_id) VALUES (?)', (user_id,))
    conn.commit()
    print("Quiniela created for admin")
else:
    print("Quiniela already exists for admin")

# Create settings if not exists
existing_settings = conn.execute('SELECT key FROM settings WHERE key = ?', ('quinielas_activas',)).fetchone()
if not existing_settings:
    conn.execute('INSERT INTO settings (key, value) VALUES (?, ?)', ('quinielas_activas', '1'))
    conn.commit()
    print("Settings created")

# Verify
user = conn.execute('SELECT id, email, nombre, rol FROM usuarios WHERE email = ?', ('admin@example.com',)).fetchone()
total_users = conn.execute('SELECT COUNT(*) FROM usuarios').fetchone()[0]
quinielas = conn.execute('SELECT COUNT(*) FROM quinielas').fetchone()[0]
partidos = conn.execute('SELECT COUNT(*) FROM partidos').fetchone()[0]

print(f"\n=== STATUS ===")
print(f"Admin: {user[1]} (ID: {user[0]})")
print(f"Total users: {total_users}")
print(f"Total quinielas: {quinielas}")
print(f"Total partidos: {partidos}")

conn.close()

print("\n=== LOGIN ===")
print("Email: admin@example.com")
print("Password: admin123")

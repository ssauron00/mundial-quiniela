#!/usr/bin/env python3
"""Create or reset admin user."""
import sqlite3
from pathlib import Path
from werkzeug.security import generate_password_hash
import sys

DB_PATH = Path('/tmp/mundial.db')

# Also check local path
if not DB_PATH.exists():
    DB_PATH = Path('data/mundial.db')

if not DB_PATH.exists():
    print("ERROR: Database not found")
    print(f"  Checked: /tmp/mundial.db")
    print(f"  Checked: data/mundial.db")
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
    print("=" * 50)
    print("PASSWORD RESET SUCCESSFULLY")
    print("=" * 50)
else:
    # Create new admin
    conn.execute('INSERT INTO usuarios (email, password_hash, nombre, rol) VALUES (?, ?, ?, ?)',
                 ('admin@example.com', pw_hash, 'Administrador', 'admin'))
    conn.commit()
    print("=" * 50)
    print("ADMIN CREATED SUCCESSFULLY")
    print("=" * 50)

# Create settings if not exists
existing_settings = conn.execute('SELECT key FROM settings WHERE key = ?', ('quinielas_activas',)).fetchone()
if not existing_settings:
    conn.execute('INSERT INTO settings (key, value) VALUES (?, ?)', ('quinielas_activas', '1'))
    conn.commit()
    print("Settings created")

# Verify
user = conn.execute('SELECT id, email, nombre, rol FROM usuarios WHERE email = ?', ('admin@example.com',)).fetchone()
print(f"\nUser details:")
print(f"  ID: {user[0]}")
print(f"  Email: {user[1]}")
print(f"  Name: {user[2]}")
print(f"  Role: {user[3]}")

# Count users and tables
total_users = conn.execute('SELECT COUNT(*) FROM usuarios').fetchone()[0]
tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
print(f"\nTotal users: {total_users}")
print(f"Tables: {[t[0] for t in tables]}")

conn.close()

print("\n" + "=" * 50)
print("LOGIN CREDENTIALS:")
print("  Email: admin@example.com")
print("  Password: admin123")
print("=" * 50)

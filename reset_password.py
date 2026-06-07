#!/usr/bin/env python3
"""Reset admin password. Usage: python3 reset_password.py [email] [new_password]"""
import sys
from pathlib import Path
from werkzeug.security import generate_password_hash

DB_PATH = Path('/tmp/mundial.db')

if not DB_PATH.exists():
    # Try local path
    DB_PATH = Path('data/mundial.db')

if not DB_PATH.exists():
    print(f"Database not found")
    sys.exit(1)

import sqlite3
conn = sqlite3.connect(DB_PATH)

email = sys.argv[1] if len(sys.argv) > 1 else 'admin@example.com'
password = sys.argv[2] if len(sys.argv) > 2 else 'admin123'

pw_hash = generate_password_hash(password)
conn.execute("UPDATE usuarios SET password_hash=? WHERE email=?", (pw_hash, email))
conn.commit()

# Verify
user = conn.execute("SELECT * FROM usuarios WHERE email=?", (email,)).fetchone()
if user:
    print(f"Password reset for {email}")
else:
    print(f"User {email} not found")

conn.close()

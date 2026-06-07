#!/usr/bin/env python3
"""Fix column name in selecciones table."""
import sqlite3
from pathlib import Path

DB_PATH = Path('/tmp/mundial.db')
if not DB_PATH.exists():
    DB_PATH = Path('data/mundial.db')

print(f"Database: {DB_PATH}")
conn = sqlite3.connect(DB_PATH)

# Check columns
cursor = conn.execute("PRAGMA table_info(selecciones)")
columns = [(row[1], row[2]) for row in cursor.fetchall()]
print(f"Columns in selecciones: {columns}")

has_old = any(c[0] == 'elección' for c in columns)
has_new = any(c[0] == 'eleccion' for c in columns)

if has_old and not has_new:
    print("Renaming 'elección' to 'eleccion'...")
    conn.execute('ALTER TABLE selecciones RENAME COLUMN "elección" TO eleccion')
    conn.commit()
    print("Done!")
elif has_new:
    print("Column 'eleccion' already exists")
else:
    print("Adding column 'eleccion'...")
    conn.execute("ALTER TABLE selecciones ADD COLUMN eleccion TEXT")
    conn.commit()
    print("Done!")

# Verify
cursor = conn.execute("PRAGMA table_info(selecciones)")
columns = [(row[1], row[2]) for row in cursor.fetchall()]
print(f"Final columns: {columns}")

# Test insert
print("\nTesting insert...")
try:
    # Get first partido and quiniela
    partido = conn.execute('SELECT id FROM partidos LIMIT 1').fetchone()
    quiniela = conn.execute('SELECT id FROM quinielas LIMIT 1').fetchone()
    
    if partido and quiniela:
        # Delete test data first
        conn.execute('DELETE FROM selecciones WHERE quiniela_id = ? AND partido_id = ?', 
                     (quiniela[0], partido[0]))
        
        conn.execute('INSERT INTO selecciones (quiniela_id, partido_id, eleccion) VALUES (?, ?, ?)',
                     (quiniela[0], partido[0], '1'))
        conn.commit()
        print("[OK] Insert test passed")
        
        # Verify
        row = conn.execute('SELECT eleccion FROM selecciones WHERE quiniela_id = ? AND partido_id = ?',
                          (quiniela[0], partido[0])).fetchone()
        print(f"[OK] Read back: {row[0]}")
        
        # Clean up
        conn.execute('DELETE FROM selecciones WHERE quiniela_id = ? AND partido_id = ?', 
                     (quiniela[0], partido[0]))
        conn.commit()
    else:
        print("[SKIP] No partidos or quinielas to test")
        
except Exception as e:
    print(f"[ERROR] {e}")

conn.close()
print("\nDone!")

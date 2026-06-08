#!/usr/bin/env python3
"""Restore database from JSON backup file."""
import sqlite3
import json
from pathlib import Path
import sys

if len(sys.argv) < 2:
    print("Usage: python3 restore.py <backup_file.json>")
    exit(1)

backup_file = sys.argv[1]
if not Path(backup_file).exists():
    print(f"ERROR: File not found: {backup_file}")
    exit(1)

DB_PATH = Path('/tmp/mundial.db')
if not DB_PATH.exists():
    DB_PATH = Path('data/mundial.db')

print(f"Restoring to: {DB_PATH}")
print(f"From backup: {backup_file}")

with open(backup_file, 'r', encoding='utf-8') as f:
    backup = json.load(f)

print(f"Backup from: {backup.get('timestamp', 'unknown')}")

conn = sqlite3.connect(DB_PATH)
conn.execute("PRAGMA foreign_keys = ON")

# Restore each table
for table_name, rows in backup['tables'].items():
    if not rows:
        print(f"  {table_name}: 0 rows (skipped)")
        continue
    
    # Get columns from first row
    columns = list(rows[0].keys())
    placeholders = ', '.join(['?' for _ in columns])
    col_names = ', '.join(columns)
    
    # Insert rows
    inserted = 0
    for row in rows:
        values = [row.get(col) for col in columns]
        try:
            conn.execute(f"INSERT OR IGNORE INTO {table_name} ({col_names}) VALUES ({placeholders})", values)
            inserted += 1
        except Exception as e:
            print(f"    ERROR in {table_name}: {e}")
    
    conn.commit()
    print(f"  {table_name}: {inserted}/{len(rows)} rows restored")

conn.close()
print("\nRestore completed!")

#!/usr/bin/env python3
"""Backup database to JSON file."""
import sqlite3
import json
from pathlib import Path
from datetime import datetime

DB_PATH = Path('/tmp/mundial.db')
if not DB_PATH.exists():
    DB_PATH = Path('data/mundial.db')

if not DB_PATH.exists():
    print("ERROR: Database not found")
    exit(1)

print(f"Backing up: {DB_PATH}")
conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

backup = {
    'timestamp': datetime.now().isoformat(),
    'tables': {}
}

# Get all tables
tables = conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
print(f"Tables found: {[t[0] for t in tables]}")

for table in tables:
    table_name = table[0]
    rows = conn.execute(f"SELECT * FROM {table_name}").fetchall()
    backup['tables'][table_name] = [dict(row) for row in rows]
    print(f"  {table_name}: {len(rows)} rows")

conn.close()

# Save to file
backup_file = f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
with open(backup_file, 'w', encoding='utf-8') as f:
    json.dump(backup, f, indent=2, ensure_ascii=False, default=str)

print(f"\nBackup saved to: {backup_file}")
print(f"Total tables: {len(backup['tables'])}")

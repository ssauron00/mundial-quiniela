#!/usr/bin/env python3
"""Seed partidos from CSV. Safe to run multiple times - skips duplicates."""
import csv
import sqlite3
from pathlib import Path

# Use /tmp for Railway, data/ for local
DB_PATH = Path('/tmp/mundial.db')
if not DB_PATH.exists():
    DB_PATH = Path('data/mundial.db')

if not DB_PATH.exists():
    print("Database not found, skipping seed")
    exit(0)

conn = sqlite3.connect(DB_PATH)
conn.execute("PRAGMA foreign_keys = ON")

CSV_PATH = Path('data/partidos.csv')
if not CSV_PATH.exists():
    print("CSV file not found, skipping seed")
    conn.close()
    exit(0)

inserted = 0
skipped = 0

with open(CSV_PATH, newline='', encoding='utf-8') as f:
    reader = csv.DictReader(f)
    for row in reader:
        fase = row['fase'].strip()
        fecha = row['fecha'].strip()
        local_nombre = row['equipo_local'].strip()
        visitante_nombre = row['equipo_visitante'].strip()

        # Get or create local equipo
        local_row = conn.execute('SELECT id FROM equipos WHERE nombre = ?', (local_nombre,)).fetchone()
        if local_row:
            local_id = local_row[0]
        else:
            cur = conn.execute('INSERT INTO equipos (nombre) VALUES (?)', (local_nombre,))
            local_id = cur.lastrowid

        # Get or create visitante equipo
        visitante_row = conn.execute('SELECT id FROM equipos WHERE nombre = ?', (visitante_nombre,)).fetchone()
        if visitante_row:
            visitante_id = visitante_row[0]
        else:
            cur = conn.execute('INSERT INTO equipos (nombre) VALUES (?)', (visitante_nombre,))
            visitante_id = cur.lastrowid

        # Check if partido already exists
        existing = conn.execute(
            'SELECT id FROM partidos WHERE fecha = ? AND equipo_local_id = ? AND equipo_visitante_id = ?',
            (fecha, local_id, visitante_id)
        ).fetchone()

        if existing:
            skipped += 1
        else:
            conn.execute(
                'INSERT INTO partidos (fase, fecha, equipo_local_id, equipo_visitante_id) VALUES (?, ?, ?, ?)',
                (fase, fecha, local_id, visitante_id)
            )
            inserted += 1

conn.commit()
print(f"Seed completed: {inserted} inserted, {skipped} skipped")
conn.close()

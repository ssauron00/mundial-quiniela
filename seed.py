import csv
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / 'data' / 'mundial.db'
CSV_PATH = Path(__file__).parent / 'data' / 'partidos.csv'

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def ensure_equipo(conn, nombre):
    cur = conn.execute("SELECT id FROM equipos WHERE nombre = ?", (nombre,))
    row = cur.fetchone()
    if row:
        return row['id']
    cur = conn.execute("INSERT INTO equipos (nombre) VALUES (?)", (nombre,))
    conn.commit()
    return cur.lastrowid

def main():
    if not CSV_PATH.exists():
        print(f"CSV file not found: {CSV_PATH}")
        return
    conn = get_db()
    with open(CSV_PATH, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            fase = row['fase'].strip()
            fecha = row['fecha'].strip()
            local_nombre = row['equipo_local'].strip()
            visitante_nombre = row['equipo_visitante'].strip()
            local_id = ensure_equipo(conn, local_nombre)
            visitante_id = ensure_equipo(conn, visitante_nombre)
            # Insert partido if not exists (optional: check duplicate)
            cur = conn.execute(
                "SELECT id FROM partidos WHERE fecha = ? AND equipo_local_id = ? AND equipo_visitante_id = ?",
                (fecha, local_id, visitante_id)
            )
            if cur.fetchone():
                print(f"Partido ya existe: {local_nombre} vs {visitante_nombre} en {fecha}")
                continue
            conn.execute(
                "INSERT INTO partidos (fase, fecha, equipo_local_id, equipo_visitante_id) VALUES (?, ?, ?, ?)",
                (fase, fecha, local_id, visitante_id)
            )
            print(f"Insertado: {local_nombre} vs {visitante_nombre} ({fase})")
    conn.commit()
    conn.close()
    print("Seed completed.")

if __name__ == '__main__':
    main()
#!/usr/bin/env python3
"""Debug: verificar que las selecciones se cargan correctamente."""
import sqlite3
from pathlib import Path

DB_PATH = Path('/tmp/mundial.db')
if not DB_PATH.exists():
    DB_PATH = Path('data/mundial.db')

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row

print("=== DEBUG QUINIELA ===\n")

# 1. Verificar usuario admin
admin = conn.execute('SELECT id, email FROM usuarios WHERE email = ?', ('admin@example.com',)).fetchone()
print(f"1. Admin: {dict(admin) if admin else 'NO EXISTE'}")

if admin:
    # 2. Verificar quiniela del admin
    quiniela = conn.execute('SELECT * FROM quinielas WHERE usuario_id = ?', (admin['id'],)).fetchone()
    print(f"2. Quiniela: {dict(quiniela) if quiniela else 'NO EXISTE'}")
    
    if quiniela:
        quiniela_id = quiniela['id']
        
        # 3. Verificar selecciones del admin
        selecciones = conn.execute('SELECT * FROM selecciones WHERE quiniela_id = ?', (quiniela_id,)).fetchall()
        print(f"3. Selecciones del admin: {len(selecciones)}")
        for s in selecciones:
            print(f"   - partido_id={s['partido_id']}, eleccion={s['eleccion']}")
        
        # 4. Verificar partidos
        partidos = conn.execute('SELECT id, fase FROM partidos LIMIT 5').fetchall()
        print(f"\n4. Partidos (primeros 5): {len(partidos)}")
        for p in partidos:
            print(f"   - ID={p['id']}, fase={p['fase']}")
        
        # 5. Simular la query de quiniela_hacer
        print(f"\n5. Simulando query de quiniela_hacer (quiniela_id={quiniela_id})...")
        resultados = conn.execute('''
            SELECT p.id, p.fase, p.fecha,
                   el.nombre AS local,
                   el.bandera_url AS bandera_local,
                   ev.nombre AS visitante,
                   ev.bandera_url AS bandera_visitante,
                   s.eleccion AS eleccion
            FROM partidos p
            JOIN equipos el ON p.equipo_local_id = el.id
            JOIN equipos ev ON p.equipo_visitante_id = ev.id
            LEFT JOIN selecciones s ON s.partido_id = p.id AND s.quiniela_id = ?
            ORDER BY p.fecha
        ''', (quiniela_id,)).fetchall()
        
        print(f"   Resultados: {len(resultados)}")
        for r in resultados[:5]:
            print(f"   - Partido {r['id']}: {r['local']} vs {r['visitante']}, eleccion={r['eleccion']}")
        
        # 6. Verificar columna eleccion
        print("\n6. Verificando columna 'eleccion' en selecciones...")
        cursor = conn.execute("PRAGMA table_info(selecciones)")
        for row in cursor.fetchall():
            print(f"   - {row[1]} ({row[2]})")

conn.close()
print("\n=== FIN DEBUG ===")

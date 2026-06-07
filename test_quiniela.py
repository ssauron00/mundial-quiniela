#!/usr/bin/env python3
"""Test completo de quiniela: crear usuario, seleccionar, guardar, verificar."""
import sqlite3
from pathlib import Path
from werkzeug.security import generate_password_hash

DB_PATH = Path('/tmp/mundial.db')
if not DB_PATH.exists():
    DB_PATH = Path('data/mundial.db')

print(f"Database: {DB_PATH}")
conn = sqlite3.connect(DB_PATH)

# 1. Limpiar datos de prueba previos
conn.execute("DELETE FROM selecciones WHERE quiniela_id IN (SELECT id FROM quinielas WHERE usuario_id IN (SELECT id FROM usuarios WHERE email = 'test@test.com'))")
conn.execute("DELETE FROM quinielas WHERE usuario_id IN (SELECT id FROM usuarios WHERE email = 'test@test.com')")
conn.execute("DELETE FROM usuarios WHERE email = 'test@test.com'")
conn.commit()

# 2. Crear usuario de prueba
pw_hash = generate_password_hash('test123')
cur = conn.execute('INSERT INTO usuarios (email, password_hash, nombre, rol) VALUES (?, ?, ?, ?)',
                   ('test@test.com', pw_hash, 'Usuario Test', 'usuario'))
test_user_id = cur.lastrowid
conn.commit()
print(f"[OK] Usuario creado: ID={test_user_id}")

# 3. Crear quiniela para el usuario
cur = conn.execute('INSERT INTO quinielas (usuario_id) VALUES (?)', (test_user_id,))
test_quiniela_id = cur.lastrowid
conn.commit()
print(f"[OK] Quiniela creada: ID={test_quiniela_id}")

# 4. Verificar que hay partidos
partidos = conn.execute('SELECT id, fase FROM equipos LIMIT 5').fetchall()
print(f"[INFO] Equipos disponibles: {len(partidos)}")
for p in partidos:
    print(f"  - {p[1]}")

# Obtener partidos reales
partidos = conn.execute('SELECT id, fase, equipo_local_id, equipo_visitante_id FROM partidos LIMIT 3').fetchall()
print(f"[INFO] Partidos disponibles: {len(partidos)}")
for p in partidos:
    local = conn.execute('SELECT nombre FROM equipos WHERE id = ?', (p[2],)).fetchone()[0]
    visitante = conn.execute('SELECT nombre FROM equipos WHERE id = ?', (p[3],)).fetchone()[0]
    print(f"  ID={p[0]}: {local} vs {visitante}")

if len(partidos) < 3:
    print("[ERROR] No hay suficientes partidos para la prueba")
    conn.close()
    exit(1)

# 5. Simular guardar quiniela (insertar selecciones)
print("\n[TEST] Guardando selecciones...")
for i, p in enumerate(partidos[:3]):
    eleccion = ['1', 'X', '2'][i]
    try:
        conn.execute('INSERT INTO selecciones (quiniela_id, partido_id, eleccion) VALUES (?, ?, ?)',
                     (test_quiniela_id, p[0], eleccion))
        print(f"  [OK] Partido {p[0]}: {eleccion}")
    except Exception as e:
        print(f"  [ERROR] Partido {p[0]}: {e}")
conn.commit()

# 6. Verificar que se guardaron
print("\n[TEST] Verificando selecciones guardadas...")
selecciones = conn.execute('''
    SELECT s.id, s.eleccion, p.fase, 
           el.nombre as local, ev.nombre as visitante
    FROM selecciones s
    JOIN partidos p ON s.partido_id = p.id
    JOIN equipos el ON p.equipo_local_id = el.id
    JOIN equipos ev ON p.equipo_visitante_id = ev.id
    WHERE s.quiniela_id = ?
''', (test_quiniela_id,)).fetchall()

print(f"  Selecciones guardadas: {len(selecciones)}")
for s in selecciones:
    print(f"  - {s[3]} vs {s[4]}: {s[1]}")

if len(selecciones) == 3:
    print("\n[PASS] Guardar quiniela funciona correctamente!")
else:
    print(f"\n[FAIL] Se esperaban 3 selecciones, se encontraron {len(selecciones)}")

# 7. Verificar estado de la quiniela
quiniela = conn.execute('SELECT * FROM quinielas WHERE id = ?', (test_quiniela_id,)).fetchone()
print(f"\n[TEST] Estado quiniela: finalizada={ quiniela['finalizada']}")

# 8. Limpiar datos de prueba
conn.execute('DELETE FROM selecciones WHERE quiniela_id = ?', (test_quiniela_id,))
conn.execute('DELETE FROM quinielas WHERE id = ?', (test_quiniela_id,))
conn.execute('DELETE FROM usuarios WHERE id = ?', (test_user_id,))
conn.commit()
print("\n[OK] Datos de prueba limpiados")

conn.close()

# 9. Verificar estructura de tablas
print("\n[TEST] Estructura de tablas...")
conn2 = sqlite3.connect(DB_PATH)
cursor = conn2.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [row[0] for row in cursor.fetchall()]
print(f"  Tablas: {tables}")

# Verificar columna eleccion en selecciones
cursor = conn2.execute("PRAGMA table_info(selecciones)")
cols = [(row[1], row[2]) for row in cursor.fetchall()]
print(f"  Columnas en selecciones: {cols}")

# Verificar columna eleccion específicamente
has_eleccion = any(col[0] == 'eleccion' for col in cols)
has_eleccion_acento = any(col[0] == 'elección' for col in cols)
print(f"  Tiene 'eleccion' (sin acento): {has_eleccion}")
print(f"  Tiene 'elección' (con acento): {has_eleccion_acento}")

if not has_eleccion:
    print("\n[WARNING] La tabla no tiene columna 'eleccion'. Intentando agregar...")
    try:
        conn2.execute("ALTER TABLE selecciones ADD COLUMN eleccion TEXT")
        print("  [OK] Columna 'eleccion' agregada")
    except Exception as e:
        print(f"  [ERROR] No se pudo agregar columna: {e}")
    conn2.commit()

conn2.close()

print("\n=== FIN DEL TEST ===")

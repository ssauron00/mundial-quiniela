#!/usr/bin/env python3
"""Test completo de quiniela."""
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

# 3. Crear quiniela
cur = conn.execute('INSERT INTO quinielas (usuario_id) VALUES (?)', (test_user_id,))
test_quiniela_id = cur.lastrowid
conn.commit()
print(f"[OK] Quiniela creada: ID={test_quiniela_id}")

# 4. Verificar partidos disponibles
partidos = conn.execute('SELECT COUNT(*) FROM partidos').fetchone()[0]
print(f"[INFO] Partidos en BD: {partidos}")

if partidos == 0:
    print("[ERROR] No hay partidos. Ejecuta seed.py primero.")
    conn.close()
    exit(1)

# Obtener 3 partidos
partidos = conn.execute('SELECT id, equipo_local_id, equipo_visitante_id, fase FROM partidos LIMIT 3').fetchall()
print(f"[INFO] Usando {len(partidos)} partidos para la prueba:")
for p in partidos:
    local = conn.execute('SELECT nombre FROM equipos WHERE id = ?', (p[1],)).fetchone()[0]
    visitante = conn.execute('SELECT nombre FROM equipos WHERE id = ?', (p[2],)).fetchone()[0]
    print(f"  ID={p[0]}: {local} vs {visitante} ({p[3]})")

# 5. Simular guardar quiniela
print("\n[TEST] Guardando selecciones...")
for i, p in enumerate(partidos):
    eleccion = ['1', 'X', '2'][i]
    try:
        conn.execute('INSERT INTO selecciones (quiniela_id, partido_id, eleccion) VALUES (?, ?, ?)',
                     (test_quiniela_id, p[0], eleccion))
        print(f"  [OK] Partido {p[0]}: {eleccion}")
    except Exception as e:
        print(f"  [ERROR] Partido {p[0]}: {e}")
        import traceback
        traceback.print_exc()
conn.commit()

# 6. Verificar
print("\n[TEST] Verificando selecciones guardadas...")
selecciones = conn.execute('SELECT id, eleccion, partido_id FROM selecciones WHERE quiniela_id = ?', (test_quiniela_id,)).fetchall()
print(f"  Total: {len(selecciones)}")
for s in selecciones:
    print(f"  - Seleccion {s[0]}: partido={s[2]}, eleccion={s[1]}")

if len(selecciones) == len(partidos):
    print("\n[PASS] Guardar quiniela funciona!")
else:
    print(f"\n[FAIL] Esperados {len(partidos)}, encontrados {len(selecciones)}")

# 7. Verificar que hay usuario admin
admin = conn.execute('SELECT id, email FROM usuarios WHERE email = ?', ('admin@example.com',)).fetchone()
if admin:
    admin_quiniela = conn.execute('SELECT id FROM quinielas WHERE usuario_id = ?', (admin[0],)).fetchone()
    print(f"\n[TEST] Admin tiene quiniela: {admin_quiniela is not None}")
    if not admin_quiniela:
        print("  Creando quiniela para admin...")
        conn.execute('INSERT INTO quinielas (usuario_id) VALUES (?)', (admin[0],))
        conn.commit()
        print("  [OK] Quiniela creada")
else:
    print("[WARNING] Admin no existe")

# 8. Limpiar
conn.execute('DELETE FROM selecciones WHERE quiniela_id = ?', (test_quiniela_id,))
conn.execute('DELETE FROM quinielas WHERE id = ?', (test_quiniela_id,))
conn.execute('DELETE FROM usuarios WHERE id = ?', (test_user_id,))
conn.commit()
print("\n[OK] Limpieza completada")

# 9. Resumen
usuarios = conn.execute('SELECT COUNT(*) FROM usuarios').fetchone()[0]
quinielas = conn.execute('SELECT COUNT(*) FROM quinielas').fetchone()[0]
selecciones_total = conn.execute('SELECT COUNT(*) FROM selecciones').fetchone()[0]
partidos_total = conn.execute('SELECT COUNT(*) FROM partidos').fetchone()[0]

print(f"\n=== RESUMEN ===")
print(f"Usuarios: {usuarios}")
print(f"Quinielas: {quinielas}")
print(f"Selecciones: {selecciones_total}")
print(f"Partidos: {partidos_total}")

conn.close()

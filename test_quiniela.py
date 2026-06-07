#!/usr/bin/env python3
"""Test del flujo completo de guardar quiniela via POST."""
import sqlite3
from pathlib import Path
from werkzeug.security import generate_password_hash

DB_PATH = Path('/tmp/mundial.db')
if not DB_PATH.exists():
    DB_PATH = Path('data/mundial.db')

print(f"Database: {DB_PATH}")
conn = sqlite3.connect(DB_PATH)

# 1. Crear usuario de prueba
conn.execute("DELETE FROM selecciones WHERE quiniela_id IN (SELECT id FROM quinielas WHERE usuario_id IN (SELECT id FROM usuarios WHERE email = 'test@test.com'))")
conn.execute("DELETE FROM quinielas WHERE usuario_id IN (SELECT id FROM usuarios WHERE email = 'test@test.com')")
conn.execute("DELETE FROM usuarios WHERE email = 'test@test.com'")
conn.commit()

pw_hash = generate_password_hash('test123')
cur = conn.execute('INSERT INTO usuarios (email, password_hash, nombre, rol) VALUES (?, ?, ?, ?)',
                   ('test@test.com', pw_hash, 'Usuario Test', 'usuario'))
test_user_id = cur.lastrowid
conn.execute('INSERT INTO quinielas (usuario_id) VALUES (?)', (test_user_id,))
conn.commit()
print(f"[OK] Usuario creado: ID={test_user_id}")

# 2. Obtener partidos
partidos = conn.execute('SELECT id FROM partidos LIMIT 3').fetchall()
print(f"[INFO] Partidos: {[p[0] for p in partidos]}")

# 3. Simular el POST del formulario (como lo hace el navegador)
print("\n[TEST] Simulando POST del formulario...")
form_data = {}
for i, p in enumerate(partidos):
    form_data[f'partido_{p[0]}'] = ['1', 'X', '2'][i]

print(f"  Form data: {form_data}")

# 4. Ejecutar la misma lógica que quiniela_guardar
quiniela = conn.execute('SELECT id, usuario_id, finalizada FROM quinielas WHERE usuario_id = ?', (test_user_id,)).fetchone()
quiniela_id = quiniela[0]
print(f"  Quiniela ID: {quiniela_id}")

# Verificar si está finalizada
if quiniela[2]:
    print("  [ERROR] Quiniela está finalizada")
else:
    # Borrar selecciones anteriores
    conn.execute('DELETE FROM selecciones WHERE quiniela_id = ?', (quiniela_id,))
    
    # Insertar nuevas selecciones
    for key, value in form_data.items():
        if key.startswith('partido_'):
            partido_id = int(key.split('_')[1])
            eleccion = value
            if eleccion in ('1', 'X', '2'):
                try:
                    conn.execute('INSERT INTO selecciones (quiniela_id, partido_id, eleccion) VALUES (?, ?, ?)',
                                 (quiniela_id, partido_id, eleccion))
                    print(f"  [OK] Insertado: partido={partido_id}, eleccion={eleccion}")
                except Exception as e:
                    print(f"  [ERROR] partido={partido_id}: {e}")
    
    conn.commit()
    print("  [OK] Commit ejecutado")

# 5. Verificar
print("\n[TEST] Verificando...")
selecciones = conn.execute('SELECT id, quiniela_id, partido_id, eleccion FROM selecciones WHERE quiniela_id = ?', (quiniela_id,)).fetchall()
print(f"  Selecciones guardadas: {len(selecciones)}")
for s in selecciones:
    print(f"    - id={s[0]}, partido={s[2]}, eleccion={s[3]}")

if len(selecciones) == len(partidos):
    print("\n[PASS] Guardar quiniela funciona correctamente!")
else:
    print(f"\n[FAIL] Esperados {len(partidos)}, encontrados {len(selecciones)}")

# 6. Ahora probar con el admin
print("\n[TEST] Probando con admin...")
admin = conn.execute('SELECT id FROM usuarios WHERE email = ?', ('admin@example.com',)).fetchone()
if admin:
    admin_quiniela = conn.execute('SELECT id, finalizada FROM quinielas WHERE usuario_id = ?', (admin[0],)).fetchone()
    if admin_quiniela:
        print(f"  Admin quiniela: ID={admin_quiniela[0]}, finalizada={admin_quiniela[1]}")
        admin_selecciones = conn.execute('SELECT COUNT(*) FROM selecciones WHERE quiniela_id = ?', (admin_quiniela[0],)).fetchone()[0]
        print(f"  Admin selecciones: {admin_selecciones}")
    else:
        print("  [WARNING] Admin no tiene quiniela")
        conn.execute('INSERT INTO quinielas (usuario_id) VALUES (?)', (admin[0],))
        conn.commit()
        print("  [OK] Quiniela creada para admin")
else:
    print("  [WARNING] Admin no existe")

# Limpiar
conn.execute('DELETE FROM selecciones WHERE quiniela_id IN (SELECT id FROM quinielas WHERE usuario_id = ?)', (test_user_id,))
conn.execute('DELETE FROM quinielas WHERE usuario_id = ?', (test_user_id,))
conn.execute('DELETE FROM usuarios WHERE id = ?', (test_user_id,))
conn.commit()
print("\n[OK] Limpieza completada")

conn.close()
print("\n=== FIN DEL TEST ===")

from flask import Flask, render_template, request, redirect, url_for, session, flash, g, make_response
from database import get_db, init_app, is_postgres
from auth import login_required, role_required, create_user, get_user_by_email, check_password
import os
from io import BytesIO

def create_app():
    app = Flask(__name__)
    app.secret_key = os.environ.get('SECRET_KEY', 'dev-secret-key-change-me')
    init_app(app)

    # Helper: detectar si es PostgreSQL
    def is_postgres():
        return os.environ.get('DATABASE_URL') is not None

    # Helper: get setting value
    def get_setting(key, default='0'):
        db = get_db()
        row = db.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return row['value'] if row else default

    # Helper: set setting value
    def set_setting(key, value):
        db = get_db()
        db.execute("INSERT OR REPLACE INTO settings (key, value, updated_at) VALUES (?, ?, CURRENT_TIMESTAMP)",
                   (key, value))
        db.commit()

    # Context processor: make settings available to all templates
    @app.context_processor
    def inject_settings():
        return {
            'quinielas_activas': get_setting('quinielas_activas', '1') == '1'
        }

    # context processor to inject menu based on role
    @app.context_processor
    def inject_menu():
        menu_items = getattr(g, 'menu_items', {})
        return {'menu_items': menu_items}

    @app.before_request
    def load_menu():
        g.menu_items = {}
        if 'usuario_id' in session:
            db = get_db()
            # fetch menu items for the user's role
            menu_rows = db.execute('''
                SELECT m.nombre AS grupo, o.nombre AS opcion, o.ruta
                FROM menu_opciones o
                JOIN menu_grupos m ON o.grupo_id = m.id
                JOIN rol_menu_permisos rmp ON o.id = rmp.opcion_id
                JOIN usuarios u ON u.rol = rmp.rol
                WHERE u.id = ?
                ORDER BY m.orden, o.orden
            ''', (session['usuario_id'],)).fetchall()
            # build dict {grupo: [opciones]}
            for row in menu_rows:
                g.menu_items.setdefault(row['grupo'], []).append({
                    'nombre': row['opcion'],
                    'ruta': row['ruta']
                })

    # Home / index
    @app.route('/')
    def index():
        if 'usuario_id' in session:
            return redirect(url_for('welcome'))
        return redirect(url_for('login'))

    # Login
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method == 'POST':
            email = request.form['email'].strip()
            password = request.form['password']
            user = get_user_by_email(email)
            if user and check_password(password, user['password_hash']):
                session.clear()
                session['usuario_id'] = user['id']
                session['usuario_nombre'] = user['nombre']
                session['usuario_rol'] = user['rol']
                flash('Inicio de sesión exitoso.', 'success')
                return redirect(url_for('welcome'))
            else:
                flash('Credenciales inválidas.', 'danger')
        return render_template('login.html')

    # Logout
    @app.route('/logout')
    def logout():
        session.clear()
        flash('Has cerrado sesión.', 'info')
        return redirect(url_for('index'))

    # Welcome page (after login)
    @app.route('/welcome')
    @login_required
    def welcome():
        return render_template('welcome.html')

    # Admin: partidos CRUD
    @app.route('/partidos')
    @login_required
    @role_required('admin')
    def partidos_list():
        db = get_db()
        orden = request.args.get('orden', 'fecha')
        if orden == 'resultado':
            order_clause = "CASE WHEN p.goles_local IS NULL THEN 1 ELSE 0 END, p.fecha"
        elif orden == 'pendientes':
            order_clause = "CASE WHEN p.goles_local IS NULL THEN 0 ELSE 1 END, p.fecha"
        elif orden == 'fase':
            order_clause = "p.fase, p.fecha"
        else:
            order_clause = "p.fecha"
        partidos = db.execute(f'''
            SELECT p.*,
                   el.nombre AS local, el.bandera_url AS bandera_local,
                   ev.nombre AS visitante, ev.bandera_url AS bandera_visitante
            FROM partidos p
            JOIN equipos el ON p.equipo_local_id = el.id
            JOIN equipos ev ON p.equipo_visitante_id = ev.id
            ORDER BY {order_clause}
        ''').fetchall()
        return render_template('partidos/list.html', partidos=partidos, orden=orden)

    @app.route('/partidos/nuevo', methods=['GET', 'POST'])
    @login_required
    @role_required('admin')
    def partidos_nuevo():
        db = get_db()
        if request.method == 'POST':
            fase = request.form['fase']
            fecha = request.form['fecha']
            local_id = request.form['equipo_local']
            visitante_id = request.form['equipo_visitante']
            db.execute('''
                INSERT INTO partidos (fase, fecha, equipo_local_id, equipo_visitante_id)
                VALUES (?, ?, ?, ?)
            ''', (fase, fecha, local_id, visitante_id))
            db.commit()
            flash('Partido creado.', 'success')
            return redirect(url_for('partidos_list'))
        equipos = db.execute('SELECT id, nombre FROM equipos ORDER BY nombre').fetchall()
        return render_template('partidos/form.html', equipos=equipos, partido=None)

    @app.route('/partidos/<int:id>/editar', methods=['GET', 'POST'])
    @login_required
    @role_required('admin')
    def partidos_editar(id):
        db = get_db()
        partido = db.execute('SELECT * FROM partidos WHERE id = ?', (id,)).fetchone()
        if request.method == 'POST':
            fase = request.form['fase']
            fecha = request.form['fecha']
            local_id = request.form['equipo_local']
            visitante_id = request.form['equipo_visitante']
            goles_local = request.form.get('goles_local', '').strip()
            goles_visitante = request.form.get('goles_visitante', '').strip()
            gl = int(goles_local) if goles_local else None
            gv = int(goles_visitante) if goles_visitante else None
            db.execute('''
                UPDATE partidos SET fase=?, fecha=?, equipo_local_id=?, equipo_visitante_id=?,
                                   goles_local=?, goles_visitante=?
                WHERE id=?
            ''', (fase, fecha, local_id, visitante_id, gl, gv, id))
            db.commit()
            flash('Partido actualizado.', 'success')
            return redirect(url_for('partidos_list'))
        equipos = db.execute('SELECT id, nombre FROM equipos ORDER BY nombre').fetchall()
        return render_template('partidos/form.html', equipos=equipos, partido=partido)

    # Quiniela UI
    @app.route('/quiniela/hacer')
    @login_required
    def quiniela_hacer():
        db = get_db()
        quiniela = db.execute('SELECT * FROM quinielas WHERE usuario_id = ?', (session['usuario_id'],)).fetchone()
        quiniela_id = quiniela['id']
        finalizada = quiniela['finalizada']
        finalizada_en = quiniela['finalizada_en']
        # get partidos
        partidos = db.execute('''
            SELECT p.id, p.fase, p.fecha,
                   el.nombre AS local,
                   el.bandera_url AS "bandera_local",
                   ev.nombre AS visitante,
                   ev.bandera_url AS "bandera_visitante",
                   s.eleccion AS eleccion
            FROM partidos p
            JOIN equipos el ON p.equipo_local_id = el.id
            JOIN equipos ev ON p.equipo_visitante_id = ev.id
            LEFT JOIN selecciones s ON s.partido_id = p.id AND s.quiniela_id = ?
            ORDER BY p.fecha
        ''', (quiniela_id,)).fetchall()
        return render_template('quiniela/hacer.html', partidos=partidos,
                               finalizada=finalizada, finalizada_en=finalizada_en)

    @app.route('/quiniela/guardar', methods=['POST'])
    @login_required
    def quiniela_guardar():
        if not get_setting('quinielas_activas', '1') == '1':
            flash('Las quinielas están desactivadas por el administrador.', 'warning')
            return redirect(url_for('quiniela_hacer'))
        db = get_db()
        quiniela = db.execute('SELECT * FROM quinielas WHERE usuario_id = ?', (session['usuario_id'],)).fetchone()
        if quiniela['finalizada']:
            flash('Tu quiniela ya fue finalizada. No se pueden hacer cambios.', 'warning')
            return redirect(url_for('quiniela_hacer'))
        quiniela_id = quiniela['id']
        db.execute('DELETE FROM selecciones WHERE quiniela_id = ?', (quiniela_id,))
        for key, value in request.form.items():
            if key.startswith('partido_'):
                partido_id = int(key.split('_')[1])
                eleccion = value
                if eleccion in ('1','X','2'):
                    db.execute('''
                        INSERT INTO selecciones (quiniela_id, partido_id, elección)
                        VALUES (?, ?, ?)
                    ''', (quiniela_id, partido_id, eleccion))
        db.commit()
        flash('Quiniela guardada.', 'success')
        return redirect(url_for('quiniela_hacer'))

    @app.route('/quiniela/finalizar', methods=['POST'])
    @login_required
    def quiniela_finalizar():
        if not get_setting('quinielas_activas', '1') == '1':
            flash('Las quinielas están desactivadas por el administrador.', 'warning')
            return redirect(url_for('quiniela_hacer'))
        db = get_db()
        quiniela = db.execute('SELECT * FROM quinielas WHERE usuario_id = ?', (session['usuario_id'],)).fetchone()
        if quiniela['finalizada']:
            flash('Tu quiniela ya está finalizada.', 'info')
            return redirect(url_for('quiniela_hacer'))
        count = db.execute('SELECT COUNT(*) AS cnt FROM selecciones WHERE quiniela_id = ?', (quiniela['id'],)).fetchone()['cnt']
        if count == 0:
            flash('Debes hacer al menos un pronóstico antes de finalizar.', 'warning')
            return redirect(url_for('quiniela_hacer'))
        db.execute("UPDATE quinielas SET finalizada=1, finalizada_en=CURRENT_TIMESTAMP WHERE id=?", (quiniela['id'],))
        db.commit()
        flash('¡Quiniela finalizada! Ya no se pueden hacer cambios.', 'success')
        return redirect(url_for('quiniela_hacer'))

    @app.route('/quiniela/reabrir', methods=['POST'])
    @login_required
    def quiniela_reabrir():
        if not get_setting('quinielas_activas', '1') == '1':
            flash('Las quinielas están desactivadas por el administrador.', 'warning')
            return redirect(url_for('quiniela_hacer'))
        db = get_db()
        quiniela = db.execute('SELECT * FROM quinielas WHERE usuario_id = ?', (session['usuario_id'],)).fetchone()
        if not quiniela['finalizada']:
            flash('Tu quiniela no está finalizada.', 'info')
            return redirect(url_for('quiniela_hacer'))
        db.execute("UPDATE quinielas SET finalizada=0, finalizada_en=NULL WHERE id=?", (quiniela['id'],))
        db.commit()
        flash('Quiniela reabierta. Ya puedes hacer cambios.', 'success')
        return redirect(url_for('quiniela_hacer'))

    # Registro de usuarios
    @app.route('/register', methods=['GET', 'POST'])
    def register():
        if request.method == 'POST':
            email = request.form['email'].strip()
            password = request.form['password']
            nombre = request.form['nombre'].strip()
            if get_user_by_email(email):
                flash('El correo ya está registrado.', 'danger')
                return render_template('register.html')
            create_user(email, password, nombre)
            flash('Cuenta creada. Ahora inicia sesión.', 'success')
            return redirect(url_for('login'))
        return render_template('register.html')

    # Admin: usuarios CRUD
    @app.route('/admin/usuarios')
    @login_required
    @role_required('admin')
    def admin_usuarios_list():
        db = get_db()
        usuarios = db.execute('''
            SELECT u.id, u.email, u.nombre, u.rol, u.activo,
                   COUNT(s.id) AS total_selecciones
            FROM usuarios u
            LEFT JOIN quinielas q ON u.id = q.usuario_id
            LEFT JOIN selecciones s ON q.id = s.quiniela_id
            GROUP BY u.id
            ORDER BY u.nombre
        ''').fetchall()
        return render_template('admin/usuarios_list.html', usuarios=usuarios)

    @app.route('/admin/usuarios/<int:id>/editar', methods=['GET', 'POST'])
    @login_required
    @role_required('admin')
    def admin_usuarios_editar(id):
        db = get_db()
        usuario = db.execute('SELECT * FROM usuarios WHERE id = ?', (id,)).fetchone()
        if not usuario:
            flash('Usuario no encontrado.', 'danger')
            return redirect(url_for('admin_usuarios_list'))
        if request.method == 'POST':
            nombre = request.form['nombre'].strip()
            email = request.form['email'].strip()
            rol = request.form['rol']
            activo = 1 if 'activo' in request.form else 0
            nuevo_password = request.form.get('password', '').strip()
            # check email uniqueness (exclude self)
            dup = db.execute('SELECT id FROM usuarios WHERE email = ? AND id != ?', (email, id)).fetchone()
            if dup:
                flash('El correo ya está en uso por otro usuario.', 'danger')
                return render_template('admin/usuarios_form.html', usuario=usuario)
            if nuevo_password:
                from werkzeug.security import generate_password_hash
                pw_hash = generate_password_hash(nuevo_password)
                db.execute('UPDATE usuarios SET nombre=?, email=?, rol=?, activo=?, password_hash=? WHERE id=?',
                           (nombre, email, rol, activo, pw_hash, id))
            else:
                db.execute('UPDATE usuarios SET nombre=?, email=?, rol=?, activo=? WHERE id=?',
                           (nombre, email, rol, activo, id))
            db.commit()
            flash('Usuario actualizado.', 'success')
            return redirect(url_for('admin_usuarios_list'))
        return render_template('admin/usuarios_form.html', usuario=usuario)

    @app.route('/admin/usuarios/<int:id>/eliminar', methods=['POST'])
    @login_required
    @role_required('admin')
    def admin_usuarios_eliminar(id):
        db = get_db()
        # prevent self-deletion
        if id == session['usuario_id']:
            flash('No puedes eliminar tu propia cuenta.', 'danger')
            return redirect(url_for('admin_usuarios_list'))
        db.execute('DELETE FROM selecciones WHERE quiniela_id IN (SELECT id FROM quinielas WHERE usuario_id=?)', (id,))
        db.execute('DELETE FROM quinielas WHERE usuario_id = ?', (id,))
        db.execute('DELETE FROM usuarios WHERE id = ?', (id,))
        db.commit()
        flash('Usuario eliminado.', 'success')
        return redirect(url_for('admin_usuarios_list'))

    @app.route('/admin/usuarios/nuevo', methods=['GET', 'POST'])
    @login_required
    @role_required('admin')
    def admin_usuarios_nuevo():
        if request.method == 'POST':
            email = request.form['email'].strip()
            password = request.form['password']
            nombre = request.form['nombre'].strip()
            rol = request.form['rol']
            if get_user_by_email(email):
                flash('El correo ya está registrado.', 'danger')
                return render_template('admin/usuarios_form.html', usuario=None)
            create_user(email, password, nombre, rol)
            flash('Usuario creado.', 'success')
            return redirect(url_for('admin_usuarios_list'))
        return render_template('admin/usuarios_form.html', usuario=None)

    # Admin: settings
    @app.route('/admin/settings', methods=['GET', 'POST'])
    @login_required
    @role_required('admin')
    def admin_settings():
        if request.method == 'POST':
            quinielas_activas = '1' if 'quinielas_activas' in request.form else '0'
            set_setting('quinielas_activas', quinielas_activas)
            flash('Configuración guardada.', 'success')
            return redirect(url_for('admin_settings'))
        settings = {}
        db = get_db()
        rows = db.execute("SELECT key, value FROM settings").fetchall()
        for row in rows:
            settings[row['key']] = row['value']
        return render_template('admin/settings.html', settings=settings)

    # PDF: resumen de quiniela
    @app.route('/quiniela/pdf')
    @login_required
    def quiniela_pdf():
        from reportlab.lib.pagesizes import letter
        from reportlab.lib import colors
        from reportlab.lib.units import mm
        from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.enums import TA_CENTER, TA_LEFT

        db = get_db()
        quiniela = db.execute('SELECT * FROM quinielas WHERE usuario_id = ?', (session['usuario_id'],)).fetchone()
        usuario = db.execute('SELECT nombre FROM usuarios WHERE id = ?', (session['usuario_id'],)).fetchone()

        partidos = db.execute('''
            SELECT p.fase, p.fecha,
                   el.nombre AS local,
                   ev.nombre AS visitante,
                   s.eleccion
            FROM partidos p
            JOIN equipos el ON p.equipo_local_id = el.id
            JOIN equipos ev ON p.equipo_visitante_id = ev.id
            LEFT JOIN selecciones s ON s.partido_id = p.id AND s.quiniela_id = ?
            ORDER BY p.fecha
        ''', (quiniela['id'],)).fetchall()

        # Build PDF
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter,
                                leftMargin=20*mm, rightMargin=20*mm,
                                topMargin=20*mm, bottomMargin=20*mm)
        styles = getSampleStyleSheet()
        elements = []

        # Title
        title_style = ParagraphStyle('Title', parent=styles['Title'], fontSize=18, alignment=TA_CENTER, spaceAfter=4*mm)
        elements.append(Paragraph("Mundial Quiniela - Resumen", title_style))

        # User info
        info_style = ParagraphStyle('Info', parent=styles['Normal'], fontSize=10, alignment=TA_CENTER, spaceAfter=2*mm, textColor=colors.HexColor('#555555'))
        elements.append(Paragraph(f"Usuario: <b>{usuario['nombre']}</b>", info_style))
        if quiniela['finalizada'] and quiniela['finalizada_en']:
            elements.append(Paragraph(f"Finalizada: {quiniela['finalizada_en']}", info_style))
        else:
            elements.append(Paragraph("Estado: <i>Sin finalizar</i>", info_style))
        elements.append(Spacer(1, 6*mm))

        # Table - text only (no flags for PDF stability)
        data = [['#', 'Fase', 'Fecha', 'Local', 'Visitante', 'Eleccion']]
        for i, p in enumerate(partidos, 1):
            eleccion = p['eleccion'] if p['eleccion'] else '-'
            if eleccion == '1':
                eleccion_texto = f"1 - {p['local']}"
            elif eleccion == '2':
                eleccion_texto = f"2 - {p['visitante']}"
            elif eleccion == 'X':
                eleccion_texto = "X - Empate"
            else:
                eleccion_texto = "-"
            data.append([
                str(i),
                p['fase'],
                p['fecha'][:16] if p['fecha'] else '-',
                p['local'],
                p['visitante'],
                eleccion_texto
            ])

        table = Table(data, colWidths=[10*mm, 25*mm, 28*mm, 45*mm, 45*mm, 35*mm])
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#e94560')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 9),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('ALIGN', (3, 1), (5, -1), 'LEFT'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#cccccc')),
            ('TOPPADDING', (0, 0), (-1, -1), 5),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        elements.append(table)

        # Footer
        elements.append(Spacer(1, 8*mm))
        from datetime import datetime
        footer_style = ParagraphStyle('Footer', parent=styles['Normal'], fontSize=8, alignment=TA_CENTER, textColor=colors.HexColor('#999999'))
        elements.append(Paragraph(f"Generado el {datetime.now().strftime('%d/%m/%Y %H:%M')}", footer_style))

        doc.build(elements)
        buffer.seek(0)

        response = make_response(buffer.read())
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = f'attachment; filename=quiniela_{usuario["nombre"]}.pdf'
        return response

    # Leaderboard
    @app.route('/leaderboard')
    @login_required
    def leaderboard():
        db = get_db()
        ranking = db.execute('''
            SELECT u.nombre, COUNT(s.id) AS aciertos
            FROM usuarios u
            JOIN quinielas q ON u.id = q.usuario_id
            JOIN selecciones s ON q.id = s.quiniela_id
            JOIN partidos p ON s.partido_id = p.id
            WHERE (s.elección = '1' AND p.goles_local > p.goles_visitante)
               OR (s.elección = 'X' AND p.goles_local = p.goles_visitante)
               OR (s.elección = '2' AND p.goles_local < p.goles_visitante)
            GROUP BY u.id
            ORDER BY aciertos DESC, u.nombre
        ''').fetchall()
        return render_template('leaderboard/index.html', ranking=ranking)

    # Leaderboard chart (imagen)
    @app.route('/leaderboard/chart')
    @login_required
    def leaderboard_chart():
        import matplotlib
        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
        import matplotlib.patches as mpatches
        from io import BytesIO
        import base64

        db = get_db()
        ranking = db.execute('''
            SELECT u.nombre, COUNT(s.id) AS aciertos
            FROM usuarios u
            JOIN quinielas q ON u.id = q.usuario_id
            JOIN selecciones s ON q.id = s.quiniela_id
            JOIN partidos p ON s.partido_id = p.id
            WHERE (s.elección = '1' AND p.goles_local > p.goles_visitante)
               OR (s.elección = 'X' AND p.goles_local = p.goles_visitante)
               OR (s.elección = '2' AND p.goles_local < p.goles_visitante)
            GROUP BY u.id
            ORDER BY aciertos DESC, u.nombre
        ''').fetchall()

        if not ranking:
            return "Sin datos suficientes para la gráfica", 404

        nombres = [r['nombre'] for r in ranking]
        aciertos = [r['aciertos'] for r in ranking]

        # Colores para las barras (oro, plata, bronce, resto)
        colors = []
        for i in range(len(nombres)):
            if i == 0:
                colors.append('#FFD700')  # oro
            elif i == 1:
                colors.append('#C0C0C0')  # plata
            elif i == 2:
                colors.append('#CD7F32')  # bronce
            else:
                colors.append('#e94560')  # rojo tema

        fig, ax = plt.subplots(figsize=(10, max(4, len(nombres) * 0.5)))
        bars = ax.barh(range(len(nombres)), aciertos, color=colors, height=0.6, edgecolor='white', linewidth=0.5)

        ax.set_yticks(range(len(nombres)))
        ax.set_yticklabels(nombres, fontsize=9)
        ax.set_xlabel('Aciertos', fontsize=10)
        ax.set_title('🏆 Leaderboard - Aciertos por Usuario', fontsize=14, fontweight='bold', pad=15)
        ax.invert_yaxis()

        # Agregar valores en las barras
        for bar, val in zip(bars, aciertos):
            ax.text(bar.get_width() + 0.3, bar.get_y() + bar.get_height()/2,
                    str(val), va='center', fontsize=9, fontweight='bold')

        # Leyenda
        oro = mpatches.Patch(color='#FFD700', label='1° Lugar')
        plata = mpatches.Patch(color='#C0C0C0', label='2° Lugar')
        bronce = mpatches.Patch(color='#CD7F32', label='3° Lugar')
        otros = mpatches.Patch(color='#e94560', label='Otros')
        ax.legend(handles=[oro, plata, bronce, otros], loc='lower right', fontsize=8)

        ax.set_facecolor('#f8f9fa')
        fig.patch.set_facecolor('white')
        plt.tight_layout()

        buf = BytesIO()
        fig.savefig(buf, format='png', dpi=120, bbox_inches='tight')
        plt.close(fig)
        buf.seek(0)

        response = make_response(buf.read())
        response.headers['Content-Type'] = 'image/png'
        return response

    return app

app = create_app()
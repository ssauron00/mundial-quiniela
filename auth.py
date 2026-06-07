import functools
from flask import session, flash, redirect, url_for, request
from werkzeug.security import check_password_hash, generate_password_hash
from database import get_db

def login_required(f):
    @functools.wraps(f)
    def decorated_function(*args, **kwargs):
        if 'usuario_id' not in session:
            flash('Debes iniciar sesión.', 'warning')
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

def role_required(*roles):
    def wrapper(f):
        @functools.wraps(f)
        def decorated_function(*args, **kwargs):
            if 'usuario_id' not in session:
                flash('Debes iniciar sesión.', 'warning')
                return redirect(url_for('index'))
            # check role
            db = get_db()
            user = db.execute('SELECT rol FROM usuarios WHERE id = ?', (session['usuario_id'],)).fetchone()
            if user is None or user['rol'] not in roles:
                flash('No tienes permiso para acceder a esta página.', 'danger')
                return redirect(url_for('index'))
            return f(*args, **kwargs)
        return decorated_function
    return wrapper

def get_user_by_email(email):
    db = get_db()
    return db.execute('SELECT * FROM usuarios WHERE email = ?', (email,)).fetchone()

def create_user(email, password, nombre, rol='usuario'):
    db = get_db()
    password_hash = generate_password_hash(password)
    cur = db.execute(
        'INSERT INTO usuarios (email, password_hash, nombre, rol) VALUES (?, ?, ?, ?)',
        (email, password_hash, nombre, rol)
    )
    db.commit()
    # create quiniela record for new user
    user_id = cur.lastrowid
    db.execute('INSERT INTO quinielas (usuario_id) VALUES (?)', (user_id,))
    db.commit()
    return user_id

def check_password(password, password_hash):
    return check_password_hash(password_hash, password)
-- Schema para SQLite (Railway)

CREATE TABLE IF NOT EXISTS equipos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    bandera_url TEXT
);

CREATE TABLE IF NOT EXISTS partidos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fase TEXT NOT NULL,
    fecha DATETIME NOT NULL,
    equipo_local_id INTEGER NOT NULL,
    equipo_visitante_id INTEGER NOT NULL,
    goles_local INTEGER,
    goles_visitante INTEGER
);

CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    nombre TEXT NOT NULL,
    activo INTEGER NOT NULL DEFAULT 1,
    rol TEXT NOT NULL DEFAULT 'usuario'
);

CREATE TABLE IF NOT EXISTS quinielas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER NOT NULL,
    creado_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    finalizada INTEGER NOT NULL DEFAULT 0,
    finalizada_en DATETIME,
    codigo_verificacion TEXT
);

CREATE TABLE IF NOT EXISTS selecciones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    quiniela_id INTEGER NOT NULL,
    partido_id INTEGER NOT NULL,
    eleccion TEXT NOT NULL CHECK (eleccion IN ('1','X','2'))
);

CREATE TABLE IF NOT EXISTS menu_grupos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    orden INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS menu_opciones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    ruta TEXT NOT NULL,
    grupo_id INTEGER NOT NULL,
    orden INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS rol_menu_permisos (
    rol TEXT NOT NULL,
    opcion_id INTEGER NOT NULL,
    PRIMARY KEY (rol, opcion_id)
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL DEFAULT '',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Datos iniciales
INSERT OR IGNORE INTO menu_grupos (id, nombre, orden) VALUES (1, 'Partido', 1);
INSERT OR IGNORE INTO menu_grupos (id, nombre, orden) VALUES (2, 'Quiniela', 2);
INSERT OR IGNORE INTO menu_grupos (id, nombre, orden) VALUES (3, 'Leaderboard', 3);
INSERT OR IGNORE INTO menu_grupos (id, nombre, orden) VALUES (4, 'Admin', 4);

INSERT OR IGNORE INTO menu_opciones (id, nombre, ruta, grupo_id, orden) VALUES (1, 'Listar partidos', '/partidos', 1, 1);
INSERT OR IGNORE INTO menu_opciones (id, nombre, ruta, grupo_id, orden) VALUES (2, 'Crear partido', '/partidos/nuevo', 1, 2);
INSERT OR IGNORE INTO menu_opciones (id, nombre, ruta, grupo_id, orden) VALUES (3, 'Hacer quiniela', '/quiniela/hacer', 2, 1);
INSERT OR IGNORE INTO menu_opciones (id, nombre, ruta, grupo_id, orden) VALUES (4, 'Ver leaderboard', '/leaderboard', 3, 1);
INSERT OR IGNORE INTO menu_opciones (id, nombre, ruta, grupo_id, orden) VALUES (5, 'Usuarios', '/admin/usuarios', 4, 1);
INSERT OR IGNORE INTO menu_opciones (id, nombre, ruta, grupo_id, orden) VALUES (6, 'Configuracion', '/admin/settings', 4, 2);

INSERT OR IGNORE INTO rol_menu_permisos (rol, opcion_id) VALUES ('admin', 1);
INSERT OR IGNORE INTO rol_menu_permisos (rol, opcion_id) VALUES ('admin', 2);
INSERT OR IGNORE INTO rol_menu_permisos (rol, opcion_id) VALUES ('admin', 3);
INSERT OR IGNORE INTO rol_menu_permisos (rol, opcion_id) VALUES ('admin', 4);
INSERT OR IGNORE INTO rol_menu_permisos (rol, opcion_id) VALUES ('admin', 5);
INSERT OR IGNORE INTO rol_menu_permisos (rol, opcion_id) VALUES ('admin', 6);
INSERT OR IGNORE INTO rol_menu_permisos (rol, opcion_id) VALUES ('usuario', 3);
INSERT OR IGNORE INTO rol_menu_permisos (rol, opcion_id) VALUES ('usuario', 4);

INSERT OR IGNORE INTO settings (key, value) VALUES ('quinielas_activas', '1');

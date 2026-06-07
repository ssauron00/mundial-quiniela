-- Schema compatible with SQLite and PostgreSQL

DROP TABLE IF EXISTS selecciones CASCADE;
DROP TABLE IF EXISTS quinielas CASCADE;
DROP TABLE IF EXISTS usuarios CASCADE;
DROP TABLE IF EXISTS partidos CASCADE;
DROP TABLE IF EXISTS equipos CASCADE;
DROP TABLE IF EXISTS rol_menu_permisos CASCADE;
DROP TABLE IF EXISTS menu_opciones CASCADE;
DROP TABLE IF EXISTS menu_grupos CASCADE;
DROP TABLE IF EXISTS settings CASCADE;

CREATE TABLE equipos (
    id SERIAL PRIMARY KEY,
    nombre TEXT NOT NULL,
    bandera_url TEXT
);

CREATE TABLE partidos (
    id SERIAL PRIMARY KEY,
    fase TEXT NOT NULL,
    fecha TIMESTAMP NOT NULL,
    equipo_local_id INTEGER NOT NULL REFERENCES equipos(id),
    equipo_visitante_id INTEGER NOT NULL REFERENCES equipos(id),
    goles_local INTEGER,
    goles_visitante INTEGER
);

CREATE TABLE usuarios (
    id SERIAL PRIMARY KEY,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    nombre TEXT NOT NULL,
    activo BOOLEAN NOT NULL DEFAULT true,
    rol TEXT NOT NULL DEFAULT 'usuario'
);

CREATE TABLE quinielas (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER NOT NULL REFERENCES usuarios(id),
    creado_en TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    finalizada BOOLEAN NOT NULL DEFAULT false,
    finalizada_en TIMESTAMP
);

CREATE TABLE selecciones (
    id SERIAL PRIMARY KEY,
    quiniela_id INTEGER NOT NULL REFERENCES quinielas(id),
    partido_id INTEGER NOT NULL REFERENCES partidos(id),
    eleccion TEXT NOT NULL CHECK (eleccion IN ('1','X','2')),
    UNIQUE(quiniela_id, partido_id)
);

CREATE TABLE menu_grupos (
    id SERIAL PRIMARY KEY,
    nombre TEXT NOT NULL,
    orden INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE menu_opciones (
    id SERIAL PRIMARY KEY,
    nombre TEXT NOT NULL,
    ruta TEXT NOT NULL,
    grupo_id INTEGER NOT NULL REFERENCES menu_grupos(id),
    orden INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE rol_menu_permisos (
    rol TEXT NOT NULL,
    opcion_id INTEGER NOT NULL REFERENCES menu_opciones(id),
    PRIMARY KEY (rol, opcion_id)
);

CREATE TABLE settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL DEFAULT '',
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

INSERT INTO menu_grupos (nombre, orden) VALUES ('Partido', 1);
INSERT INTO menu_grupos (nombre, orden) VALUES ('Quiniela', 2);
INSERT INTO menu_grupos (nombre, orden) VALUES ('Leaderboard', 3);
INSERT INTO menu_grupos (nombre, orden) VALUES ('Admin', 4);

INSERT INTO menu_opciones (nombre, ruta, grupo_id, orden) VALUES
    ('Listar partidos', '/partidos', 1, 1),
    ('Crear partido', '/partidos/nuevo', 1, 2),
    ('Hacer quiniela', '/quiniela/hacer', 2, 1),
    ('Ver leaderboard', '/leaderboard', 3, 1),
    ('Usuarios', '/admin/usuarios', 4, 1),
    ('Configuracion', '/admin/settings', 4, 2);

INSERT INTO rol_menu_permisos (rol, opcion_id) VALUES
    ('admin', 1), ('admin', 2), ('admin', 3), ('admin', 4), ('admin', 5), ('admin', 6),
    ('usuario', 3), ('usuario', 4);

INSERT INTO settings (key, value) VALUES ('quinielas_activas', '1');

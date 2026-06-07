-- Drop tables if exist (for development)
DROP TABLE IF EXISTS selecciones;
DROP TABLE IF EXISTS quinielas;
DROP TABLE IF EXISTS usuarios;
DROP TABLE IF EXISTS partidos;
DROP TABLE IF EXISTS equipos;
DROP TABLE IF EXISTS rol_menu_permisos;
DROP TABLE IF EXISTS menu_opciones;
DROP TABLE IF EXISTS menu_grupos;

-- Teams
CREATE TABLE equipos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    bandera_url TEXT
);

-- Matches
CREATE TABLE partidos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    fase TEXT NOT NULL,          -- e.g., 'grupos', 'octavos', etc.
    fecha DATETIME NOT NULL,
    equipo_local_id INTEGER NOT NULL,
    equipo_visitante_id INTEGER NOT NULL,
    goles_local INTEGER,
    goles_visitante INTEGER,
    FOREIGN KEY (equipo_local_id) REFERENCES equipos(id),
    FOREIGN KEY (equipo_visitante_id) REFERENCES equipos(id)
);

-- Users
CREATE TABLE usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    nombre TEXT NOT NULL,
    activo BOOLEAN NOT NULL DEFAULT 1,
    rol TEXT NOT NULL DEFAULT 'usuario'   -- 'admin' or 'usuario'
);

-- Quiniela (one per user)
CREATE TABLE quinielas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER NOT NULL,
    creado_en DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    finalizada BOOLEAN NOT NULL DEFAULT 0,
    finalizada_en DATETIME,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id)
);

-- Selections (user picks)
CREATE TABLE selecciones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    quiniela_id INTEGER NOT NULL,
    partido_id INTEGER NOT NULL,
    elección TEXT NOT NULL CHECK (elección IN ('1','X','2')),
    FOREIGN KEY (quiniela_id) REFERENCES quinielas(id),
    FOREIGN KEY (partido_id) REFERENCES partidos(id),
    UNIQUE(quiniela_id, partido_id)  -- one selection per match per user
);

-- Menu groups
CREATE TABLE menu_grupos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    orden INTEGER NOT NULL DEFAULT 0
);

-- Menu options
CREATE TABLE menu_opciones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    ruta TEXT NOT NULL,
    grupo_id INTEGER NOT NULL,
    orden INTEGER NOT NULL DEFAULT 0,
    FOREIGN KEY (grupo_id) REFERENCES menu_grupos(id)
);

-- Role-menu permissions
CREATE TABLE rol_menu_permisos (
    rol TEXT NOT NULL,
    opcion_id INTEGER NOT NULL,
    PRIMARY KEY (rol, opcion_id),
    FOREIGN KEY (opcion_id) REFERENCES menu_opciones(id)
);

-- Global settings (key-value)
CREATE TABLE settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL DEFAULT '',
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Insert initial data for menu
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
    ('Configuración', '/admin/settings', 4, 2);

-- Permissions: admin can see all, usuario can see quiniela and leaderboard
INSERT INTO rol_menu_permisos (rol, opcion_id) VALUES
    ('admin', 1), ('admin', 2), ('admin', 3), ('admin', 4), ('admin', 5), ('admin', 6),
    ('usuario', 3), ('usuario', 4);

-- Default settings
INSERT INTO settings (key, value) VALUES ('quinielas_activas', '1');

-- NOTE: Admin user is created via create_admin.py, not here.
-- Default credentials: admin@example.com / admin123

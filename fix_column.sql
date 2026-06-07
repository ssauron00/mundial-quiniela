CREATE TABLE IF NOT EXISTS selecciones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    quiniela_id INTEGER NOT NULL,
    partido_id INTEGER NOT NULL,
    eleccion TEXT NOT NULL CHECK (eleccion IN ('1','X','2'))
);

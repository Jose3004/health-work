import sqlite3

# Crear conexión (se creará automáticamente el archivo healthy.db)
conn = sqlite3.connect("instance/healthy.db")

# Crear tabla de usuarios
conn.execute("""
CREATE TABLE IF NOT EXISTS usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    area TEXT
)
""")

# Crear tabla de citas
conn.execute("""
CREATE TABLE IF NOT EXISTS citas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER,
    fecha TEXT NOT NULL,
    hora TEXT NOT NULL,
    motivo TEXT,
    FOREIGN KEY(usuario_id) REFERENCES usuarios(id)
)
""")

# Cerrar conexión
conn.close()

print("Base de datos creada correctamente (healthy.db)")

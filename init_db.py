import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()
DB_PATH = os.getenv("DB_PATH", "pedidos.db")

conn = sqlite3.connect(DB_PATH)
c = conn.cursor()
c.execute('''
CREATE TABLE IF NOT EXISTS pedidos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre TEXT,
    telefono TEXT,
    direccion TEXT,
    items TEXT,
    total REAL,
    estado TEXT,
    creado TEXT
)
''')
conn.commit()
conn.close()
print("Base de datos creada en", DB_PATH)
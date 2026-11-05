import os
from dotenv import load_dotenv
import mysql.connector
from mysql.connector import Error

load_dotenv()
def get_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "127.0.0.1"),
        port=int(os.getenv("DB_PORT", "3306")),
        database=os.getenv("DB_NAME", "AcaBiblioteca"),
        user=os.getenv("DB_USER", "estudiante_php"),
        password=os.getenv("DB_PASSWORD", "clave_segura"),
        charset="utf8mb4",
        collation="utf8mb4_unicode_ci",
    )

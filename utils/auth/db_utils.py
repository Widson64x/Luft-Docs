# utils/db_utils.py

import os
from Config import DB_PATH
import sqlite3

def connect_db():
    return sqlite3.connect(DB_PATH)

def verificar_usuario(user_name: str, user_id: str) -> bool:
    """
    Retorna True se existir um registro na tabela `users` cujo
    user_name e user_id correspondam aos parâmetros.
    """
    conn = connect_db()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM users WHERE user_name = ? AND user_id = ?", (user_name, user_id))
    resultado = cursor.fetchone()
    conn.close()
    return resultado is not None

# create_db.py

import sqlite3

def criar_banco_e_tabela(path='users.db'):
    """
    Cria (ou abre, se já existir) o arquivo SQLite em `path`
    e garante que exista a tabela `users` com colunas (user_name TEXT, user_id TEXT).
    """
    conn = sqlite3.connect(path)
    cursor = conn.cursor()
    
    # Cria a tabela de usuários, se não existir
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS users (
        user_name TEXT NOT NULL,
        user_id   TEXT NOT NULL,
        email VARCHAR(255) NOT NULL,
        permission TEXT NOT NULL,
        token     TEXT,
        PRIMARY KEY(user_name, user_id)
    )
    """)
    
    # Para fins de teste, inserir alguns usuários fixos
    # (o IGNORE evita erro se já existirem)
    cursor.execute("INSERT OR IGNORE INTO users (user_name, user_id, permission, email) VALUES (?, ?, ?, ?)", ("widson.araujo", "12345", "MASTER", "widson.araujo@luftlogistics.com"))
    cursor.execute("INSERT OR IGNORE INTO users (user_name, user_id, permission, email) VALUES (?, ?, ?, ?)", ("luft.teste", "12345", "ADM", "luft.teste@luftlogistics.com"))
    cursor.execute("INSERT OR IGNORE INTO users (user_name, user_id, permission, email) VALUES (?, ?, ?, ?)", ("luft", "12345", "USER", "ana.silva@luftlogistics.com"))
    
    conn.commit()
    conn.close()
    print(f"[INFO] Banco SQLite criado/atualizado em '{path}' com tabela 'users' e dados de teste.")


if __name__ == "__main__":
    criar_banco_e_tabela()

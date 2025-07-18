# /utils/database_utils.py
import sqlite3
import os
from flask import current_app, g

# Define o nome do arquivo do banco de dados
DATABASE_NAME = 'recommendations.db'

def get_db_path():
    """Retorna o caminho completo para o arquivo do banco de dados."""
    return os.path.join(current_app.root_path, DATABASE_NAME)

def get_db():
    """
    Abre uma nova conexão com o banco de dados se não houver uma para a requisição atual.
    'g' é um objeto especial do Flask que é único para cada requisição.
    """
    if 'db' not in g:
        g.db = sqlite3.connect(
            get_db_path(),
            detect_types=sqlite3.PARSE_DECLTYPES
        )
        g.db.row_factory = sqlite3.Row  # Permite acessar colunas por nome
    return g.db

def close_db(e=None):
    """Fecha a conexão com o banco de dados ao final da requisição."""
    db = g.pop('db', None)
    if db is not None:
        db.close()

def init_db():
    """
    Cria as tabelas do banco de dados. Deve ser executado uma vez para configurar o banco.
    """
    db = sqlite3.connect(get_db_path())
    cursor = db.cursor()

    # Tabela para registrar acessos aos documentos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS document_access (
            document_id TEXT PRIMARY KEY,
            access_count INTEGER NOT NULL DEFAULT 1,
            last_access TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Tabela para registrar os termos buscados
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS search_log (
            query_term TEXT PRIMARY KEY,
            search_count INTEGER NOT NULL DEFAULT 1,
            last_searched TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    db.commit()
    db.close()
    print("Banco de dados inicializado com sucesso.")

def init_app(app):
    """Registra as funções do banco de dados com a aplicação Flask."""
    app.teardown_appcontext(close_db)

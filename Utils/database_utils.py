# /utils/database_utils.py
import sqlite3
import os
from flask import current_app, g
from Config import BASE_DIR

# Define o nome do arquivo do banco de dados
DATABASE_NAME = BASE_DIR / 'DATA' / 'luftdocs.db'

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

def create_bug_reports_table(cursor):
    """
    Cria ou atualiza a tabela de report de bugs (bug_reports).
    Adiciona novas colunas se a tabela já existir, mas as colunas não.
    """
    # Verifica as colunas existentes na tabela para evitar erros
    cursor.execute("PRAGMA table_info(bug_reports)")
    existing_columns = [column[1] for column in cursor.fetchall()]

    # Se a lista de colunas estiver vazia, a tabela não existe. Então, a criamos.
    if not existing_columns:
        print("Criando nova tabela 'bug_reports'...")
        cursor.execute('''
            CREATE TABLE bug_reports (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                report_type TEXT NOT NULL,
                target_entity TEXT,
                description TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'aberto',
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        ''')
    # Se a tabela já existe, verificamos se as colunas específicas estão faltando
    else:
        if 'report_type' not in existing_columns:
            print("Adicionando coluna 'report_type' à tabela 'bug_reports'...")
            cursor.execute("ALTER TABLE bug_reports ADD COLUMN report_type TEXT NOT NULL DEFAULT 'geral'")
        if 'target_entity' not in existing_columns:
            print("Adicionando coluna 'target_entity' à tabela 'bug_reports'...")
            cursor.execute("ALTER TABLE bug_reports ADD COLUMN target_entity TEXT")


def init_db():
    """
    Cria todas as tabelas do banco de dados. Deve ser executado uma vez para configurar o banco.
    """
    print("Inicializando o banco de dados...")
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
    
    # --- ADIÇÃO DA CRIAÇÃO DA TABELA DE BUGS ---
    create_bug_reports_table(cursor)
    
    db.commit()
    db.close()
    print("Banco de dados inicializado com sucesso.")

def init_app(app):
    """Registra as funções do banco de dados com a aplicação Flask."""
    app.teardown_appcontext(close_db)

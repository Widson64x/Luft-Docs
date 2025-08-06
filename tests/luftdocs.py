import sqlite3

def criar_tabelas():
    """Cria as tabelas no banco de dados luftdocs.db."""
    conn = sqlite3.connect('luftdocs.db')
    cursor = conn.cursor()

    # 1. Tabela de Módulos
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS modulos (
            id TEXT PRIMARY KEY,
            nome TEXT NOT NULL,
            descricao TEXT,
            icone TEXT,
            status TEXT,
            ultima_edicao_user TEXT,
            ultima_edicao_data TEXT,
            pending_edit_user TEXT,
            pending_edit_data TEXT,
            current_version TEXT,
            last_approved_by TEXT,
            last_approved_on TEXT
        )
    ''')

    # 2. Tabela de Palavras-Chave (relação muitos-para-muitos)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS palavras_chave (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            modulo_id TEXT,
            palavra TEXT,
            FOREIGN KEY (modulo_id) REFERENCES modulos (id)
        )
    ''')

    # 3. Tabela de Módulos Relacionados (relação muitos-para-muitos)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS modulos_relacionados (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            modulo_id TEXT,
            relacionado_id TEXT,
            FOREIGN KEY (modulo_id) REFERENCES modulos (id),
            FOREIGN KEY (relacionado_id) REFERENCES modulos (id)
        )
    ''')

    # 4. Tabela de Histórico de Edição (relação um-para-muitos)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS historico_edicao (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            modulo_id TEXT,
            event TEXT,
            version TEXT,
            editor TEXT,
            approver TEXT,
            timestamp TEXT,
            backup_file_doc TEXT,
            backup_file_tech TEXT,
            FOREIGN KEY (modulo_id) REFERENCES modulos (id)
        )
    ''')

    # 5. Tabela de Palavras Globais
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS palavras_globais (
            palavra TEXT PRIMARY KEY,
            descricao TEXT
        )
    ''')

    conn.commit()
    conn.close()
    print("Banco de dados 'luftdocs.db' e tabelas criados com sucesso!")

# Executar a função para criar as tabelas
if __name__ == '__main__':
    criar_tabelas()
# fix_db.py
import sqlite3

DB_NAME = 'luftdocs.db'

def fix_document_access_table():
    """
    Altera a tabela 'document_access' para garantir que 'access_count'
    seja um campo obrigatório (NOT NULL) com valor padrão 1.
    Este script corrige dados existentes que possam ser nulos.
    """
    print(f"Iniciando a correção da tabela 'document_access' em '{DB_NAME}'...")
    try:
        conn = sqlite3.connect(DB_NAME)
        cursor = conn.cursor()

        # Inicia uma transação para garantir que tudo seja feito de uma vez
        cursor.execute("BEGIN TRANSACTION;")

        # 1. Cria uma nova tabela com a estrutura correta e robusta
        print(" -> Etapa 1: Criando tabela temporária com a estrutura correta...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS document_access_new (
                document_id TEXT PRIMARY KEY,
                access_count INTEGER NOT NULL DEFAULT 1,
                last_access TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # 2. Copia os dados da tabela antiga para a nova, corrigindo os valores nulos
        print(" -> Etapa 2: Copiando e corrigindo dados da tabela antiga...")
        cursor.execute("""
            INSERT INTO document_access_new (document_id, access_count, last_access)
            SELECT
                document_id,
                COALESCE(access_count, 0),
                COALESCE(last_access, CURRENT_TIMESTAMP)
            FROM document_access;
        """)

        # 3. Remove a tabela antiga
        print(" -> Etapa 3: Removendo a tabela antiga...")
        cursor.execute("DROP TABLE document_access;")

        # 4. Renomeia a nova tabela para o nome original
        print(" -> Etapa 4: Renomeando a tabela temporária...")
        cursor.execute("ALTER TABLE document_access_new RENAME TO document_access;")

        # Finaliza a transação, salvando todas as alterações
        conn.commit()
        print("\n[SUCESSO] Tabela 'document_access' corrigida com sucesso!")
        print("A coluna 'access_count' agora é obrigatória e o contador funcionará corretamente.")

    except sqlite3.Error as e:
        print(f"\n[ERRO] Ocorreu um erro ao tentar corrigir a tabela: {e}")
        if 'conn' in locals():
            print(" -> Revertendo todas as alterações (rollback)...")
            conn.rollback()
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == '__main__':
    fix_document_access_table()
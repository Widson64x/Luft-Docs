import json
import sqlite3
import os

# Variáveis para os caminhos dos arquivos
# Observação: Usando 'r' antes da string para garantir que as barras invertidas sejam tratadas corretamente.
DB_PATH = r'DATA/luftdocs.db'
JSON_PATH = r'DATA/permission.json'

def create_and_migrate_permissions(db_name, json_file):
    """
    Cria um esquema de banco de dados normalizado para permissões e migra os dados do JSON.
    A nova convenção de nomes usa um prefixo para agrupar as tabelas no navegador do banco de dados.
    """
    conn = None
    try:
        # Verifica se os arquivos existem antes de prosseguir
        if not os.path.exists(db_name):
            print(f"Erro: O arquivo de banco de dados '{db_name}' não foi encontrado.")
            return
        
        if not os.path.exists(json_file):
            print(f"Erro: O arquivo JSON '{json_file}' não foi encontrado.")
            return

        conn = sqlite3.connect(db_name)
        cursor = conn.cursor()

        # Nomes das novas tabelas, usando um prefixo para agrupar as tabelas de permissão
        # Lft_Tb_Perm_ para todas as tabelas, seguido pelo nome específico
        perm_data_table = 'Lft_Tb_Perm_Permissoes'
        group_data_table = 'Lft_Tb_Perm_Grupos'
        user_data_table = 'Lft_Tb_Perm_Usuarios'
        perm_group_rel_table = 'Lft_Tb_Perm_Rel_Grupos'
        perm_user_rel_table = 'Lft_Tb_Perm_Rel_Usuarios'

        # --- Etapa 1: Apaga as tabelas antigas (se existirem) para uma migração limpa ---
        # Removendo todas as versões anteriores para evitar conflitos
        cursor.execute("DROP TABLE IF EXISTS Lft_Tb_D_Permissoes")
        cursor.execute("DROP TABLE IF EXISTS Lft_Tb_D_Grupos")
        cursor.execute("DROP TABLE IF EXISTS Lft_Tb_D_Usuarios")
        cursor.execute("DROP TABLE IF EXISTS Lft_Tb_R_Permissoes_Grupos")
        cursor.execute("DROP TABLE IF EXISTS Lft_Tb_R_Permissoes_Usuarios")
        
        cursor.execute("DROP TABLE IF EXISTS Lft_Tb_Info_Permissoes")
        cursor.execute("DROP TABLE IF EXISTS Lft_Tb_Info_Grupos")
        cursor.execute("DROP TABLE IF EXISTS Lft_Tb_Info_Usuarios")
        cursor.execute("DROP TABLE IF EXISTS Lft_Tb_Rel_Permissoes_Grupos")
        cursor.execute("DROP TABLE IF EXISTS Lft_Tb_Rel_Permissoes_Usuarios")
        
        cursor.execute("DROP TABLE IF EXISTS Lft_Tb_Cfg_Permissoes")
        cursor.execute("DROP TABLE IF EXISTS Lft_Tb_Cfg_Grupos")
        cursor.execute("DROP TABLE IF EXISTS Lft_Tb_Cfg_Usuarios")
        
        cursor.execute("DROP TABLE IF EXISTS Lft_Tb_Auth_Permissoes")
        cursor.execute("DROP TABLE IF EXISTS Lft_Tb_Auth_Grupos")
        cursor.execute("DROP TABLE IF EXISTS Lft_Tb_Auth_Usuarios")
        
        cursor.execute("DROP TABLE IF EXISTS Lft_Tb_Perm_Permissoes")
        cursor.execute("DROP TABLE IF EXISTS Lft_Tb_Perm_Grupos")
        cursor.execute("DROP TABLE IF EXISTS Lft_Tb_Perm_Usuarios")
        cursor.execute("DROP TABLE IF EXISTS Lft_Tb_Rel_Permissoes_Grupos")
        cursor.execute("DROP TABLE IF EXISTS Lft_Tb_Rel_Permissoes_Usuarios")
        
        cursor.execute("DROP TABLE IF EXISTS Lft_Tb_Permissoes")
        cursor.execute("DROP TABLE IF EXISTS Lft_Tb_Grupos_Permissoes")
        cursor.execute("DROP TABLE IF EXISTS Lft_Tb_Usuarios_Permissoes")
        
        # --- Etapa 2: Cria as novas tabelas normalizadas ---
        print("Criando tabelas de permissão e relacionamento...")
        
        # Tabela de dados de Permissões
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS {perm_data_table} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                id_permissao TEXT UNIQUE NOT NULL,
                descricao TEXT
            )
        ''')

        # Tabela de dados de Grupos
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS {group_data_table} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome_grupo TEXT UNIQUE NOT NULL
            )
        ''')

        # Tabela de dados de Usuários
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS {user_data_table} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome_usuario TEXT UNIQUE NOT NULL
            )
        ''')
        
        # Tabela de relacionamento entre Permissões e Grupos
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS {perm_group_rel_table} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                permissao_id INTEGER,
                grupo_id INTEGER,
                FOREIGN KEY (permissao_id) REFERENCES {perm_data_table} (id),
                FOREIGN KEY (grupo_id) REFERENCES {group_data_table} (id),
                UNIQUE(permissao_id, grupo_id)
            )
        ''')

        # Tabela de relacionamento entre Permissões e Usuários
        cursor.execute(f'''
            CREATE TABLE IF NOT EXISTS {perm_user_rel_table} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                permissao_id INTEGER,
                usuario_id INTEGER,
                FOREIGN KEY (permissao_id) REFERENCES {perm_data_table} (id),
                FOREIGN KEY (usuario_id) REFERENCES {user_data_table} (id),
                UNIQUE(permissao_id, usuario_id)
            )
        ''')

        # --- Etapa 3: Lê o arquivo JSON ---
        with open(json_file, 'r', encoding='utf-8') as f:
            permissions_data = json.load(f)

        # --- Etapa 4: Popula as tabelas de dados e coleta os IDs ---
        print("Popunando tabelas de permissões e coletando IDs...")
        
        all_groups = set()
        all_users = set()
        
        for details in permissions_data.values():
            all_groups.update(details['groups'])
            all_users.update(details['users'])
        
        # Dicionários para mapear nomes para IDs (serão usados nas tabelas de relacionamento)
        perm_map = {}
        group_map = {}
        user_map = {}

        # Insere permissões
        for perm_name, details in permissions_data.items():
            cursor.execute(f'''
                INSERT INTO {perm_data_table} (id_permissao, descricao)
                VALUES (?, ?)
            ''', (perm_name, details['description']))
            perm_map[perm_name] = cursor.lastrowid
        
        # Insere grupos
        for group in sorted(list(all_groups)):
            cursor.execute(f'''
                INSERT INTO {group_data_table} (nome_grupo)
                VALUES (?)
            ''', (group,))
            group_map[group] = cursor.lastrowid

        # Insere usuários
        for user in sorted(list(all_users)):
            cursor.execute(f'''
                INSERT INTO {user_data_table} (nome_usuario)
                VALUES (?)
            ''', (user,))
            user_map[user] = cursor.lastrowid

        # --- Etapa 5: Popula as tabelas de relacionamento com os IDs ---
        print("Populando tabelas de relacionamento...")
        for perm_name, details in permissions_data.items():
            perm_id = perm_map[perm_name]
            
            # Popula relacionamento de grupos
            for group_name in details['groups']:
                group_id = group_map.get(group_name)
                if group_id:
                    cursor.execute(f'''
                        INSERT INTO {perm_group_rel_table} (permissao_id, grupo_id)
                        VALUES (?, ?)
                    ''', (perm_id, group_id))

            # Popula relacionamento de usuários
            for user_name in details['users']:
                user_id = user_map.get(user_name)
                if user_id:
                    cursor.execute(f'''
                        INSERT INTO {perm_user_rel_table} (permissao_id, usuario_id)
                        VALUES (?, ?)
                    ''', (perm_id, user_id))

        conn.commit()
        print("\nDados migrados com sucesso para as novas tabelas normalizadas.")

        # --- Etapa 6: Verificação para demonstrar a nova estrutura ---
        print("\nVerificando dados das novas tabelas:")
        
        print("\n--- Lft_Tb_Perm_Permissoes ---")
        cursor.execute(f'SELECT id, id_permissao, descricao FROM {perm_data_table} LIMIT 5')
        print(cursor.fetchall())
        
        print("\n--- Lft_Tb_Perm_Grupos ---")
        cursor.execute(f'SELECT id, nome_grupo FROM {group_data_table} LIMIT 5')
        print(cursor.fetchall())

        print("\n--- Lft_Tb_Perm_Rel_Grupos ---")
        cursor.execute(f'''
            SELECT T1.id_permissao, T2.nome_grupo
            FROM {perm_group_rel_table} AS rel
            JOIN {perm_data_table} AS T1 ON rel.permissao_id = T1.id
            JOIN {group_data_table} AS T2 ON rel.grupo_id = T2.id
            LIMIT 5
        ''')
        print(cursor.fetchall())
        
        print("\n--- Lft_Tb_Perm_Rel_Usuarios ---")
        cursor.execute(f'''
            SELECT T1.id_permissao, T2.nome_usuario
            FROM {perm_user_rel_table} AS rel
            JOIN {perm_data_table} AS T1 ON rel.permissao_id = T1.id
            JOIN {user_data_table} AS T2 ON rel.usuario_id = T2.id
            LIMIT 5
        ''')
        print(cursor.fetchall())


    except sqlite3.Error as e:
        print(f"Erro no banco de dados: {e}")
    except Exception as e:
        print(f"Ocorreu um erro inesperado: {e}")
    finally:
        if conn:
            conn.close()

# Executa a função de migração
if __name__ == '__main__':
    create_and_migrate_permissions(DB_PATH, JSON_PATH)

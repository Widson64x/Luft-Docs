import sqlite3
import os
import sys
from types import SimpleNamespace

# Importa as funções do arquivo permissions.py
# Nota: O caminho deve ser relativo ao diretório raiz do seu projeto
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))
from Routes.api.permissions import (
    load_permissions_by_user,
    load_permissions_by_group,
    load_permissions_for_user
)

# Caminho do banco de dados (ajuste se necessário)
DB_PATH = 'DATA/luftdocs.db'

# Simula o ambiente do Flask, incluindo a variável 'g' e a conexão com o banco
class MockG:
    def __init__(self):
        self.db = None

class MockApp:
    def __init__(self, db_path):
        self.config = {'DATABASE': db_path}

def mock_get_db_factory(db_path):
    g = MockG()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    g.db = conn
    return lambda: g.db

if __name__ == "__main__":
    # Configuração do teste
    test_user = 'widson.araujo'
    test_group = 'GRUPO TI'
    
    # Simula a sessão do Flask com os dados do usuário
    test_session = SimpleNamespace(
        get=lambda key, default=None: {
            'user_name': test_user,
            'user_group': {'acronym': test_group}
        }.get(key, default)
    )

    try:
        # Cria uma conexão simulada e a injeta nas funções
        original_get_db = sys.modules['Utils.database_utils'].get_db
        sys.modules['Utils.database_utils'].get_db = mock_get_db_factory(DB_PATH)

        print(f"--- Executando teste para o usuário '{test_user}' e grupo '{test_group}' ---")

        # 1. Testa a busca de permissões por usuário
        perms_user = load_permissions_by_user(test_user)
        print(f"\nPermissões individuais do usuário '{test_user}': {perms_user}")

        # 2. Testa a busca de permissões por grupo
        perms_group = load_permissions_by_group(test_group)
        print(f"Permissões do grupo '{test_group}': {perms_group}")

        # 3. Testa a busca combinada para usuário e grupo
        all_perms = load_permissions_for_user(test_session)
        print("\nTodas as permissões e status de acesso:")
        for perm, details in all_perms.items():
            print(f"  - {perm}: {details['description']} -> Acesso: {details['has_access']}")
            
    except Exception as e:
        print(f"\nOcorreu um erro inesperado: {e}")
    finally:
        # Restaura a função original para evitar efeitos colaterais
        sys.modules['Utils.database_utils'].get_db = original_get_db

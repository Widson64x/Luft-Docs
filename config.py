# config.py
from pathlib import Path
import os

# Diretório raiz do projeto
BASE_DIR = Path(__file__).parent.resolve()

# Dados e módulos
DATA_DIR         = BASE_DIR / 'data' / 'modules'
GLOBAL_DATA_DIR  = BASE_DIR / 'data' / 'global'
CONFIG_FILE      = BASE_DIR / 'data' / 'config.json'

# JSONs de controle
MODULE_ACCESS_FILE   = DATA_DIR / 'module_access.json'
SEARCH_HISTORY_FILE  = DATA_DIR / 'search_history.json'

# Limites e defaults
MAX_SEARCH_HISTORY = 20
TOP_MOST_ACCESSED  = 7
TOP_MOST_SEARCHED  = 7

USER_API_URL = os.environ.get("USER_API_URL", "https://api-wikidocs.onrender.com/api")
USER_API_CREDENTIAL_PARAMS = ["login_usuario"]
USER_API_TOKEN_PARAMS = ["token"]

'''
# Rodar localmente com API fake:

USER_API_URL = os.environ.get("USER_API_URL", "http://localhost:8000/api")

# Rodar com API fake no Render:

USER_API_URL = os.environ.get("USER_API_URL", "https://api-wikidocs.onrender.com/api")

'''

# Configuração do SQLite
DB_FILE = BASE_DIR / 'users.db'
DB_PATH = str(DB_FILE)        # caminho para sqlite3.connect()
# Se em futuro migrar para SQLAlchemy, poderia usar:
# DB_URI  = f"sqlite:///{DB_FILE}"

# Variáveis globais usadas em utils/
# (Adicione as linhas abaixo)

# Para utils/data/module_access.py
ARQ = MODULE_ACCESS_FILE  # Usado como caminho do arquivo de acesso de módulos

# Para utils/data/module_utils.py
# DATA_DIR, CONFIG_FILE, GLOBAL_DATA_DIR já definidos acima

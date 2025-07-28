# config.py
from pathlib import Path
# o 'import os' não é mais necessário para as URLs, mas pode ser usado por outras partes do projeto.
import os 

# -----------------------------------------------------------------------------
# AVISO DE SEGURANÇA: As chaves abaixo estão diretamente no código.
# NUNCA envie este arquivo para um repositório público (GitHub, GitLab, etc.).
# -----------------------------------------------------------------------------

# --- CHAVES DAS APIS DE IA (HARDCODED) ---
AI_KEYS = {
    'GEMINI_API_KEY': '',
    'GROQ_API_KEY': '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',
    'OPENAI_API_KEY': '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'
    # Adicione outras chaves de IA conforme necessário
}

# --- CONFIGURAÇÃO DE AMBIENTE E API ---
# Altere esta variável para 'local', 'render' ou 'real' para mudar a API de usuário.
ACTIVE_ENVIRONMENT = 'real'  # Opções: 'local', 'render', 'real'

# URLs para os diferentes ambientes
_URLS = {
    'local': "http://localhost:8000/api",
    'render': "https://api-wikidocs.onrender.com/api",
    'real': "http://172.16.200.80:8000/api"
}

# Define a URL da API com base no ambiente ativo
# Usa a URL 'real' como padrão se a variável for inválida.
USER_API_URL = _URLS.get(ACTIVE_ENVIRONMENT, _URLS['real'])

# =============================================================================
# O RESTANTE DAS SUAS CONFIGURAÇÕES (mantido como estava)
# =============================================================================

# Diretório raiz do projeto
BASE_DIR = Path(__file__).parent.resolve()

# Dados e módulos
DATA_DIR  = BASE_DIR / 'data' / 'modules'
GLOBAL_DATA_DIR = BASE_DIR / 'data' / 'global'
CONFIG_FILE = BASE_DIR / 'data' / 'config.json'

# JSONs de controle
MODULE_ACCESS_FILE = DATA_DIR / 'module_access.json'
SEARCH_HISTORY_FILE = DATA_DIR / 'search_history.json'

# Limites e defaults
MAX_SEARCH_HISTORY = 20
TOP_MOST_ACCESSED = 7
TOP_MOST_SEARCHED = 7

# Parâmetros da API de usuário
USER_API_CREDENTIAL_PARAMS = ["login_usuario"]
USER_API_TOKEN_PARAMS = ["token"]

# Configuração do SQLite
DB_FILE = BASE_DIR / 'users.db'
DB_PATH = str(DB_FILE) # caminho para sqlite3.connect()
# Se em futuro migrar para SQLAlchemy, poderia usar:
# DB_URI  = f"sqlite:///{DB_FILE}"

# Variáveis globais usadas em utils/
# (Adicione as linhas abaixo)

# Para utils/data/module_access.py
ARQ = MODULE_ACCESS_FILE # Usado como caminho do arquivo de acesso de módulos

# Para utils/data/module_utils.py
# DATA_DIR, CONFIG_FILE, GLOBAL_DATA_DIR já definidos acima

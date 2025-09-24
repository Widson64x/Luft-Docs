from pathlib import Path
import os

# -----------------------------------------------------------------------------
# AVISO DE SEGURANÇA: Prefira variáveis de ambiente para chaves.
# -----------------------------------------------------------------------------

AI_KEYS = {
    'GEMINI_API_KEY': os.getenv('GEMINI_API_KEY', ''),
    'GROQ_API_KEY':   os.getenv('GROQ_API_KEY', ''),
    'OPENAI_API_KEY': os.getenv('OPENAI_API_KEY', ''),
}

# --- CONFIGURAÇÃO DE AMBIENTE E API ---
ACTIVE_ENVIRONMENT = os.getenv('ACTIVE_ENVIRONMENT', 'real')  # 'local' | 'render' | 'real'
_URLS = {
    'local' : "http://localhost:8005/api",
    'render': "https://api-wikidocs.onrender.com/api",
    'real'  : "http://b2bi-apps.luftfarma.com.br/luft-api/api",
}
USER_API_URL = _URLS.get(ACTIVE_ENVIRONMENT, _URLS['real'])

# =============================================================================
# CAMINHOS
# =============================================================================

# Diretório raiz do projeto
BASE_DIR: Path = Path(__file__).parent.resolve()

# ---- Dois roots possíveis para DATA/ -----------------------------------------
# Modo de seleção: 'local' | 'server' | 'auto'
# - local  -> sempre usa a pasta DATA dentro do projeto
# - server -> força o uso do share UNC (afetando o servidor)
# - auto   -> se Windows e o share existir, usa servidor; senão local
DATA_SOURCE = os.getenv('DATA_SOURCE', 'server').lower()

# Caminho do servidor (pode ser sobrescrito por env)
SERVER_DATA_DEFAULT = r"\\172.16.200.80\c$\Documents\DATA_LUFTDOCS"
DATA_ROOT_SERVER: Path = Path(os.getenv('DATA_ROOT_SERVER', SERVER_DATA_DEFAULT))

# Caminho local (pode ser sobrescrito por env)
DATA_ROOT_LOCAL: Path = Path(os.getenv('DATA_ROOT_LOCAL', str(BASE_DIR / 'DATA')))

def choose_data_root() -> Path:
    mode = DATA_SOURCE
    if mode == 'server':
        return DATA_ROOT_SERVER
    if mode == 'server':
        try:
            if os.name == 'nt' and DATA_ROOT_SERVER.exists():
                return DATA_ROOT_SERVER
        except Exception:
            pass
        return DATA_ROOT_LOCAL
    # default/local
    return DATA_ROOT_LOCAL

# Root efetivo em uso
DATA_ROOT: Path = choose_data_root()

# --- Subpastas usuais dentro de DATA/ ---
MODULES_DIR:       Path = DATA_ROOT / 'modules'                 # (compat: DATA_DIR -> abaixo)
GLOBAL_DATA_DIR:   Path = DATA_ROOT / 'global'
IMAGES_DIR:        Path = DATA_ROOT / 'img'
VIDEOS_DIR:        Path = DATA_ROOT / 'videos'
DOWNLOADS_DIR:     Path = DATA_ROOT / 'downloads'
DOCS_DOWNLOAD_DIR: Path = DOWNLOADS_DIR / 'docs'
VECTOR_DB_DIR:     Path = DATA_ROOT / 'LUFTDOCS_VECTOR_STORAGE'

# --- Arquivos dentro de DATA/ ---
CONFIG_FILE:     Path = DATA_ROOT / 'config.json'
PERMISSION_PATH: Path = DATA_ROOT / 'permission.json'
ICONS_FILE:      Path = DATA_ROOT / 'icons.json'
DB_FILE:         Path = DATA_ROOT / 'luftdocs.db'

# --- Compatibilidade com código existente ---
DATA_DIR: Path = MODULES_DIR   # muitos pontos do projeto usam DATA_DIR para 'modules'

# Strings úteis
DB_PATH: str = str(DB_FILE)
# DB_URI = f"sqlite:///{DB_FILE}"  # se migrar para SQLAlchemy

# Limites e defaults
MAX_SEARCH_HISTORY = 20
TOP_MOST_ACCESSED  = 7
TOP_MOST_SEARCHED  = 7

# Parâmetros da API de usuário
# Login HASH: login_hash OU login_usuario (Depende se vocÊ estiver usando hash ou texto puro)
USER_API_CREDENTIAL_PARAMS = ["login_hash"]
USER_API_TOKEN_PARAMS      = ["token"]

# Criar pastas no startup (cautela no 'server')
def ensure_data_dirs(create_vector_dir: bool = True, allow_on_server: bool = False) -> None:
    # Evita criar pastas acidentalmente no compartilhamento de produção
    if (DATA_ROOT == DATA_ROOT_SERVER) and not allow_on_server:
        return
    dirs = [
        MODULES_DIR, GLOBAL_DATA_DIR, IMAGES_DIR, VIDEOS_DIR,
        DOWNLOADS_DIR, DOCS_DOWNLOAD_DIR
    ]
    if create_vector_dir:
        dirs.append(VECTOR_DB_DIR)
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)

# Ativos opcionais via env
if os.getenv("CREATE_DATA_DIRS_ON_STARTUP", "0") == "1":
    allow = os.getenv("ALLOW_CREATE_ON_SERVER", "0") == "1"
    ensure_data_dirs(allow_on_server=allow)

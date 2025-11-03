import os
import logging
from pathlib import Path
from urllib.parse import quote_plus
from dotenv import load_dotenv

# Configura o logging BÁSICO primeiro para ver os logs de carga
logging.basicConfig(level=os.getenv("LOG_LEVEL", "INFO"), format="%(asctime)s - %(levelname)s - [%(name)s] - %(message)s")
logger = logging.getLogger(__name__)

# =============================================================================
# 1. CARGA DE AMBIENTE
# =============================================================================

# Diretório raiz do projeto
BASE_DIR: Path = Path(__file__).parent.resolve()

# 1.1. Carrega o .env global (para chaves de API, etc.)
load_dotenv(dotenv_path=BASE_DIR / '.env')

# 1.2. Determina o ambiente ATIVO (Prod ou Local)
#      Default 'Local' se APP_ENV não estiver definida
APP_ENV = os.getenv("APP_ENV", "Local").capitalize()
logger.info(f"Ambiente APP_ENV detectado: '{APP_ENV}'")

# 1.3. Carrega o .env específico do ambiente (SOBRESCREVE o global)
env_file = BASE_DIR / f'.env_{APP_ENV.upper()}'
if env_file.exists():
    load_dotenv(dotenv_path=env_file, override=True)
    logger.info(f"Configuração específica carregada de: {env_file}")
else:
    logger.warning(f"Arquivo de ambiente não encontrado: {env_file}. Usando defaults/global.")
    if APP_ENV == 'Prod':
        logger.error(f"ERRO CRÍTICO: Arquivo .env_PROD não encontrado!")

# =============================================================================
# 2. METADADOS DA APLICAÇÃO (Lidos APÓS carregar .env)
# =============================================================================
APP_NAME = os.getenv("APP_NAME", "luftdocs_web")
APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
FLASK_SECRET_KEY = os.getenv("FLASK_SECRET_KEY", "CHANGE-ME-IN-PROD")
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO") # Log level pode ser por ambiente
BASE_PREFIX = "/luft-docs" # Prefixo da aplicação

# =============================================================================
# 3. CONFIGURAÇÃO DE BANCO DE DADOS (Nova Lógica)
# =============================================================================

def get_database_url(env_name: str) -> str:
    """Monta a URL do banco com base nas variáveis carregadas."""
    db_user = os.getenv("DB_USER")
    db_pass = os.getenv("DB_PASS", "")
    db_host = os.getenv("DB_HOST")
    db_port = os.getenv("DB_PORT")
    db_name = os.getenv("DB_NAME")
    db_driver = os.getenv("DB_DRIVER", "postgresql+psycopg")

    _missing = [k for k, v in {
        "DB_USER": db_user, "DB_HOST": db_host, "DB_PORT": db_port, "DB_NAME": db_name
    }.items() if not v]
    
    if _missing:
        msg = f"Variáveis de banco ausentes para o ambiente '{env_name}': {', '.join(_missing)}"
        logger.error(msg)
        raise RuntimeError(msg)

    # Monta a URL
    encoded_pass = quote_plus(db_pass)
    url = f"{db_driver}://{db_user}:{encoded_pass}@{db_host}:{db_port}/{db_name}"
    
    logger.info(f"Database para '{env_name}' definida: {db_user}@{db_host}:{db_port}/{db_name}")
    return url

#
# ATENÇÃO: Se você mudar a linha abaixo sem saber o que está fazendo,
# a casa cai, o dragão acorda e 500 programadores choram.
# NÃO MEXA POR QUE FUNCIONA.

# URL de Banco de Dados ATIVA
DATABASE_URL: str = get_database_url(APP_ENV)

# =============================================================================
# 4. CAMINHOS DE DADOS (DATA_ROOT) (Nova Lógica)
# =============================================================================

# Define os caminhos PADRÃO para cada ambiente
_DATA_ROOTS_DEFAULT = {
    'Prod': Path(r"\\172.16.200.80\c$\Documents\DATA_LUFTDOCS"),
    'Local': BASE_DIR / 'DATA_LUFTDOCS' # Pasta 'DATA' na raiz do projeto
}

# Seleciona o root padrão para o ambiente atual
default_root_for_env = _DATA_ROOTS_DEFAULT.get(APP_ENV, _DATA_ROOTS_DEFAULT['Local'])

# Permite que o .env (ex: .env_LOCAL) SOBRESCEVA o caminho padrão
# Ex: DATA_ROOT_LOCAL=C:\outra_pasta
DATA_ROOT: Path = Path(os.getenv(f'DATA_ROOT_{APP_ENV.upper()}', str(default_root_for_env)))

logger.info(f"DATA_ROOT ativo para '{APP_ENV}': {DATA_ROOT}")


# =============================================================================
# 5. CONFIGURAÇÕES RESTANTES (Chaves, APIs, Subpastas)
# =============================================================================

# --- Chaves de API (lidas do .env global) ---
AI_KEYS = {
    'GEMINI_API_KEY': os.getenv('GEMINI_API_KEY', ''),
    'GROQ_API_KEY':   os.getenv('GROQ_API_KEY', ''),
    'OPEN_ROUTER_API_KEY': os.getenv('OPEN_ROUTER_API_KEY', ''),
}

# --- API de Usuário (Mapeando Prod/Local para real/local) ---
env_map = {'Prod': 'real', 'Local': 'local'}
active_api_env = env_map.get(APP_ENV, 'local')

_URLS = {
    'local' : "http://127.0.0.1:9006/luft-api/api",
    'render': "https://api-wikidocs.onrender.com/api",
    'real'  : "http://b2bi-apps.luftfarma.com.br/luft-api/api",
}
USER_API_URL = _URLS.get(active_api_env, _URLS['real'])
logger.info(f"USER_API_URL definida para '{active_api_env}': {USER_API_URL}")

# --- Subpastas (agora dinâmicas baseadas no DATA_ROOT) ---
MODULES_DIR:       Path = DATA_ROOT / 'Modules'
GLOBAL_DATA_DIR:   Path = DATA_ROOT / 'Global'
IMAGES_DIR:        Path = DATA_ROOT / 'Img'
VIDEOS_DIR:        Path = DATA_ROOT / 'Videos'
DOWNLOADS_DIR:     Path = DATA_ROOT / 'Downloads'
DOCS_DOWNLOAD_DIR: Path = DOWNLOADS_DIR / 'Docs'
VECTOR_DB_DIR:     Path = BASE_DIR / 'LUFTDOCS_VECTOR_STORAGE'

# --- Arquivos dentro de DATA_ROOT ---
CONFIG_FILE:     Path = DATA_ROOT / 'config.json' # -- OBSOLETO / SALVO EM 'DATA_LUFTDOCS\Archive\Private\permission.json'
PERMISSION_PATH: Path = DATA_ROOT / 'permission.json' # -- OBSOLETO
ICONS_FILE:      Path = DATA_ROOT / 'icons.json'

# --- Compatibilidade com código existente ---
DATA_DIR: Path = MODULES_DIR 

# Limites e defaults
MAX_SEARCH_HISTORY = 20
TOP_MOST_ACCESSED  = 7
TOP_MOST_SEARCHED  = 7

# Parâmetros da API de usuário
USER_API_CREDENTIAL_PARAMS = ["login_hash"]
USER_API_TOKEN_PARAMS      = ["token"]

# Criar pastas no startup
def ensure_data_dirs(create_vector_dir: bool = True, allow_on_prod: bool = False) -> None:
    # Evita criar pastas acidentalmente no compartilhamento de produção
    if (APP_ENV == 'Prod') and not allow_on_prod:
        logger.warning("Ignorando criação de diretórios no ambiente 'Prod'.")
        return
        
    dirs = [
        MODULES_DIR, GLOBAL_DATA_DIR, IMAGES_DIR, VIDEOS_DIR,
        DOWNLOADS_DIR, DOCS_DOWNLOAD_DIR
    ]
    if create_vector_dir:
        dirs.append(VECTOR_DB_DIR)
    
    logger.info(f"Verificando/criando diretórios de dados em: {DATA_ROOT}")
    for d in dirs:
        try:
            d.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error(f"Falha ao criar diretório {d}: {e}")

# Ativos opcionais via env (lidos do .env específico)
if os.getenv("CREATE_DATA_DIRS_ON_STARTUP", "0") == "1":
    allow = os.getenv("ALLOW_CREATE_ON_SERVER", "0") == "1"
    ensure_data_dirs(allow_on_prod=allow)
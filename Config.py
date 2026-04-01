from __future__ import annotations

import logging
import os
from pathlib import Path
from urllib.parse import urlparse
from urllib.parse import quote_plus

from dotenv import load_dotenv


logger = logging.getLogger(__name__)

BASE_DIR: Path = Path(__file__).parent.resolve()
_CAMINHO_DOTENV = BASE_DIR / ".env"

if _CAMINHO_DOTENV.exists():
    load_dotenv(dotenv_path=_CAMINHO_DOTENV, override=False)
else:
    logger.warning("Arquivo .env nao encontrado em %s.", _CAMINHO_DOTENV)


def obterEnv(nomeVariavel: str, valorPadrao: str | None = None) -> str | None:
    valor = os.getenv(nomeVariavel)
    if valor is None:
        return valorPadrao

    valorNormalizado = valor.strip()
    if valorNormalizado == "":
        return valorPadrao
    return valorNormalizado


def obterBoolEnv(nomeVariavel: str, valorPadrao: bool = False) -> bool:
    valor = obterEnv(nomeVariavel)
    if valor is None:
        return valorPadrao
    return valor.lower() in {"1", "true", "t", "yes", "y", "on", "sim"}


def obterIntEnv(nomeVariavel: str, valorPadrao: int) -> int:
    valor = obterEnv(nomeVariavel)
    if valor is None:
        return valorPadrao

    try:
        return int(valor)
    except ValueError:
        logger.warning(
            "Valor invalido para %s: %s. Usando padrao %s.",
            nomeVariavel,
            valor,
            valorPadrao,
        )
        return valorPadrao


def normalizarPrefixo(prefixo: str | None) -> str:
    valor = (prefixo or "/luft-docs").strip()
    if not valor:
        return "/"
    if not valor.startswith("/"):
        valor = f"/{valor}"
    if len(valor) > 1:
        valor = valor.rstrip("/")
    return valor or "/"


def resolverAmbienteAtual() -> str:
    ambienteConfigurado = (obterEnv("APP_ENV", "Local") or "Local").strip().lower()

    if ambienteConfigurado in {"prod", "producao", "production"}:
        return "Prod"
    if ambienteConfigurado in {"local", "dev", "desenvolvimento", "development"}:
        return "Local"

    logger.warning(
        "APP_ENV invalido (%s). Usando ambiente Local.",
        ambienteConfigurado,
    )
    return "Local"


def hostEhLocal(host: str | None) -> bool:
    hostNormalizado = (host or "").strip().lower()
    return hostNormalizado in {"127.0.0.1", "localhost", "::1"}


def urlApontaParaHostLocal(url: str | None) -> bool:
    if not url:
        return False

    try:
        host = urlparse(url).hostname
    except Exception:
        return False

    return hostEhLocal(host)


def montarUrlPostgres() -> str:
    urlDireta = obterEnv("DATABASE_URL") or obterEnv("POSTGRES_URL")
    if urlDireta:
        if resolverAmbienteAtual() == "Prod" and urlApontaParaHostLocal(urlDireta):
            logger.warning(
                "DATABASE_URL/POSTGRES_URL aponta para localhost em ambiente Prod. "
                "Usando configuracao PG_HOST/PG_NAME para montar URL de producao."
            )
        else:
            return urlDireta

    usuario = obterEnv("PG_USER")
    senha = quote_plus(obterEnv("PG_PASS", "") or "")
    host = obterEnv("PG_HOST")
    porta = obterEnv("PG_PORT", "5432") or "5432"
    banco = obterEnv("PG_NAME")
    driver = obterEnv("PG_DRIVER", "postgresql+psycopg") or "postgresql+psycopg"

    ausentes = [
        nome
        for nome, valor in {
            "PG_USER": usuario,
            "PG_HOST": host,
            "PG_NAME": banco,
        }.items()
        if not valor
    ]

    if ausentes:
        mensagem = (
            "Variaveis obrigatorias do PostgreSQL ausentes: "
            + ", ".join(ausentes)
        )
        raise RuntimeError(mensagem)

    return f"{driver}://{usuario}:{senha}@{host}:{porta}/{banco}"


def montarUrlSqlServer() -> str | None:
    urlDireta = obterEnv("SQLSERVER_URL")
    if urlDireta:
        return urlDireta

    usuario = obterEnv("SQL_USER")
    senha = quote_plus(obterEnv("SQL_PASS", "") or "")
    host = obterEnv("SQL_HOST")
    porta = obterEnv("SQL_PORT", "1433") or "1433"
    banco = obterEnv("SQL_DB")
    driver = obterEnv("SQL_DRIVER", "mssql+pyodbc") or "mssql+pyodbc"
    driverOdbc = obterEnv("SS_ODBC_DRIVER", "ODBC Driver 17 for SQL Server")

    ausentes = [
        nome
        for nome, valor in {
            "SQL_USER": usuario,
            "SQL_HOST": host,
            "SQL_DB": banco,
        }.items()
        if not valor
    ]

    if ausentes:
        logger.warning(
            "SQL Server desabilitado; variaveis ausentes: %s.",
            ", ".join(ausentes),
        )
        return None

    return (
        f"{driver}://{usuario}:{senha}@{host}:{porta}/{banco}"
        f"?driver={quote_plus(driverOdbc or 'ODBC Driver 17 for SQL Server')}"
    )


class ConfiguracaoBase:
    nomeAplicacao = obterEnv("APP_NAME", "LuftDocs") or "LuftDocs"
    versaoAplicacao = obterEnv("APP_VERSION", "1.0.0") or "1.0.0"
    chaveSecretaFlask = (
        obterEnv("FLASK_SECRET_KEY", "CHANGE-ME-IN-PROD")
        or "CHANGE-ME-IN-PROD"
    )
    nivelLog = (obterEnv("LOG_LEVEL", "INFO") or "INFO").upper()
    prefixoBase = normalizarPrefixo(obterEnv("BASE_PREFIX", "/luft-docs"))
    mostrarLogsDb = obterBoolEnv("MOSTRAR_LOGS_DB", False)
    schemaPostgres = obterEnv("PG_SEARCH_PATH", "luftdocst") or "luftdocst"
    sqlServerDirectoryDb = (
        obterEnv("SQL_DIRECTORY_DB", "LuftInforma") or "LuftInforma"
    )
    sistemaId = obterIntEnv("SISTEMA_ID", 5)
    debugPermissions = obterBoolEnv("DEBUG_PERMISSIONS", False)
    criarDataDirsNoStartup = obterBoolEnv("CREATE_DATA_DIRS_ON_STARTUP", False)
    permitirCriacaoEmServidor = obterBoolEnv("ALLOW_CREATE_ON_SERVER", False)
    maxSearchHistory = 20
    topMostAccessed = 7
    topMostSearched = 7
    parametrosCredenciaisApiUsuario = ["login_hash"]
    parametrosTokenApiUsuario = ["token"]
    urlsApiUsuario = {
        "local": "http://127.0.0.1:9006/luft-api/api",
        "real": "http://b2bi-apps.luftfarma.com.br/luft-api/api",
    }
    chavesIa = {
        "GEMINI_API_KEY": obterEnv("GEMINI_API_KEY", "") or "",
        "GROQ_API_KEY": obterEnv("GROQ_API_KEY", "") or "",
        "OPEN_ROUTER_API_KEY": obterEnv("OPEN_ROUTER_API_KEY", "") or "",
        "OPENAI_API_KEY": obterEnv("OPENAI_API_KEY", "") or "",
    }

    @classmethod
    def obterDataRootPadrao(cls) -> Path:
        raise NotImplementedError

    @classmethod
    def obterDataRoot(cls) -> Path:
        caminhoConfigurado = obterEnv("DATA_ROOT")
        if caminhoConfigurado:
            caminho = Path(caminhoConfigurado)
            if cls.nomeAmbiente == "Prod":
                caminhoNormalizado = caminhoConfigurado.strip()
                if not caminhoNormalizado.startswith("\\\\") and not caminho.is_absolute():
                    logger.warning(
                        "DATA_ROOT relativo em ambiente Prod (%s). "
                        "Usando caminho padrao de producao.",
                        caminhoConfigurado,
                    )
                    return cls.obterDataRootPadrao()
            return caminho
        return cls.obterDataRootPadrao()

    @classmethod
    def obterUrlPostgres(cls) -> str:
        return montarUrlPostgres()

    @classmethod
    def obterUrlSqlServer(cls) -> str | None:
        return montarUrlSqlServer()

    @classmethod
    def obterUrlApiUsuario(cls) -> str:
        urlDireta = obterEnv("USER_API_URL")
        if urlDireta:
            if cls.nomeAmbiente == "Prod":
                if urlApontaParaHostLocal(urlDireta):
                    logger.warning(
                        "USER_API_URL aponta para localhost em ambiente Prod. "
                        "Usando endpoint de producao configurado em USER_API_AMBIENTE/urlsApiUsuario."
                    )
                else:
                    return urlDireta
            else:
                return urlDireta

        ambienteApi = (
            obterEnv("USER_API_AMBIENTE")
            or ("real" if cls.nomeAmbiente == "Prod" else "local")
        ).lower()
        return cls.urlsApiUsuario.get(ambienteApi, cls.urlsApiUsuario["real"])

    @classmethod
    def obterCaminhoBancoLocal(cls) -> Path:
        caminhoConfigurado = obterEnv("DB_PATH")
        if caminhoConfigurado:
            return Path(caminhoConfigurado)
        return BASE_DIR / "DATA" / "luftdocs.db"


class ConfiguracaoLocal(ConfiguracaoBase):
    nomeAmbiente = "Local"

    @classmethod
    def obterDataRootPadrao(cls) -> Path:
        return BASE_DIR / "DATA_LUFTDOCS"


class ConfiguracaoProducao(ConfiguracaoBase):
    nomeAmbiente = "Prod"

    @classmethod
    def obterDataRootPadrao(cls) -> Path:
        return Path(r"\\172.16.200.80\c$\Documents\DATA_LUFTDOCS")


def obterClasseConfiguracaoAtual():
    return ConfiguracaoProducao if resolverAmbienteAtual() == "Prod" else ConfiguracaoLocal


ConfiguracaoAtual = obterClasseConfiguracaoAtual()

APP_ENV = ConfiguracaoAtual.nomeAmbiente
APP_NAME = ConfiguracaoAtual.nomeAplicacao
APP_VERSION = ConfiguracaoAtual.versaoAplicacao
FLASK_SECRET_KEY = ConfiguracaoAtual.chaveSecretaFlask
LOG_LEVEL = ConfiguracaoAtual.nivelLog
BASE_PREFIX = ConfiguracaoAtual.prefixoBase
MOSTRAR_LOGS_DB = ConfiguracaoAtual.mostrarLogsDb
DATABASE_URL = ConfiguracaoAtual.obterUrlPostgres()
SQLSERVER_URL = ConfiguracaoAtual.obterUrlSqlServer()
SQLSERVER_DIRECTORY_DB = ConfiguracaoAtual.sqlServerDirectoryDb
USER_API_URL = ConfiguracaoAtual.obterUrlApiUsuario()

DATA_ROOT = ConfiguracaoAtual.obterDataRoot()
MODULES_DIR = DATA_ROOT / "Modules"
GLOBAL_DATA_DIR = DATA_ROOT / "Global"
IMAGES_DIR = DATA_ROOT / "Img"
VIDEOS_DIR = DATA_ROOT / "Videos"
DOWNLOADS_DIR = DATA_ROOT / "Downloads"
DOCS_DOWNLOAD_DIR = DOWNLOADS_DIR / "Docs"
VECTOR_DB_DIR = DATA_ROOT / "LUFTDOCS_VECTOR_STORAGE"

CONFIG_FILE = DATA_ROOT / "config.json"
PERMISSION_PATH = DATA_ROOT / "permission.json"
ICONS_FILE = DATA_ROOT / "icons.json"
DATA_DIR = MODULES_DIR
DB_PATH = ConfiguracaoAtual.obterCaminhoBancoLocal()

AI_KEYS = ConfiguracaoAtual.chavesIa
MAX_SEARCH_HISTORY = ConfiguracaoAtual.maxSearchHistory
TOP_MOST_ACCESSED = ConfiguracaoAtual.topMostAccessed
TOP_MOST_SEARCHED = ConfiguracaoAtual.topMostSearched
USER_API_CREDENTIAL_PARAMS = ConfiguracaoAtual.parametrosCredenciaisApiUsuario
USER_API_TOKEN_PARAMS = ConfiguracaoAtual.parametrosTokenApiUsuario
SISTEMA_ID = ConfiguracaoAtual.sistemaId
DEBUG_PERMISSIONS = ConfiguracaoAtual.debugPermissions
POSTGRES_SEARCH_PATH = ConfiguracaoAtual.schemaPostgres


def garantirDiretoriosDados(
    criarDiretorioVetorial: bool = True,
    permitirCriacaoEmProducao: bool = False,
) -> None:
    if APP_ENV == "Prod" and not permitirCriacaoEmProducao:
        logger.warning("Criacao de diretorios ignorada no ambiente Prod.")
        return

    diretorios = [
        MODULES_DIR,
        GLOBAL_DATA_DIR,
        IMAGES_DIR,
        VIDEOS_DIR,
        DOWNLOADS_DIR,
        DOCS_DOWNLOAD_DIR,
        DB_PATH.parent,
    ]
    if criarDiretorioVetorial:
        diretorios.append(VECTOR_DB_DIR)

    for diretorio in diretorios:
        try:
            diretorio.mkdir(parents=True, exist_ok=True)
        except Exception as erro:
            logger.error("Falha ao criar diretorio %s: %s", diretorio, erro)


if ConfiguracaoAtual.criarDataDirsNoStartup:
    garantirDiretoriosDados(
        permitirCriacaoEmProducao=ConfiguracaoAtual.permitirCriacaoEmServidor
    )
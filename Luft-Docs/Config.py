from __future__ import annotations

import logging
import os
from functools import lru_cache
from pathlib import Path
from urllib.parse import urlparse
from urllib.parse import quote_plus

from dotenv import load_dotenv
from luftcore import SqlAlchemyExtension


logger = logging.getLogger(__name__)

BASE_DIR: Path = Path(__file__).parent.resolve()
MONOREPO_ROOT: Path = BASE_DIR.parent
_CAMINHO_DOTENV = MONOREPO_ROOT / ".env"

if _CAMINHO_DOTENV.exists():
    load_dotenv(dotenv_path=_CAMINHO_DOTENV, override=False)
else:
    logger.warning("Arquivo .env nao encontrado em %s.", _CAMINHO_DOTENV)


def obterVersaoMonorepo() -> str:
    caminho_versao = MONOREPO_ROOT / "_version.py"

    try:
        namespace: dict[str, str] = {}
        exec(caminho_versao.read_text(encoding="utf-8"), namespace)
        versao = str(namespace.get("__version__", "")).strip()
        if versao:
            return versao
    except OSError as erro:
        logger.warning("Nao foi possivel ler _version.py em %s: %s", caminho_versao, erro)

    return "0.1.0"


def _removerAspasOpcionais(valor: str | None) -> str | None:
    if valor is None:
        return None

    valorNormalizado = valor.strip()
    if (
        len(valorNormalizado) >= 2
        and valorNormalizado[0] == valorNormalizado[-1]
        and valorNormalizado[0] in {'"', "'"}
    ):
        return valorNormalizado[1:-1].strip()
    return valorNormalizado


def obterEnv(nomeVariavel: str, valorPadrao: str | None = None) -> str | None:
    valor = _removerAspasOpcionais(os.getenv(nomeVariavel))
    if valor is None:
        return valorPadrao

    valorNormalizado = valor.strip()
    if valorNormalizado == "":
        return valorPadrao
    return valorNormalizado


def sincronizarTokenAcessoLuftCore() -> None:
    tokenProjeto = obterEnv("TOKEN_ACESSO")
    tokenFramework = _removerAspasOpcionais(os.getenv("LUFTCORE_TOKEN_ACESSO"))
    if tokenProjeto and not tokenFramework:
        os.environ["LUFTCORE_TOKEN_ACESSO"] = tokenProjeto


def obterPrimeiroEnv(*nomesVariaveis: str, valorPadrao: str | None = None) -> str | None:
    for nomeVariavel in nomesVariaveis:
        valor = obterEnv(nomeVariavel)
        if valor is not None:
            return valor
    return valorPadrao


def obterBoolEnv(nomeVariavel: str, valorPadrao: bool = False) -> bool:
    valor = obterEnv(nomeVariavel)
    if valor is None:
        return valorPadrao
    return valor.lower() in {"1", "true", "t", "yes", "y", "on", "sim"}


def obterPrimeiroBoolEnv(*nomesVariaveis: str, valorPadrao: bool = False) -> bool:
    for nomeVariavel in nomesVariaveis:
        valor = obterEnv(nomeVariavel)
        if valor is not None:
            return valor.lower() in {"1", "true", "t", "yes", "y", "on", "sim"}
    return valorPadrao


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


sincronizarTokenAcessoLuftCore()


def resolverAmbienteAtual() -> str:
    ambienteConfigurado = (obterEnv("APP_ENV", "Local") or "Local").strip().lower()

    if ambienteConfigurado in {"prod", "producao", "production"}:
        return "Prod"
    if ambienteConfigurado in {
        "local",
        "dev",
        "desenvolvimento",
        "development",
        "homolog",
        "homologacao",
        "homologation",
        "hml",
    }:
        return "Local"

    logger.warning(
        "APP_ENV invalido (%s). Usando ambiente Local.",
        ambienteConfigurado,
    )
    return "Local"


def resolverAmbienteVault() -> str:
    ambienteInformado = (obterEnv("AMBIENTE_ATUAL") or "").strip().lower()
    if ambienteInformado in {"desenvolvimento", "dev", "development"}:
        return "desenvolvimento"
    if ambienteInformado in {"homologacao", "homolog", "homologation", "hml"}:
        return "homologacao"
    if ambienteInformado in {"producao", "prod", "production"}:
        return "producao"

    ambienteAplicacao = (obterEnv("APP_ENV", "development") or "development").strip().lower()
    if ambienteAplicacao in {"prod", "producao", "production"}:
        return "producao"
    if ambienteAplicacao in {"homolog", "homologacao", "homologation", "hml"}:
        return "homologacao"
    return "desenvolvimento"


def obterTokenVaultCriptografado() -> str | None:
    tokenVault = obterPrimeiroEnv("VAULT_TOKEN_CRIPTOGRAFADO", "VAULT_TOKEN")
    if tokenVault and tokenVault.startswith(("hvs.", "s.")):
        raise RuntimeError(
            "VAULT_TOKEN deve conter o valor criptografado gerado pela CLI do LuftCore."
        )
    return tokenVault


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
    versaoAplicacao = obterEnv("APP_VERSION_OVERRIDE", obterVersaoMonorepo()) or obterVersaoMonorepo()
    chaveSecretaFlask = (
        obterPrimeiroEnv(
            "FLASK_SECRET_KEY",
            "SECRET_PASSPHRASE",
            valorPadrao="CHANGE-ME-IN-PROD",
        )
        or "CHANGE-ME-IN-PROD"
    )
    nivelLog = (obterEnv("LOG_LEVEL", "INFO") or "INFO").upper()
    prefixoBase = normalizarPrefixo(
        obterPrimeiroEnv("ROUTE_PREFIX", "BASE_PREFIX", valorPadrao="/luft-docs")
    )
    mostrarLogsDb = obterPrimeiroBoolEnv(
        "DB_CONNECT_LOGS",
        "MOSTRAR_LOGS_DB",
        valorPadrao=False,
    )
    schemaPostgres = obterEnv("PG_SEARCH_PATH", "luftdocst") or "luftdocst"
    vaultAddr = obterEnv("VAULT_ADDR")
    vaultNamespace = obterEnv("VAULT_NAMESPACE", "luft") or "luft"
    vaultTokenCriptografado = obterTokenVaultCriptografado()
    tokenAcesso = obterEnv("TOKEN_ACESSO")
    ambienteVaultAtual = resolverAmbienteVault()
    vaultPostgresPath = f"{vaultNamespace}/{ambienteVaultAtual}/postgresql"
    vaultSqlServerPath = f"{vaultNamespace}/{ambienteVaultAtual}/sqlserver"
    driverPostgres = obterPrimeiroEnv("PG_DRIVER", valorPadrao="psycopg") or "psycopg"
    driverSqlServer = (
        obterPrimeiroEnv(
            "SQL_DRIVER",
            "SS_ODBC_DRIVER",
            valorPadrao="ODBC Driver 17 for SQL Server",
        )
        or "ODBC Driver 17 for SQL Server"
    )
    sqlTrustServerCertificate = (
        obterPrimeiroEnv(
            "SQLDB_TRUST_SERVER_CERTIFICATE",
            "SQL_TRUST_SERVER_CERTIFICATE",
            valorPadrao="yes",
        )
        or "yes"
    )
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
    chaveAcessoApiUsuario = obterEnv("API_ACCESS_KEY", "") or ""
    nomeCabecalhoChaveApiUsuario = (
        obterEnv("API_ACCESS_KEY_HEADER", "X-API-Key") or "X-API-Key"
    )
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
    def possuiConfiguracaoVaultCompleta(cls) -> bool:
        return all([cls.vaultAddr, cls.vaultTokenCriptografado, cls.tokenAcesso])

    @classmethod
    def possuiConfiguracaoVaultParcial(cls) -> bool:
        return any([cls.vaultAddr, cls.vaultTokenCriptografado, cls.tokenAcesso]) and not cls.possuiConfiguracaoVaultCompleta()

    @classmethod
    def validarConfiguracaoVault(cls) -> None:
        if not cls.possuiConfiguracaoVaultParcial():
            return

        ausentes = [
            nomeVariavel
            for nomeVariavel, valor in {
                "VAULT_ADDR": cls.vaultAddr,
                "VAULT_TOKEN": cls.vaultTokenCriptografado,
                "TOKEN_ACESSO": cls.tokenAcesso,
            }.items()
            if not valor
        ]
        raise RuntimeError(
            "Configuracao do Vault incompleta. Variaveis ausentes: " + ", ".join(ausentes)
        )

    @classmethod
    @lru_cache(maxsize=1)
    def obterExtensaoPostgres(cls) -> SqlAlchemyExtension | None:
        cls.validarConfiguracaoVault()
        if not cls.possuiConfiguracaoVaultCompleta():
            return None

        parametrosConexao: dict[str, object] = {}
        schemaPostgres = (cls.schemaPostgres or "").strip()
        if schemaPostgres:
            parametrosConexao["options"] = f"-c search_path={schemaPostgres}"

        return SqlAlchemyExtension(
            vault_addr=cls.vaultAddr,
            vault_token_criptografado=cls.vaultTokenCriptografado,
            token_acesso=cls.tokenAcesso,
            caminho_segredo=cls.vaultPostgresPath,
            tipo_banco="postgresql",
            driver_banco=cls.driverPostgres,
            parametros_conexao=parametrosConexao or None,
        )

    @classmethod
    @lru_cache(maxsize=1)
    def obterExtensaoSqlServer(cls) -> SqlAlchemyExtension | None:
        cls.validarConfiguracaoVault()
        if not cls.possuiConfiguracaoVaultCompleta():
            return None

        return SqlAlchemyExtension(
            vault_addr=cls.vaultAddr,
            vault_token_criptografado=cls.vaultTokenCriptografado,
            token_acesso=cls.tokenAcesso,
            caminho_segredo=cls.vaultSqlServerPath,
            tipo_banco="mssql",
            driver_banco=cls.driverSqlServer,
            parametros_conexao={
                "TrustServerCertificate": cls.sqlTrustServerCertificate,
            },
        )

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
        extensaoBanco = cls.obterExtensaoPostgres()
        if extensaoBanco is not None:
            return extensaoBanco.obter_uri_conexao()
        return montarUrlPostgres()

    @classmethod
    def obterUrlSqlServer(cls) -> str | None:
        extensaoBanco = cls.obterExtensaoSqlServer()
        if extensaoBanco is not None:
            return extensaoBanco.obter_uri_conexao()
        return montarUrlSqlServer()

    @classmethod
    def obterUrlApiUsuario(cls) -> str:
        urlDireta = obterEnv("USER_API_URL")
        if urlDireta:
            if cls.nomeAmbiente == "Prod":
                if urlApontaParaHostLocal(urlDireta):
                    logger.warning(
                        "USER_API_URL aponta para localhost em ambiente Prod. "
                        "Ignorando USER_API_URL e resolvendo endpoint via USER_API_AMBIENTE/urlsApiUsuario."
                    )
                else:
                    return urlDireta
            else:
                return urlDireta

        ambienteApi = (
            obterEnv("USER_API_AMBIENTE")
            or ("real" if cls.nomeAmbiente == "Prod" else "local")
        ).strip().lower()
        urlResolvida = cls.urlsApiUsuario.get(ambienteApi, cls.urlsApiUsuario["real"])

        if cls.nomeAmbiente == "Prod" and urlApontaParaHostLocal(urlResolvida):
            logger.warning(
                "USER_API_AMBIENTE=%s aponta para localhost em ambiente Prod. "
                "Usando endpoint 'real' configurado em urlsApiUsuario.",
                ambienteApi,
            )
            return cls.urlsApiUsuario["real"]

        return urlResolvida

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
USER_API_ACCESS_KEY = ConfiguracaoAtual.chaveAcessoApiUsuario
USER_API_ACCESS_KEY_HEADER = ConfiguracaoAtual.nomeCabecalhoChaveApiUsuario

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
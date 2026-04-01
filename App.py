import os
import time
import logging
from typing import Optional

from flask import Flask, g, request, Response, session
from flask.cli import with_appcontext
import click
from sqlalchemy.pool import NullPool

# Importacao do framework LuftCore
from luftcore import LuftCorePackages, LuftUser

try:
    import Config as cfg
except ImportError:
    print("ERRO CRITICO: Nao foi possivel encontrar o arquivo Config.py")
    exit(1)

from Db.Connections import db

from flask_login import LoginManager

from Routes.Auth import Auth_BP
from Routes.Lia import Lia_BP
from Routes.Inicio import Inicio_BP, injetarPermissoesGlobais
from Routes.Modulo import Modulo_BP
from Routes.Submodulo import Submodulo_BP
from Routes.Arquivos import Arquivos_BP
from Routes.Editor import Editor_BP
from Routes.Avaliacao import Avaliacao_BP
from Routes.Permissoes import Permissoes_BP
from Routes.Api import Api_BP
from Routes.Busca import Busca_BP

from prometheus_client import (
    Counter, Histogram, Gauge, Info,
    REGISTRY, generate_latest, CONTENT_TYPE_LATEST
)

# =============================== LOGGING ===============================
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=cfg.LOG_LEVEL,
    format="%(asctime)s - %(levelname)s - [%(name)s] - %(message)s",
)
logger.info(f"Logging inicializado. Nivel configurado: {cfg.LOG_LEVEL}")

# ================================ APP =================================
app = Flask(
    __name__,
    static_folder="static",
    static_url_path=f"{cfg.BASE_PREFIX}/static"
)

app.secret_key = cfg.FLASK_SECRET_KEY
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_COOKIE_PATH"] = cfg.BASE_PREFIX

def ObterUsuarioSessao():
    """
    Recupera os dados da sessao ativa do Flask e os converte para um objeto 
    compativevel com os requisitos do framework LuftCore.

    Returns:
        UsuarioAtivo | None: Objeto representando o usuario logado ou None se nao autenticado.
    """
    if 'user_name' not in session:
        return None
        
    class UsuarioAtivo:
        """Classe efemera para encapsular os dados da sessao em formato de atributos."""
        def __init__(self):
            self.is_authenticated = True
            # Mapeia para os atributos que definimos no LuftUser
            self.Login = session.get('full_name') or session.get('user_name')
            
            # Tenta pegar a sigla ou descricao do grupo configurado no modulo de autenticacao.
            dadosGrupo = session.get('user_group', {})
            self.Grupo = dadosGrupo.get('acronym') or 'Usuario'
            
            # Atributos adicionais de interface que o framework pode tentar ler
            self.email = session.get('email', '')
            self.iniciais = "".join([n[0] for n in self.Login.split()[:2]]).upper() if self.Login else "US"

    return UsuarioAtivo()


def InicializarLuftCore(aplicacaoFlask: Flask) -> LuftCorePackages:
    """
    Inicializa e acopla o framework LuftCore a aplicacao Flask atual.
    
    Configura a integracao do gerenciador de usuarios utilizando o contexto 
    de sessao customizado do LuftDocs e aplica as configuracoes globais de injecao.
    
    Args:
        aplicacaoFlask (Flask): A instancia da aplicacao web Flask.
        
    Returns:
        LuftCorePackages: Instancia configurada do framework de interface.
    """
    gerenciadorUsuario = LuftUser(
        callback_usuario=ObterUsuarioSessao, # <-- Usa o adaptador de sessao customizado
        attr_nome='Login',
        cargo='Grupo'
    )
    
    luftcoreApp = LuftCorePackages(
        app=aplicacaoFlask,
        app_name=cfg.APP_NAME,
        gerenciador_usuario=gerenciadorUsuario,
        inject_theme=True,
        inject_global=True,
        inject_animations=True,
        inject_js=True,
        show_topbar=True,
        show_search=False,
        show_notifications=False,
        show_breadcrumb=True
    )
    
    return luftcoreApp

# Instanciacao do framework
instanciaLuftCore = InicializarLuftCore(app)

# --------------------------- PROMETHEUS -------------------------------
LATENCY_BUCKETS = (
    0.005, 0.01, 0.025, 0.05,
    0.075, 0.1, 0.25, 0.5,
    0.75, 1.0, 2.5, 5.0, 10.0
)

FLASK_REQUEST_STATUS_TOTAL = Counter(
    "flask_request_status_total",
    "Total de requisicoes por classe de status (2xx/3xx/4xx/5xx)",
    ["app_name", "status"]
)

FLASK_REQUEST_TOTAL = Counter(
    "flask_request_total",
    "Total de requisicoes por metodo e path",
    ["app_name", "method", "path"]
)

FLASK_REQUEST_DURATION = Histogram(
    "flask_request_duration_seconds",
    "Duracao das requisicoes (segundos) por metodo e path",
    ["app_name", "method", "path"],
    buckets=LATENCY_BUCKETS
)

FLASK_REQUEST_INPROGRESS = Gauge(
    "flask_request_inprogress",
    "Requisicoes em andamento",
    ["app_name", "method", "path"]
)

FLASK_REQUEST_EXCEPTIONS = Counter(
    "flask_request_exceptions_total",
    "Excecoes nao tratadas por tipo e path",
    ["app_name", "type", "path"]
)

FLASK_RESPONSE_SIZE = Histogram(
    "flask_response_size_bytes",
    "Tamanho da resposta em bytes por path",
    ["app_name", "path"],
    buckets=(0, 200, 500, 1_000, 2_000, 5_000, 10_000, 50_000, 100_000, 1_000_000)
)

FLASK_APP_INFO = Info("flask_app_info", "Informacoes da aplicacao")
FLASK_APP_INFO.info({"app_name": cfg.APP_NAME, "env": cfg.APP_ENV, "version": cfg.APP_VERSION})

def ObterTemplateRota() -> str:
    """
    Retorna o template da rota avaliada ou o caminho literal caso nao possua regra definida.

    Returns:
        str: O padrao da rota da requisicao atual.
    """
    try:
        regraRota = getattr(request, "url_rule", None)
        return regraRota.rule if regraRota else request.path
    except Exception:
        return request.path

def ObterClasseStatus(codigoHTTP: int) -> str:
    """
    Classifica o codigo de retorno HTTP em categorias amplas (ex: 2xx, 4xx).

    Args:
        codigoHTTP (int): O codigo de status HTTP original.

    Returns:
        str: A categoria do status representada como string.
    """
    try:
        return f"{int(codigoHTTP) // 100}xx"
    except Exception:
        return "5xx"

_PATHS_IGNORADOS = {
    f"{cfg.BASE_PREFIX}/metrics",
    "/.well-known/appspecific/com.chrome.devtools.json",
}

@app.before_request
def AntesDaRequisicao():
    """
    Interceptador previo de requisicoes para inicializacao da contagem de metricas.
    Ignora processamento do endpoint de metricas nativo.
    """
    if request.path in _PATHS_IGNORADOS:
        return
    g._t0 = time.perf_counter()
    caminho = ObterTemplateRota()
    FLASK_REQUEST_INPROGRESS.labels(cfg.APP_NAME, request.method, caminho).inc()

@app.after_request
def AposRequisicao(respostaContexto: Response) -> Response:
    """
    Interceptador posterior de requisicoes para avaliacao de metricas e registro de duracao.

    Args:
        respostaContexto (Response): O objeto de resposta Flask gerado pela rota.

    Returns:
        Response: O objeto de resposta original mantido ou incrementado com headers adicionais.
    """
    try:
        if request.path not in _PATHS_IGNORADOS:
            duracao = time.perf_counter() - getattr(g, "_t0", time.perf_counter())
            caminho = ObterTemplateRota()
            metodo = request.method
            codigoStatus = respostaContexto.status_code
            classeStatus = ObterClasseStatus(codigoStatus)

            FLASK_REQUEST_TOTAL.labels(cfg.APP_NAME, metodo, caminho).inc()
            FLASK_REQUEST_STATUS_TOTAL.labels(cfg.APP_NAME, classeStatus).inc()
            FLASK_REQUEST_DURATION.labels(cfg.APP_NAME, metodo, caminho).observe(duracao)

            tamanhoBytes = respostaContexto.calculate_content_length()
            if tamanhoBytes is None:
                try:
                    tamanhoBytes = len(respostaContexto.get_data())
                except Exception:
                    tamanhoBytes = 0
            FLASK_RESPONSE_SIZE.labels(cfg.APP_NAME, caminho).observe(float(tamanhoBytes or 0))

            respostaContexto.headers["X-Process-Time-ms"] = f"{duracao * 1000:.2f}"
    finally:
        if request.path not in _PATHS_IGNORADOS:
            caminho = ObterTemplateRota()
            FLASK_REQUEST_INPROGRESS.labels(cfg.APP_NAME, request.method, caminho).dec()
    return respostaContexto

@app.teardown_request
def EncerrarRequisicao(excecao: Optional[BaseException]):
    """
    Rotina de encerramento de contexto para registro de excecoes nao tratadas nas metricas.

    Args:
        excecao (Optional[BaseException]): Objeto da excecao lancada, se houver.
    """
    if excecao is not None and request.path not in _PATHS_IGNORADOS:
        try:
            caminho = ObterTemplateRota()
            metodo = request.method
            
            FLASK_REQUEST_EXCEPTIONS.labels(cfg.APP_NAME, type(excecao).__name__, caminho).inc()
            FLASK_REQUEST_STATUS_TOTAL.labels(cfg.APP_NAME, "5xx").inc()
            FLASK_REQUEST_TOTAL.labels(cfg.APP_NAME, metodo, caminho).inc()

            duracao = time.perf_counter() - getattr(g, "_t0", time.perf_counter())
            FLASK_REQUEST_DURATION.labels(cfg.APP_NAME, metodo, caminho).observe(duracao)
        except Exception:
            pass


# ---------------------------------------
# Banco de dados (PostgreSQL + SQL Server)
# ---------------------------------------
logger.info(
    "PostgreSQL (Ambiente: %s) -> %s",
    cfg.APP_ENV,
    cfg.DATABASE_URL.split("@")[-1],
)

_sqlalchemy_cfg: dict = {
    "SQLALCHEMY_DATABASE_URI": cfg.DATABASE_URL,
    "SQLALCHEMY_TRACK_MODIFICATIONS": False,
    "SQLALCHEMY_ENGINE_OPTIONS": {
        "poolclass": NullPool,
        "pool_pre_ping": True,
        "connect_args": {"options": "-c search_path=luftdocst"},
    },
}

# SQL Server (permissões + usuários) — opcional; desativado se SS_* não configuradas
if cfg.SQLSERVER_URL:
    _sqlalchemy_cfg["SQLALCHEMY_BINDS"] = {"sqlserver": cfg.SQLSERVER_URL}
    logger.info(
        "Bind SQL Server registrado -> %s",
        cfg.SQLSERVER_URL.split("@")[-1].split("?")[0],
    )
else:
    logger.warning(
        "SQL Server não configurado (SS_* ausentes). "
        "Permissões e busca de usuários no AD estarão indisponíveis."
    )

app.config.update(_sqlalchemy_cfg)

db.init_app(app)

# Cria as tabelas SQL Server (Tb_Permissao, Tb_PermissaoGrupo, etc.) se ainda não existirem.
# Tabelas PostgreSQL já existentes são ignoradas (checkfirst=True por padrão).
if cfg.SQLSERVER_URL:
    try:
        with app.app_context():
            db.create_all()
        logger.info("Tabelas SQL Server verificadas/criadas com sucesso.")
    except Exception as _e_createall:
        logger.warning("Não foi possível criar tabelas SQL Server: %s", _e_createall)

# ---------------------------------------------------------------------------
# flask_login
# ---------------------------------------------------------------------------
login_manager = LoginManager(app)
login_manager.login_view = "Auth.login"          # redireciona para /auth/login
login_manager.login_message = "Acesso restrito. Por favor, faça login."
login_manager.login_message_category = "warning"

@login_manager.user_loader
def _carregar_usuario(user_id: str):
    """
    Reconstrói o UsuarioSistema a partir do cookie de sessão do flask_login.
    Não faz query; usa os dados já armazenados na sessão Flask.
    """
    from flask import session as _session
    from Utils.auth.UsuarioModel import UsuarioSistema
    return UsuarioSistema.da_sessao(_session)

@app.teardown_appcontext
def EncerrarSessaoBanco(excecao=None):
    """
    Desassocia e remove a sessao do banco de dados ao fim do contexto da aplicacao.

    Args:
        excecao (Exception, optional): Possivel excecao que causou o encerramento.
    """
    try:
        db.session.remove()
    except Exception:
        pass

# ---------------------------------------
# CLI: Operacoes de dev
# ---------------------------------------
@click.command("init-db")
@with_appcontext
def InicializarBancoDados():
    """
    Comando CLI responsavel por inicializar as estruturas fisicas do banco de dados.
    """
    click.echo("Processando a inicializacao de tabelas no banco de dados...")
    db.create_all()
    click.echo("Operacao de banco de dados concluida com exito.")

app.cli.add_command(InicializarBancoDados)

# ---------------------------------------
# Blueprints 
# ---------------------------------------
app.context_processor(injetarPermissoesGlobais)

def AjustarPrefixoRota(sufixoRota: str) -> str:
    """
    Realiza a composicao segura entre o prefixo base e a rota pretendida,
    eliminando barras excedentes.

    Args:
        sufixoRota (str): A string do caminho relativo do modulo.

    Returns:
        str: O caminho de rota devidamente formatado.
    """
    if not sufixoRota.startswith("/"): 
        sufixoRota = "/" + sufixoRota
    return (cfg.BASE_PREFIX + sufixoRota).replace("//", "/")

app.register_blueprint(Auth_BP,         url_prefix=AjustarPrefixoRota("/auth"))
app.register_blueprint(Inicio_BP,       url_prefix=AjustarPrefixoRota("/"))
app.register_blueprint(Modulo_BP,       url_prefix=AjustarPrefixoRota("/modulo"))
app.register_blueprint(Submodulo_BP,    url_prefix=AjustarPrefixoRota("/submodulo"))
app.register_blueprint(Arquivos_BP,     url_prefix=AjustarPrefixoRota("/arquivos"))
app.register_blueprint(Editor_BP,       url_prefix=AjustarPrefixoRota("/editor"))
app.register_blueprint(Permissoes_BP,   url_prefix=AjustarPrefixoRota("/permissoes"))
app.register_blueprint(Busca_BP,        url_prefix=AjustarPrefixoRota("/buscar"))
app.register_blueprint(Api_BP,          url_prefix=AjustarPrefixoRota("/api"))
app.register_blueprint(Lia_BP,          url_prefix=AjustarPrefixoRota("/lia"))
app.register_blueprint(Avaliacao_BP,    url_prefix=AjustarPrefixoRota("/avaliacao"))

@app.route(AjustarPrefixoRota("/metrics"))
def ObterMetricas():
    """
    Disponibiliza os dados formatados das metricas para coleta via Prometheus.

    Returns:
        Tuple: Conteudo da resposta com metricas, codigo de status e definicao do content-type.
    """
    return generate_latest(REGISTRY), 200, {"Content-Type": CONTENT_TYPE_LATEST}

@app.route("/.well-known/appspecific/com.chrome.devtools.json")
def IgnorarChromeDevTools():
    return "", 204

@app.route(AjustarPrefixoRota("/healthz"))
def VerificarSaude():
    """
    Endpoint para validacao do status operacional basico do servico.

    Returns:
        Tuple: Dicionario contendo as informacoes do contexto ativo e codigo 200.
    """
    return {"status": "OK", "app": cfg.APP_NAME, "env": cfg.APP_ENV, "version": cfg.APP_VERSION}, 200

# ---------------------------------------
# MAIN
# ---------------------------------------
if __name__ == "__main__":
    portaExecucao = int(os.getenv("PORT", "9100"))
    modoDepuracao = (cfg.APP_ENV == 'Local')
    
    logger.info(f"Iniciando execucao local em http://127.0.0.1:{portaExecucao}{cfg.BASE_PREFIX} (Ambiente: {cfg.APP_ENV}, Debug: {modoDepuracao})")
    
    if modoDepuracao == False:
        print("\n\n" + "!"*70) 
        print(f" ALERTA: EXECUCAO FORA DE PADRAO ".center(70))
        print("!".center(70))
        print(f" MODO ATUAL: '{cfg.APP_ENV}' ".center(70))
        print(" O AMBIENTE NAO CORRESPONDE AO PERFIL LOCAL DE DESENVOLVIMENTO ".center(70))
        print("!".center(70)) 
        print(" CANCELE A EXECUCAO CASO ESTEJA EM INFRAESTRUTURA DE PRODUCAO ".center(70))
        print("!"*70 + "\n\n")
    else:
        print("Execucao iniciada em modo local de desenvolvimento.") 
        
    app.run(host="127.0.0.1", port=portaExecucao, debug=modoDepuracao)
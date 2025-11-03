# app.py — Flask + Prometheus (sem StatsD), PostgreSQL (.env) e NullPool
# Métricas alinhadas ao dashboard "Flask Monitoring":
#  - flask_request_status_total{app_name, status}
#  - flask_request_total{app_name, method, path}
#  - flask_request_duration_seconds{app_name, method, path}  -> gera _bucket/_count/_sum
#  - flask_request_inprogress{app_name, method, path}
#  - flask_request_exceptions_total{app_name, type, path}
#  - flask_response_size_bytes{app_name, path}
#  - flask_app_info{app_name, env, version}

import os
import time
import logging
# from urllib.parse import quote_plus # NÃO É MAIS NECESSÁRIO AQUI
from typing import Optional

from flask import Flask, g, request, Response
from flask.cli import with_appcontext
# from flask_migrate import Migrate  # habilite se for usar migrations
import click
# from dotenv import load_dotenv # NÃO É MAIS NECESSÁRIO AQUI
from sqlalchemy.pool import NullPool

# 1. IMPORTAR CONFIGURAÇÕES CENTRALIZADAS
#    Este import deve vir ANTES de 'Models' e 'db'
try:
    import Config as cfg
except ImportError:
    print("ERRO CRÍTICO: Não foi possível encontrar o arquivo Config.py")
    exit(1)


from Models import db  # mantém seu Models.db (Flask-SQLAlchemy)

# Blueprints (sem mudanças)
from LIA_Services.LIA import ia_bp
from Routes.Core.Main import index_bp, inject_global_permissions
from Routes.Core.Module import modulo_bp
from Routes.Core.SubModule import submodulo_bp
from Routes.Services.Download import download_bp
from Routes.Services.Editor import editor_bp
from Routes.Services.Roteiros import roteiros_bp
from Routes.Services.Evaluation import evaluation_bp
from Routes.API.Permissions import permissions_bp
from Routes.API.API import api_bp
from Routes.Components.Search import search_bp

# ---- Prometheus client (exposição direta) ----
from prometheus_client import (
    Counter, Histogram, Gauge, Info,
    REGISTRY, generate_latest, CONTENT_TYPE_LATEST
)

# =============================== LOGGING ===============================
# load_dotenv() # REMOVIDO
logger = logging.getLogger(__name__)
logging.basicConfig(
    # Usa o LOG_LEVEL do Config.py
    level=cfg.LOG_LEVEL,
    format="%(asctime)s - %(levelname)s - [%(name)s] - %(message)s",
)
logger.info(f"Logging inicializado por App.py. Nível: {cfg.LOG_LEVEL}")


# ============================ APP METADATA =============================
# REMOVIDO - Tudo agora está em Config.py (cfg.APP_NAME, cfg.APP_ENV, cfg.APP_VERSION)

# =============================== PREFIXO ===============================
# REMOVIDO - Tudo agora está em Config.py (cfg.BASE_PREFIX)

# ================================ APP =================================
# Estáticos sob /luft-docs/static
app = Flask(
    __name__,
    static_folder="static",
    # Usa o BASE_PREFIX do Config.py
    static_url_path=f"{cfg.BASE_PREFIX}/static"
)
# Usa a SECRET_KEY do Config.py
app.secret_key = cfg.FLASK_SECRET_KEY
app.config["SESSION_PERMANENT"] = False
# Escopo de cookie limitado ao prefixo (evita colisão com outros apps no mesmo domínio)
app.config["SESSION_COOKIE_PATH"] = cfg.BASE_PREFIX

# --------------------------- PROMETHEUS -------------------------------
# Buckets de latência (ajuste conforme seus SLOs)
LATENCY_BUCKETS = (
    0.005, 0.01, 0.025, 0.05,
    0.075, 0.1, 0.25, 0.5,
    0.75, 1.0, 2.5, 5.0, 10.0
)

FLASK_REQUEST_STATUS_TOTAL = Counter(
    "flask_request_status_total",
    "Total de requisições por classe de status (2xx/3xx/4xx/5xx)",
    ["app_name", "status"]
)

FLASK_REQUEST_TOTAL = Counter(
    "flask_request_total",
    "Total de requisições por método e path",
    ["app_name", "method", "path"]
)

# >>> HISTOGRAMA QUE GERA _sum/_count/_bucket <<<
FLASK_REQUEST_DURATION = Histogram(
    "flask_request_duration_seconds",
    "Duração das requisições (segundos) por método e path",
    ["app_name", "method", "path"],
    buckets=LATENCY_BUCKETS
)

FLASK_REQUEST_INPROGRESS = Gauge(
    "flask_request_inprogress",
    "Requisições em andamento",
    ["app_name", "method", "path"]
)

FLASK_REQUEST_EXCEPTIONS = Counter(
    "flask_request_exceptions_total",
    "Exceções não tratadas por tipo e path",
    ["app_name", "type", "path"]
)

FLASK_RESPONSE_SIZE = Histogram(
    "flask_response_size_bytes",
    "Tamanho da resposta em bytes por path",
    ["app_name", "path"],
    buckets=(0, 200, 500, 1_000, 2_000, 5_000, 10_000, 50_000, 100_000, 1_000_000)
)

# Info da aplicação (sinal de vida/versão/ambiente)
FLASK_APP_INFO = Info("flask_app_info", "Informações da aplicação")
# Usa os valores do Config.py
FLASK_APP_INFO.info({"app_name": cfg.APP_NAME, "env": cfg.APP_ENV, "version": cfg.APP_VERSION})

def _route_template() -> str:
    """Retorna o template da rota (ex.: '/api/<id>') ou o path literal."""
    try:
        rule = getattr(request, "url_rule", None)
        return rule.rule if rule else request.path
    except Exception:
        return request.path

def _status_class(code: int) -> str:
    try:
        return f"{int(code) // 100}xx"
    except Exception:
        return "5xx"

@app.before_request
def _before():
    # Não medir o próprio /metrics para evitar loops
    # Usa o BASE_PREFIX do Config.py
    if request.path == f"{cfg.BASE_PREFIX}/metrics":
        return
    g._t0 = time.perf_counter()
    path = _route_template()
    # Usa o APP_NAME do Config.py
    FLASK_REQUEST_INPROGRESS.labels(cfg.APP_NAME, request.method, path).inc()

@app.after_request
def _after(response: Response):
    try:
        # Usa o BASE_PREFIX do Config.py
        if request.path != f"{cfg.BASE_PREFIX}/metrics":
            dt = time.perf_counter() - getattr(g, "_t0", time.perf_counter())
            path = _route_template()
            method = request.method
            status_code = response.status_code
            status_cls = _status_class(status_code)

            # Totais (Usa o APP_NAME do Config.py)
            FLASK_REQUEST_TOTAL.labels(cfg.APP_NAME, method, path).inc()
            FLASK_REQUEST_STATUS_TOTAL.labels(cfg.APP_NAME, status_cls).inc()

            # Duração (gera _sum/_count/_bucket)
            FLASK_REQUEST_DURATION.labels(cfg.APP_NAME, method, path).observe(dt)

            # Tamanho da resposta
            size = response.calculate_content_length()
            if size is None:
                try:
                    size = len(response.get_data())
                except Exception:
                    size = 0
            FLASK_RESPONSE_SIZE.labels(cfg.APP_NAME, path).observe(float(size or 0))

            # Header auxiliar p/ debug (não influencia as métricas)
            response.headers["X-Process-Time-ms"] = f"{dt * 1000:.2f}"
    finally:
        # Usa o BASE_PREFIX e APP_NAME do Config.py
        if request.path != f"{cfg.BASE_PREFIX}/metrics":
            path = _route_template()
            FLASK_REQUEST_INPROGRESS.labels(cfg.APP_NAME, request.method, path).dec()
    return response

@app.teardown_request
def _teardown(exc: Optional[BaseException]):
    # Se uma exceção não tratada ocorreu, contabilizamos como 5xx
    if exc is not None and request.path != f"{cfg.BASE_PREFIX}/metrics": # Usa config
        try:
            path = _route_template()
            method = request.method
            # Usa o APP_NAME do Config.py
            FLASK_REQUEST_EXCEPTIONS.labels(cfg.APP_NAME, type(exc).__name__, path).inc()

            # Também incrementa classe 5xx e totais (garantia)
            FLASK_REQUEST_STATUS_TOTAL.labels(cfg.APP_NAME, "5xx").inc()
            FLASK_REQUEST_TOTAL.labels(cfg.APP_NAME, method, path).inc()

            # Duração aproximada até o erro (também alimenta _sum/_count/_bucket)
            dt = time.perf_counter() - getattr(g, "_t0", time.perf_counter())
            FLASK_REQUEST_DURATION.labels(cfg.APP_NAME, method, path).observe(dt)
        except Exception:
            pass


# ---------------------------------------
# Configuração de Banco (PostgreSQL)
# ---------------------------------------

# ========= BLOCO INTEIRO REMOVIDO E SUBSTITUÍDO =========
# DATABASE_URL = os.getenv("DATABASE_URL")
# if not DATABASE_URL:
#     DB_DRIVER = ...
#     ... (toda a lógica de montagem da URL) ...
#     DATABASE_URL = f"{DB_DRIVER}://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"
#
# logger.info("Conectando ao PostgreSQL: %s", DATABASE_URL.split('@')[-1])
# =======================================================

# Nova lógica (lê direto do Config.py)
logger.info(
    "Conectando ao PostgreSQL (Ambiente: %s) -> %s",
    cfg.APP_ENV,
    cfg.DATABASE_URL.split('@')[-1] # Oculta user/pass do log
)

app.config.update(
    # Usa a DATABASE_URL do Config.py
    SQLALCHEMY_DATABASE_URI=cfg.DATABASE_URL,
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    SQLALCHEMY_ENGINE_OPTIONS={
        "poolclass": NullPool,
        "pool_pre_ping": True,
        "connect_args": {
            "options": "-c search_path=luftdocst" # Mantido
        }
    }
)

db.init_app(app)
# migrate = Migrate(app, db)  # habilite se desejar migrations

@app.teardown_appcontext
def shutdown_session(exception=None):
    try:
        db.session.remove()
    except Exception:
        pass

# ---------------------------------------
# CLI: criar tabelas rapidamente (dev)
# ---------------------------------------
@click.command("init-db")
@with_appcontext
def init_db_command():
    click.echo("Verificando/criando tabelas...")
    db.create_all()
    click.echo("Banco pronto.")
app.cli.add_command(init_db_command)

# ---------------------------------------
# Blueprints (TODOS sob BASE_PREFIX)
# ---------------------------------------
app.context_processor(inject_global_permissions)

def p(suffix: str) -> str:
    """Concatena BASE + sufixo garantindo barra única."""
    if not suffix.startswith("/"): suffix = "/" + suffix
    # Usa o BASE_PREFIX do Config.py
    return (cfg.BASE_PREFIX + suffix).replace("//", "/")

# Blueprints SEM url_prefix interno -> definimos subpaths explícitos sob BASE_PREFIX
app.register_blueprint(index_bp,       url_prefix=p("/"))
app.register_blueprint(modulo_bp,      url_prefix=p("/modulo"))
app.register_blueprint(submodulo_bp,   url_prefix=p("/submodule"))
app.register_blueprint(download_bp,    url_prefix=p("/download"))
app.register_blueprint(editor_bp,      url_prefix=p("/editor"))
app.register_blueprint(permissions_bp, url_prefix=p("/permissions"))
app.register_blueprint(search_bp,      url_prefix=p("/search"))
app.register_blueprint(api_bp,         url_prefix=p("/api"))              # /luft-docs/api
app.register_blueprint(roteiros_bp,    url_prefix=p("/api/roteiros"))     # /luft-docs/api/roteiros
app.register_blueprint(ia_bp,          url_prefix=p("/lia"))
app.register_blueprint(evaluation_bp,  url_prefix=p("/evaluation"))


# Endpoint /metrics (Prometheus) — AGORA com prefixo
@app.route(p("/metrics"))
def metrics():
    return generate_latest(REGISTRY), 200, {"Content-Type": CONTENT_TYPE_LATEST}

# Health check — AGORA com prefixo
# (Corrigido: estava apontando para /metrics também)
@app.route(p("/healthz"))
def healthz():
    return {"status": "OK", "app": cfg.APP_NAME, "env": cfg.APP_ENV, "version": cfg.APP_VERSION}, 200


# ---------------------------------------
# MAIN (dev)
# ---------------------------------------
if __name__ == "__main__":
    # A porta ainda pode ser definida por var de ambiente (ex: Docker, Gunicorn)
    port = int(os.getenv("PORT", "9100"))
    # Debug é ativado se o ambiente for 'Local'
    is_debug = (cfg.APP_ENV == 'Local')
    print(f"Iniciando servidor de desenvolvimento em http://127.0.0.1:{port}/luft-docs/ (Ambiente: {cfg.APP_ENV}, Debug: {is_debug})")
    logger.info(f"Iniciando servidor de desenvolvimento em http://127.0.0.1:{port}/luft-docs/ (Ambiente: {cfg.APP_ENV}, Debug: {is_debug})")
    app.run(host="127.0.0.1", port=port, debug=is_debug)
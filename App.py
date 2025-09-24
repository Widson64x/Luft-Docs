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
from urllib.parse import quote_plus
from typing import Optional

from flask import Flask, g, request, Response
from flask.cli import with_appcontext
# from flask_migrate import Migrate  # habilite se for usar migrations
import click
from dotenv import load_dotenv
from sqlalchemy.pool import NullPool

from models import db  # mantém seu models.db (Flask-SQLAlchemy)

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
load_dotenv()
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s - %(levelname)s - [%(name)s] - %(message)s",
)

# ============================ APP METADATA =============================
APP_NAME    = os.getenv("APP_NAME", "luftdocs_web")
APP_ENV     = os.getenv("APP_ENV", "dev")
APP_VERSION = os.getenv("APP_VERSION", "1.0.0")

# =============================== PREFIXO ===============================
# >>> Prefixo OBRIGATÓRIO para TODAS as rotas da aplicação <<<
BASE_PREFIX = "/luft-docs"

# ================================ APP =================================
# Estáticos sob /luft-docs/static
app = Flask(
    __name__,
    static_folder="static",
    static_url_path=f"{BASE_PREFIX}/static"
)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "CHANGE-ME")
app.config["SESSION_PERMANENT"] = False
# Escopo de cookie limitado ao prefixo (evita colisão com outros apps no mesmo domínio)
app.config["SESSION_COOKIE_PATH"] = BASE_PREFIX

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
FLASK_APP_INFO.info({"app_name": APP_NAME, "env": APP_ENV, "version": APP_VERSION})

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
    if request.path == f"{BASE_PREFIX}/metrics":
        return
    g._t0 = time.perf_counter()
    path = _route_template()
    FLASK_REQUEST_INPROGRESS.labels(APP_NAME, request.method, path).inc()

@app.after_request
def _after(response: Response):
    try:
        if request.path != f"{BASE_PREFIX}/metrics":
            dt = time.perf_counter() - getattr(g, "_t0", time.perf_counter())
            path = _route_template()
            method = request.method
            status_code = response.status_code
            status_cls = _status_class(status_code)

            # Totais
            FLASK_REQUEST_TOTAL.labels(APP_NAME, method, path).inc()
            FLASK_REQUEST_STATUS_TOTAL.labels(APP_NAME, status_cls).inc()

            # Duração (gera _sum/_count/_bucket)
            FLASK_REQUEST_DURATION.labels(APP_NAME, method, path).observe(dt)

            # Tamanho da resposta
            size = response.calculate_content_length()
            if size is None:
                try:
                    size = len(response.get_data())
                except Exception:
                    size = 0
            FLASK_RESPONSE_SIZE.labels(APP_NAME, path).observe(float(size or 0))

            # Header auxiliar p/ debug (não influencia as métricas)
            response.headers["X-Process-Time-ms"] = f"{dt * 1000:.2f}"
    finally:
        if request.path != f"{BASE_PREFIX}/metrics":
            path = _route_template()
            FLASK_REQUEST_INPROGRESS.labels(APP_NAME, request.method, path).dec()
    return response

@app.teardown_request
def _teardown(exc: Optional[BaseException]):
    # Se uma exceção não tratada ocorreu, contabilizamos como 5xx
    if exc is not None and request.path != f"{BASE_PREFIX}/metrics":
        try:
            path = _route_template()
            method = request.method
            FLASK_REQUEST_EXCEPTIONS.labels(APP_NAME, type(exc).__name__, path).inc()

            # Também incrementa classe 5xx e totais (garantia)
            FLASK_REQUEST_STATUS_TOTAL.labels(APP_NAME, "5xx").inc()
            FLASK_REQUEST_TOTAL.labels(APP_NAME, method, path).inc()

            # Duração aproximada até o erro (também alimenta _sum/_count/_bucket)
            dt = time.perf_counter() - getattr(g, "_t0", time.perf_counter())
            FLASK_REQUEST_DURATION.labels(APP_NAME, method, path).observe(dt)
        except Exception:
            pass


# ---------------------------------------
# Configuração de Banco (PostgreSQL)
# ---------------------------------------
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    DB_DRIVER = os.getenv("DB_DRIVER", "postgresql+psycopg2")
    DB_USER   = os.getenv("DB_USER")
    DB_PASS   = quote_plus(os.getenv("DB_PASS", ""))
    DB_HOST   = os.getenv("DB_HOST", "localhost")
    DB_PORT   = os.getenv("DB_PORT", "5432")
    DB_NAME   = os.getenv("DB_NAME")

    _missing = [k for k, v in {
        "DB_USER": DB_USER, "DB_HOST": DB_HOST, "DB_PORT": DB_PORT, "DB_NAME": DB_NAME
    }.items() if not v]
    if _missing:
        raise RuntimeError(f"Variáveis ausentes no .env: {', '.join(_missing)}")

    DATABASE_URL = f"{DB_DRIVER}://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

logger.info("Conectando ao PostgreSQL: %s", DATABASE_URL.split('@')[-1])

app.config.update(
    SQLALCHEMY_DATABASE_URI=DATABASE_URL,
    SQLALCHEMY_TRACK_MODIFICATIONS=False,
    SQLALCHEMY_ENGINE_OPTIONS={
        "poolclass": NullPool,
        "pool_pre_ping": True,
        "connect_args": {
            "options": "-c search_path=luftdocst"
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
    return (BASE_PREFIX + suffix).replace("//", "/")

# Blueprints SEM url_prefix interno -> definimos subpaths explícitos sob BASE_PREFIX
app.register_blueprint(index_bp,       url_prefix=p("/"))
app.register_blueprint(modulo_bp,      url_prefix=p("/modulo"))
app.register_blueprint(submodulo_bp,   url_prefix=p("/submodule"))
app.register_blueprint(download_bp,    url_prefix=p("/download"))
app.register_blueprint(editor_bp,      url_prefix=p("/editor"))
app.register_blueprint(permissions_bp, url_prefix=p("/permissions"))
app.register_blueprint(search_bp,      url_prefix=p("/search"))
app.register_blueprint(api_bp,         url_prefix=p("/api"))               # /luft-docs/api
app.register_blueprint(roteiros_bp,    url_prefix=p("/api/roteiros"))      # /luft-docs/api/roteiros
app.register_blueprint(ia_bp,          url_prefix=p("/lia"))
app.register_blueprint(evaluation_bp,  url_prefix=p("/evaluation"))


# Endpoint /metrics (Prometheus) — AGORA com prefixo
@app.route(p("/metrics"))
def metrics():
    return generate_latest(REGISTRY), 200, {"Content-Type": CONTENT_TYPE_LATEST}

# Health check — AGORA com prefixo
@app.route(p("/metrics"))
def healthz():
    return {"status": "OK", "app": APP_NAME, "env": APP_ENV, "version": APP_VERSION}, 200


# ---------------------------------------
# MAIN (dev)
# ---------------------------------------
if __name__ == "__main__":
    # Ajuste PORT para casar com seu Nginx/upstream (ex.: 9100)
    app.run(host="127.0.0.1", port=int(os.getenv("PORT", "9100")), debug=True)

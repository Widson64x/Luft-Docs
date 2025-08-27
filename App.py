# app.py — Acesso ao banco via PostgreSQL (.env) e NullPool

import os
import logging
from urllib.parse import quote_plus

from flask import Flask
from flask.cli import with_appcontext
from flask_migrate import Migrate
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

# ---------------------------------------
# App
# ---------------------------------------
load_dotenv()
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "CHANGE-ME")
app.config["SESSION_PERMANENT"] = False

# ---------------------------------------
# Configuração de Banco (PostgreSQL)
# Prioriza DATABASE_URL; senão, monta via variáveis separadas
# ---------------------------------------
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    DB_DRIVER = os.getenv("DB_DRIVER", "postgresql+psycopg2")  # psycopg2 por padrão
    DB_USER   = os.getenv("DB_USER")
    DB_PASS   = quote_plus(os.getenv("DB_PASS", ""))
    DB_HOST   = os.getenv("DB_HOST", "localhost")
    DB_PORT   = os.getenv("DB_PORT", "5432")  # porta padrão do Postgres
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
        "poolclass": NullPool, # Quebra a query quando o pool está vazio
        "pool_pre_ping": True, # Verifica conexões antes de usá-las
        "connect_args": { 
            "options": "-c search_path=luftdocst"  # <- Acessa o Schema do 'luftdocst' no banco
        }
    }
)

# ---------------------------------------
# DB / Migrations
# ---------------------------------------
db.init_app(app)
# migrate = Migrate(app, db) - Migrar banco de dados

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
# Blueprints
# ---------------------------------------
app.context_processor(inject_global_permissions)
app.register_blueprint(index_bp)
app.register_blueprint(modulo_bp, url_prefix="/modulo")
app.register_blueprint(submodulo_bp, url_prefix="/submodule")
app.register_blueprint(download_bp, url_prefix="/download")
app.register_blueprint(editor_bp, url_prefix="/editor")
app.register_blueprint(permissions_bp, url_prefix="/permissions")
app.register_blueprint(search_bp, url_prefix="/search")
app.register_blueprint(api_bp, url_prefix="/api")
app.register_blueprint(roteiros_bp)
app.register_blueprint(ia_bp)
app.register_blueprint(evaluation_bp)

if __name__ == "__main__":
    app.run(debug=True)

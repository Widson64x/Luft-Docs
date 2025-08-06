# app.py (Caminho do Banco de Dados Corrigido)

import click
from flask import Flask
from flask.cli import with_appcontext
import os # Importe o módulo

from models import db

# Seus imports de rotas existentes
from Routes.core.main import index_bp, inject_global_permissions 
from Routes.core.module import modulo_bp
from Routes.core.submodule import submodulo_bp
from Routes.services.download import download_bp
from Routes.services.editor import editor_bp
from Routes.api.permissions import permissions_bp 
from Routes.components.search import search_bp
from Routes.api.api_index import api_bp
from Routes.services.ia import ia_bp
from Routes.services.evaluation import evaluation_bp

app = Flask(__name__)
app.secret_key = 'LUFT@123'
app.config['SESSION_PERMANENT'] = False

# --- CONFIGURAÇÃO DO BANCO DE DADOS (CORRIGIDO) ---

# Define o caminho base do projeto
basedir = os.path.abspath(os.path.dirname(__file__))
# Define o caminho completo para o seu banco de dados na pasta DATA
db_path = os.path.join(basedir, 'DATA', 'luftdocs.db')

# 2. Configure a URI do banco de dados para apontar para o arquivo correto.
# O prefixo 'sqlite:///' é necessário para caminhos absolutos no Windows.
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + db_path

# Exemplo para quando você for migrar para SQL Server (mantenha comentado):
# app.config['SQLALCHEMY_DATABASE_URI'] = 'mssql+pyodbc://user:password@your_server_name/your_database_name?driver=ODBC+Driver+17+for+SQL+Server'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# 3. Inicialize o objeto 'db' com a sua aplicação.
db.init_app(app)

# --- COMANDO PARA INICIALIZAR O BANCO DE DADOS ---
@click.command('init-db')
@with_appcontext
def init_db_command():
    """Cria todas as tabelas do banco de dados se elas não existirem."""
    click.echo('Verificando e criando tabelas do banco de dados se necessário...')
    db.create_all()
    click.echo('Banco de dados pronto.')
    
app.cli.add_command(init_db_command)

app.context_processor(inject_global_permissions)
app.register_blueprint(index_bp)
app.register_blueprint(modulo_bp, url_prefix='/modulo')
app.register_blueprint(submodulo_bp, url_prefix='/submodule')
app.register_blueprint(download_bp, url_prefix='/download')
app.register_blueprint(editor_bp, url_prefix='/editor')
app.register_blueprint(permissions_bp, url_prefix='/permissions')
app.register_blueprint(search_bp, url_prefix='/search')
app.register_blueprint(api_bp, url_prefix='/api')
app.register_blueprint(ia_bp)
app.register_blueprint(evaluation_bp)

if __name__ == "__main__":
    app.run(debug=True)

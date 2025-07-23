# app.py

from flask import Flask, session, redirect, url_for, request
import click  # <-- Adicionar esta importação
from flask.cli import with_appcontext 

# Seus imports existentes
from utils import database_utils
from routes.main import index_bp
from routes.module import modulo_bp
from routes.submodule import submodulo_bp
from routes.download import download_bp
from routes.editor import editor_bp
from routes.permissions import permissions_bp
from routes.search import search_bp
from routes.learning_plan import learning_plan_bp
from routes.api_index import api_bp


app = Flask(__name__)
app.secret_key = 'LUFT@123'
app.config['SESSION_PERMANENT'] = False

# --- COMANDO PARA INICIALIZAR O BANCO DE DADOS ---
# Esta função permite que você execute 'flask init-db' no terminal.
# É a maneira correta de executar tarefas de configuração do app.
@click.command('init-db')
@with_appcontext
def init_db_command():
    """Limpa dados existentes e cria novas tabelas no banco de dados."""
    database_utils.init_db()
    click.echo('Banco de dados inicializado com sucesso.')

# Adiciona o novo comando ao seu objeto 'app' do Flask
app.cli.add_command(init_db_command)


# Registra a função de fechar o DB ao final de cada requisição
database_utils.init_app(app)

# --- REGISTRO DOS SEUS BLUEPRINTS (permanece o mesmo) ---
app.register_blueprint(index_bp)
app.register_blueprint(modulo_bp, url_prefix='/modulo')
app.register_blueprint(submodulo_bp, url_prefix='/submodule')
app.register_blueprint(download_bp, url_prefix='/download')
app.register_blueprint(editor_bp, url_prefix='/editor')
app.register_blueprint(permissions_bp, url_prefix='/permissions')
app.register_blueprint(search_bp, url_prefix='/search')
app.register_blueprint(learning_plan_bp, url_for='/learning-plan')
app.register_blueprint(api_bp)


if __name__ == "__main__":
    app.run(debug=True)

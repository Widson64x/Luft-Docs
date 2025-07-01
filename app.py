# app.py

from flask import Flask, session, redirect, url_for, request
from routes.main import index_bp
from routes.module import modulo_bp
from routes.submodule import submodulo_bp
from routes.download import download_bp
from routes.search import busca_bp  
from routes.editor import editor_bp
from routes.permissions import permissions_bp

app = Flask(__name__)
app.secret_key = 'LUFT@123'
app.config['SESSION_PERMANENT'] = False  # Assegura cookie de sessão não-permanente
# 1) Registrar blueprint do index em primeiro lugar
app.register_blueprint(index_bp, url_prefix='')

# 2) Registrar blueprints de módulos e demais, sem prefixo
app.register_blueprint(modulo_bp, url_prefix='')
app.register_blueprint(submodulo_bp, url_prefix='')
app.register_blueprint(download_bp, url_prefix='/download')
app.register_blueprint(busca_bp, url_prefix='')
app.register_blueprint(editor_bp)
app.register_blueprint(permissions_bp)


# 3) Guard global: se não estiver logado, redireciona para index
@app.before_request
def verifica_sessao_global():
    # Permitir index.index (página de login / token)
    if request.endpoint == 'index.index':
        return None
    
    # Permitir arquivos estáticos (css, js, imagens)
    if request.endpoint and request.endpoint.startswith('static'):
        return None
    
    # Se não tiver session válida, volta para o login
    if 'user_name' not in session or 'user_id' not in session:
        return redirect(url_for('index.index'))

if __name__ == "__main__":
    app.run(debug=True)

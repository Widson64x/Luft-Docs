# app.py

from flask import Flask, session, redirect, url_for, request
from routes.main import index_bp
from routes.module import modulo_bp
from routes.submodule import submodulo_bp
from routes.download import download_bp
from routes.editor import editor_bp
from routes.permissions import permissions_bp

app = Flask(__name__)
app.secret_key = 'LUFT@123'
app.config['SESSION_PERMANENT'] = False  # Assegura cookie de sessão não-permanente

app.register_blueprint(index_bp)  # A rota principal responde em '/'
app.register_blueprint(modulo_bp, url_prefix='/modulo')
app.register_blueprint(submodulo_bp, url_prefix='/submodule') # <-- AQUI ESTÁ A CORREÇÃO!
app.register_blueprint(download_bp, url_prefix='/download')
app.register_blueprint(editor_bp, url_prefix='/editor')
app.register_blueprint(permissions_bp, url_prefix='/permissions')

if __name__ == "__main__":
    app.run(debug=True)

# routes/download.py

from flask import Blueprint, send_from_directory, current_app, request, abort, session
import os
from Utils.auth.auth_utils import login_required
from Config import DOCS_DOWNLOAD_DIR

# Registre este blueprint em app.py com url_prefix='/download'
download_bp = Blueprint('download', __name__)

@download_bp.route('/', methods=['GET'])
@login_required
def download_pela_raiz():
    """
    GET /download?token=<TOKEN>&download=<NOME_DO_ARQUIVO>
    """
    # 1) Parâmetro obrigatório
    nome_arquivo = request.args.get('download', '').strip()
    if not nome_arquivo:
        abort(400, "Parâmetro 'download' vazio")

    # 2) Bloqueia path traversal simples
    if '..' in nome_arquivo or nome_arquivo.startswith(('/', '\\')):
        abort(400, "Nome de arquivo inválido")
        
        #
        # "Onde você pensa que vai com esse '../' ?"
        #
        # Esta linha impede que o usuário peça "..\..\..\..\Windows\System32"
        # e leve o servidor para casa.
        #
        
    # 3) Monta caminho para data/downloads/docs
    pasta_download = DOCS_DOWNLOAD_DIR
    if not os.path.isdir(pasta_download):
        current_app.logger.error(f"Pasta de downloads não existe: {pasta_download}")
        abort(500, "Erro de configuração do servidor")

    # 4) Verifica existência
    caminho = os.path.join(pasta_download, nome_arquivo)
    if not os.path.isfile(caminho):
        current_app.logger.warning(f"Arquivo não encontrado: {caminho}")
        abort(404)

    # 5) Serve o arquivo
    return send_from_directory(pasta_download, nome_arquivo, as_attachment=True)

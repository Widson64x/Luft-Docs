# routes/download.py

from flask import Blueprint, abort, send_from_directory

from Services.ServicoDownload import ServicoDownload
from Utils.auth.Autenticacao import LoginObrigatorio

# Registre este blueprint em app.py com url_prefix='/download'
download_bp = Blueprint('download', __name__)
servicoDownload = ServicoDownload()

@download_bp.route('/', methods=['GET'])
@LoginObrigatorio
def baixarPelaRaiz():
    """Recebe a solicitacao HTTP de download e delega a validacao ao service."""
    resposta_servico = servicoDownload.obterRespostaDownload()
    if resposta_servico["tipo"] == "erro":
        abort(resposta_servico["codigo"], resposta_servico["mensagem"])
    return send_from_directory(
        resposta_servico["pasta"],
        resposta_servico["nome_arquivo"],
        as_attachment=True,
    )

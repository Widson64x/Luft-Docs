# routes/download.py

from flask import Blueprint, send_from_directory
from flask_login import login_required
from luftcore.extensions.flask_extension import render_404, render_500, render_no_permission

from Services.PermissaoService import ChavesPermissao, RequerPermissao
from Services.ServicoDownload import ServicoDownload

Arquivos_BP = Blueprint('Arquivos', __name__)
servicoDownload = ServicoDownload()


def _renderizar_erro_http(codigo, mensagem):
    if codigo == 403:
        return render_no_permission(mensagem)
    if codigo == 404:
        return render_404(mensagem)
    return render_500(mensagem)

@Arquivos_BP.route('/', methods=['GET'])
@RequerPermissao(ChavesPermissao.VISUALIZAR_MODULOS)
@login_required
def baixarPelaRaiz():
    """Recebe a solicitacao HTTP de download e delega a validacao ao service."""
    resposta_servico = servicoDownload.obterRespostaDownload()
    if resposta_servico["tipo"] == "erro":
        return _renderizar_erro_http(
            resposta_servico["codigo"],
            resposta_servico["mensagem"],
        )
    return send_from_directory(
        resposta_servico["pasta"],
        resposta_servico["nome_arquivo"],
        as_attachment=True,
    )

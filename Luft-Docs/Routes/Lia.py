from flask import Blueprint, jsonify, request
from flask_login import login_required
from luftcore.extensions.flask_extension import require_ajax

from Services.PermissaoService import ChavesPermissao, RequerPermissao
from Services.LIAServices.ServicoLIA import ServicoLIA

Lia_BP = Blueprint('Lia', __name__)
servicoLia = ServicoLIA()


def _resolverRespostaServico(resposta_servico):
    return jsonify(resposta_servico["dados"]), resposta_servico["codigo"]

@Lia_BP.route('/api/obter-lista-modulos', methods=['GET'])
@RequerPermissao(ChavesPermissao.VISUALIZAR_LIA)
@login_required
@require_ajax
def listarModulosDisponiveisApi():
    return _resolverRespostaServico(servicoLia.obterRespostaListaModulos())

@Lia_BP.route('/api/perguntar', methods=['POST'])
@RequerPermissao(ChavesPermissao.VISUALIZAR_LIA)
@login_required
@require_ajax
def perguntarLiaApi():
    return _resolverRespostaServico(
        servicoLia.obterRespostaPergunta(request.get_json(silent=True))
    )
    
@Lia_BP.route('/api/registrar-feedback', methods=['POST'])
@RequerPermissao(ChavesPermissao.VISUALIZAR_LIA)
@login_required
@require_ajax
def registrarFeedbackApi():
    return _resolverRespostaServico(
        servicoLia.obterRespostaRegistroFeedback(request.get_json(silent=True))
    )
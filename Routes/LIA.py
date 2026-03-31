from flask import Blueprint, jsonify, request

from Services.LIAServices.ServicoLIA import ServicoLIA
from Utils.auth.Autenticacao import LoginObrigatorio

ia_bp = Blueprint('ia_bp', __name__)
servicoLia = ServicoLIA()


def _resolverRespostaServico(resposta_servico):
    return jsonify(resposta_servico["dados"]), resposta_servico["codigo"]

@ia_bp.route('/api/get_modules_list', methods=['GET'])
@LoginObrigatorio
def listarModulosDisponiveisApi():
    return _resolverRespostaServico(servicoLia.obterRespostaListaModulos())

@ia_bp.route('/api/ask_llm', methods=['POST'])
@LoginObrigatorio
def perguntarLiaApi():
    return _resolverRespostaServico(
        servicoLia.obterRespostaPergunta(request.get_json(silent=True))
    )
    
@ia_bp.route('/api/submit_feedback', methods=['POST'])
@LoginObrigatorio
def registrarFeedbackApi():
    return _resolverRespostaServico(
        servicoLia.obterRespostaRegistroFeedback(request.get_json(silent=True))
    )
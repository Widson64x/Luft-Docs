from flask import Blueprint, jsonify, request

from Services.LIAServices.ServicoLIA import ServicoLIA
from Utils.auth.Autenticacao import LoginObrigatorio

Lia_BP = Blueprint('Lia', __name__)
servicoLia = ServicoLIA()


def _resolverRespostaServico(resposta_servico):
    return jsonify(resposta_servico["dados"]), resposta_servico["codigo"]

@Lia_BP.route('/api/obter-lista-modulos', methods=['GET'])
@LoginObrigatorio
def listarModulosDisponiveisApi():
    return _resolverRespostaServico(servicoLia.obterRespostaListaModulos())

@Lia_BP.route('/api/perguntar', methods=['POST'])
@LoginObrigatorio
def perguntarLiaApi():
    return _resolverRespostaServico(
        servicoLia.obterRespostaPergunta(request.get_json(silent=True))
    )
    
@Lia_BP.route('/api/registrar-feedback', methods=['POST'])
@LoginObrigatorio
def registrarFeedbackApi():
    return _resolverRespostaServico(
        servicoLia.obterRespostaRegistroFeedback(request.get_json(silent=True))
    )
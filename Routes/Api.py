from flask import Blueprint, jsonify, request

from Services.ServicoApiModulos import ServicoApiModulos
from Services.ServicoBusca import ServicoBusca
from Services.ServicoRoteiros import ServicoRoteiros
from Utils.auth.Autenticacao import LoginObrigatorio

Api_BP = Blueprint('Api', __name__)
servicoApiModulos = ServicoApiModulos()
servicoBusca = ServicoBusca()
servicoRoteiros = ServicoRoteiros()

@Api_BP.route('/obter-lista-modulos', methods=['GET'])
@LoginObrigatorio
def listarModulos():
    """
    Endpoint da API para buscar e paginar módulos.
    Aceita os parâmetros de query: ?search=... & page=...
    """
    return jsonify(
        servicoApiModulos.obterRespostaListaModulos(
            consulta=request.args.get('search', '').lower().strip(),
            pagina=request.args.get('page', 1, type=int),
            token=request.args.get('token'),
        )
    )


@Api_BP.get('/buscar')
@LoginObrigatorio
def buscarNaApi():
    return jsonify(
        servicoBusca.obterResultadosBuscaApi(
            consulta=request.args.get('q', '').strip(),
            filtro_modulo=request.args.get('module', '').strip(),
            token=request.args.get('token', '').strip(),
        )
    )


@Api_BP.route('/listar-recomendacoes')
@LoginObrigatorio
def listarRecomendacoes():
    return jsonify(servicoBusca.obterRecomendacoes(request.args.get('token', '')))


@Api_BP.route('/listar-autocomplete')
@LoginObrigatorio
def listarAutocomplete():
    return jsonify(servicoBusca.obterAutocomplete(request.args.get('q', '')))


@Api_BP.route('/roteiros', methods=['POST'])
@LoginObrigatorio
def criarRoteiro():
    resposta, codigo = servicoRoteiros.criarRoteiro(request.get_json() or {})
    return jsonify(resposta), codigo


@Api_BP.route('/roteiros/vincular', methods=['POST'])
@LoginObrigatorio
def vincularRoteiroAModulo():
    resposta, codigo = servicoRoteiros.vincularRoteiroAModulo(request.get_json() or {})
    return jsonify(resposta), codigo


@Api_BP.route('/roteiros/<int:roteiro_id>', methods=['GET'])
@LoginObrigatorio
def obterRoteiro(roteiro_id):
    resposta, codigo = servicoRoteiros.obterRoteiro(roteiro_id)
    return jsonify(resposta), codigo


@Api_BP.route('/roteiros/<int:roteiro_id>', methods=['PUT'])
@LoginObrigatorio
def atualizarRoteiro(roteiro_id):
    resposta, codigo = servicoRoteiros.atualizarRoteiro(
        roteiro_id,
        request.get_json() or {},
    )
    return jsonify(resposta), codigo


@Api_BP.route('/roteiros/<int:roteiro_id>', methods=['DELETE'])
@LoginObrigatorio
def excluirRoteiro(roteiro_id):
    resposta, codigo = servicoRoteiros.excluirRoteiro(roteiro_id)
    return jsonify(resposta), codigo
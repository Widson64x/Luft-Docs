from flask import Blueprint, current_app, jsonify, request
from flask_login import login_required
from luftcore.extensions.flask_extension import api_error, require_ajax

from Services.PermissaoService import ChavesPermissao, RequerPermissao
from Services.ServicoApiModulos import ServicoApiModulos
from Services.ServicoBusca import ServicoBusca
from Services.ServicoRoteiros import ServicoRoteiros

Api_BP = Blueprint('Api', __name__)
servicoApiModulos = ServicoApiModulos()
servicoBusca = ServicoBusca()
servicoRoteiros = ServicoRoteiros()


def _responder_json(callback, mensagem_erro: str):
    try:
        retorno = callback()
        if isinstance(retorno, tuple):
            payload, codigo = retorno
            return jsonify(payload), codigo
        return jsonify(retorno)
    except Exception as exc:
        current_app.logger.exception("[Api] %s: %s", mensagem_erro, exc)
        return api_error("Falha interna ao processar a requisição.", status=500)

@Api_BP.route('/obter-lista-modulos', methods=['GET'])
@RequerPermissao(ChavesPermissao.VISUALIZAR_MODULOS)
@login_required
@require_ajax
def listarModulos():
    """
    Endpoint da API para buscar e paginar módulos.
    Aceita os parâmetros de query: ?search=... & page=...
    """
    return _responder_json(
        lambda: servicoApiModulos.obterRespostaListaModulos(
            consulta=request.args.get('search', '').lower().strip(),
            pagina=request.args.get('page', 1, type=int),
            token=request.args.get('token'),
        ),
        'Erro ao listar módulos da página inicial',
    )


@Api_BP.route('/arvore-modulos', methods=['GET'])
@RequerPermissao(ChavesPermissao.VISUALIZAR_MODULOS)
@login_required
@require_ajax
def listarArvoreModulos():
    return _responder_json(
        servicoApiModulos.obterRespostaArvoreModulos,
        'Erro ao listar árvore de módulos',
    )


@Api_BP.get('/buscar')
@RequerPermissao(ChavesPermissao.VISUALIZAR_MODULOS)
@login_required
@require_ajax
def buscarNaApi():
    return _responder_json(
        lambda: servicoBusca.obterResultadosBuscaApi(
            consulta=request.args.get('q', '').strip(),
            filtro_modulo=request.args.get('module', '').strip(),
            token=request.args.get('token', '').strip(),
        ),
        'Erro ao executar busca na API',
    )


@Api_BP.route('/listar-recomendacoes')
@RequerPermissao(ChavesPermissao.VISUALIZAR_MODULOS)
@login_required
@require_ajax
def listarRecomendacoes():
    return _responder_json(
        lambda: servicoBusca.obterRecomendacoes(request.args.get('token', '')),
        'Erro ao listar recomendações',
    )


@Api_BP.route('/listar-autocomplete')
@RequerPermissao(ChavesPermissao.VISUALIZAR_MODULOS)
@login_required
@require_ajax
def listarAutocomplete():
    return _responder_json(
        lambda: servicoBusca.obterAutocomplete(request.args.get('q', '')),
        'Erro ao listar autocomplete',
    )


@Api_BP.route('/roteiros', methods=['POST'])
@RequerPermissao(ChavesPermissao.EDITAR_ROTEIROS)
@login_required
@require_ajax
def criarRoteiro():
    return _responder_json(
        lambda: servicoRoteiros.criarRoteiro(request.get_json() or {}),
        'Erro ao criar roteiro',
    )


@Api_BP.route('/roteiros/vincular', methods=['POST'])
@RequerPermissao(ChavesPermissao.EDITAR_ROTEIROS)
@login_required
@require_ajax
def vincularRoteiroAModulo():
    return _responder_json(
        lambda: servicoRoteiros.vincularRoteiroAModulo(request.get_json() or {}),
        'Erro ao vincular roteiro a módulo',
    )


@Api_BP.route('/roteiros/<int:roteiro_id>', methods=['GET'])
@RequerPermissao(ChavesPermissao.EDITAR_ROTEIROS)
@login_required
@require_ajax
def obterRoteiro(roteiro_id):
    return _responder_json(
        lambda: servicoRoteiros.obterRoteiro(roteiro_id),
        'Erro ao obter roteiro',
    )


@Api_BP.route('/roteiros/<int:roteiro_id>', methods=['PUT'])
@RequerPermissao(ChavesPermissao.EDITAR_ROTEIROS)
@login_required
@require_ajax
def atualizarRoteiro(roteiro_id):
    return _responder_json(
        lambda: servicoRoteiros.atualizarRoteiro(
            roteiro_id,
            request.get_json() or {},
        ),
        'Erro ao atualizar roteiro',
    )


@Api_BP.route('/roteiros/<int:roteiro_id>', methods=['DELETE'])
@RequerPermissao(ChavesPermissao.EDITAR_ROTEIROS)
@login_required
@require_ajax
def excluirRoteiro(roteiro_id):
    return _responder_json(
        lambda: servicoRoteiros.excluirRoteiro(roteiro_id),
        'Erro ao excluir roteiro',
    )
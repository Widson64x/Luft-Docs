# routes/Roteiros.py
from flask import Blueprint, jsonify, request

from Services.ServicoRoteiros import ServicoRoteiros
from Utils.auth.Autenticacao import LoginObrigatorio

# Blueprint SEM prefixo interno; o app.py define /luft-docs/api/roteiros
roteiros_bp = Blueprint('roteiros', __name__)
servicoRoteiros = ServicoRoteiros()


# ============== CREATE =======================================================
@roteiros_bp.route('/', methods=['POST'])
@LoginObrigatorio
def criarRoteiro():
    resposta, codigo = servicoRoteiros.criarRoteiro(request.get_json() or {})
    return jsonify(resposta), codigo


# ============== LINK TO MODULE(S) ===========================================
@roteiros_bp.route('/vincular', methods=['POST'])
@LoginObrigatorio
def vincularRoteiroAModulo():
    resposta, codigo = servicoRoteiros.vincularRoteiroAModulo(request.get_json() or {})
    return jsonify(resposta), codigo


# ============== READ (DETAIL) ===============================================
@roteiros_bp.route('/<int:roteiro_id>', methods=['GET'])
@LoginObrigatorio
def obterRoteiro(roteiro_id):
    resposta, codigo = servicoRoteiros.obterRoteiro(roteiro_id)
    return jsonify(resposta), codigo


# ============== UPDATE =======================================================
@roteiros_bp.route('/<int:roteiro_id>', methods=['PUT'])
@LoginObrigatorio
def atualizarRoteiro(roteiro_id):
    resposta, codigo = servicoRoteiros.atualizarRoteiro(
        roteiro_id,
        request.get_json() or {},
    )
    return jsonify(resposta), codigo


# ============== DELETE =======================================================
@roteiros_bp.route('/<int:roteiro_id>', methods=['DELETE'])
@LoginObrigatorio
def excluirRoteiro(roteiro_id):
    resposta, codigo = servicoRoteiros.excluirRoteiro(roteiro_id)
    return jsonify(resposta), codigo

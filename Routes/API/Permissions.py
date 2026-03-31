# permissions.py (Refatorado com SQLAlchemy)

from flask import Blueprint, abort, jsonify, redirect, render_template, url_for

from Services.ServicoPermissao import ServicoPermissao
from Utils.auth.Autenticacao import LoginObrigatorio

permissions_bp = Blueprint('permissions', __name__, url_prefix='/permissions')
servicoPermissao = ServicoPermissao()

@permissions_bp.route('/check/<permission_name>', methods=['GET'])
@LoginObrigatorio
def verificarPermissao(permission_name):
    return jsonify(servicoPermissao.obterRespostaVerificacao(permission_name))

@permissions_bp.route('/my-group', methods=['GET'])
@LoginObrigatorio
def obterMeuGrupo():
    return jsonify(servicoPermissao.obterRespostaMeuGrupo())

@permissions_bp.route('/', methods=['GET', 'POST'])
@LoginObrigatorio
def gerenciarPermissoes():
    resposta_servico = servicoPermissao.obterRespostaGerenciamento()
    if resposta_servico["tipo"] == "erro":
        abort(resposta_servico["codigo"], description=resposta_servico["mensagem"])
    if resposta_servico["tipo"] == "redirecionar":
        return redirect(
            url_for(
                resposta_servico["endpoint"],
                **resposta_servico.get("parametros", {}),
            )
        )
    return render_template(
        resposta_servico["template"],
        **resposta_servico.get("contexto", {}),
    )

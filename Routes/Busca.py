# /routes/search.py
from flask import Blueprint, jsonify, render_template, request
from flask_login import login_required

from Services.PermissaoService import ChavesPermissao, RequerPermissao
from Services.ServicoBusca import ServicoBusca

Busca_BP = Blueprint('Busca', __name__)
servicoBusca = ServicoBusca()

@Busca_BP.route('/')
@RequerPermissao(ChavesPermissao.VISUALIZAR_MODULOS)
@login_required
def exibirBusca():
    return render_template(
        'Pages/PesquisarModulos.html',
        **servicoBusca.obterContextoBusca(
            consulta=request.args.get('q', '').strip(),
            filtro_modulo=request.args.get('module', '').strip(),
            token=request.args.get('token', '').strip(),
        ),
    )

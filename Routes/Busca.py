# /routes/search.py
from flask import Blueprint, jsonify, render_template, request

from Services.ServicoBusca import ServicoBusca
from Utils.auth.Autenticacao import LoginObrigatorio

Busca_BP = Blueprint('Busca', __name__)
servicoBusca = ServicoBusca()

@Busca_BP.route('/')
@LoginObrigatorio
def exibirBusca():
    return render_template(
        'Pages/PesquisarModulos.html',
        **servicoBusca.obterContextoBusca(
            consulta=request.args.get('q', '').strip(),
            filtro_modulo=request.args.get('module', '').strip(),
            token=request.args.get('token', '').strip(),
        ),
    )

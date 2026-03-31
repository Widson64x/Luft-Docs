# /routes/search.py
from flask import Blueprint, jsonify, render_template, request

from Services.ServicoBusca import ServicoBusca
from Utils.auth.Autenticacao import LoginObrigatorio

search_bp = Blueprint('search', __name__)
servicoBusca = ServicoBusca()

@search_bp.route('/')
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

# --------- API JSON (palette / integrações) ----------

@search_bp.get('/api/search')
@LoginObrigatorio
def buscarNaApi():
    return jsonify(
        servicoBusca.obterResultadosBuscaApi(
            consulta=request.args.get('q', '').strip(),
            filtro_modulo=request.args.get('module', '').strip(),
            token=request.args.get('token', '').strip(),
        )
    )

@search_bp.route('/api/recommendations')
@LoginObrigatorio
def listarRecomendacoes():
    return jsonify(servicoBusca.obterRecomendacoes(request.args.get('token', '')))

@search_bp.route('/api/autocomplete')
@LoginObrigatorio
def listarAutocomplete():
    return jsonify(servicoBusca.obterAutocomplete(request.args.get('q', '')))

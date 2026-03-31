# routes/api.py

from flask import Blueprint, jsonify, request

from Services.ServicoApiModulos import ServicoApiModulos
from Utils.auth.Autenticacao import LoginObrigatorio

# Blueprint para a API
api_bp = Blueprint('api', __name__, url_prefix='/api')
servicoApiModulos = ServicoApiModulos()

@api_bp.route('/modules', methods=['GET'])
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
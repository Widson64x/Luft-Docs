# Routes/core/main.py (Refatorado)

from flask import Blueprint, jsonify, render_template, request, send_from_directory, session

from Config import IMAGES_DIR, VIDEOS_DIR
from Services.ServicoPrincipal import ServicoPrincipal
from Utils.auth.Autenticacao import LoginObrigatorio

index_bp = Blueprint("index", __name__)
servicoPrincipal = ServicoPrincipal()

@index_bp.context_processor
def injetarPermissoesGlobais():
    return servicoPrincipal.obterPermissoesGlobais()

@index_bp.route('/data/img/<path:nome_arquivo>')
def servirImagemDinamica(nome_arquivo):
    return send_from_directory(IMAGES_DIR, nome_arquivo)

@index_bp.route('/data/videos/<path:nome_arquivo>')
def servirVideo(nome_arquivo):
    return send_from_directory(VIDEOS_DIR, nome_arquivo)

@index_bp.route('/', methods=['GET'])
def exibirInicio():
    resultado_autenticacao = servicoPrincipal.autenticarRequisicaoInicial()
    if resultado_autenticacao is not True:
        return resultado_autenticacao
    return render_template("Index.html", **servicoPrincipal.obterContextoPaginaInicial())

@index_bp.route('/mapa', methods=['GET'])
@LoginObrigatorio
def exibirMapaConhecimento():
    return render_template(
        "Components/MapaModulos.html",
        **servicoPrincipal.obterContextoMapaConhecimento(),
    )

@index_bp.route('/report-bug', methods=['POST'])
@LoginObrigatorio
def reportarBug():
    resposta, codigo = servicoPrincipal.registrarReporte(
        session.get("user_id"),
        request.get_json(silent=True) or {},
    )
    return jsonify(resposta), codigo

@index_bp.route('/logout')
@LoginObrigatorio
def encerrarSessao():
    servicoPrincipal.encerrarSessaoAtual()
    return render_template("Auth/Logout.html")

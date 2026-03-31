# Routes/core/main.py (Refatorado)

from flask import Blueprint, jsonify, render_template, request, send_from_directory, session

from Config import IMAGES_DIR, VIDEOS_DIR
from Services.ServicoPrincipal import ServicoPrincipal
from Utils.auth.Autenticacao import LoginObrigatorio

Inicio_BP = Blueprint("Inicio", __name__)
servicoPrincipal = ServicoPrincipal()

@Inicio_BP.context_processor
def injetarPermissoesGlobais():
    return servicoPrincipal.obterPermissoesGlobais()

@Inicio_BP.route('/data/img/<path:nome_arquivo>')
def servirImagemDinamica(nome_arquivo):
    return send_from_directory(IMAGES_DIR, nome_arquivo)

@Inicio_BP.route('/data/videos/<path:nome_arquivo>')
def servirVideo(nome_arquivo):
    # O 'send_from_directory' é usado para servir arquivos estáticos de forma segura, garantindo que apenas arquivos dentro do diretório especificado sejam acessíveis.
    return send_from_directory(VIDEOS_DIR, nome_arquivo)

@Inicio_BP.route('/', methods=['GET'])
def exibirInicio():
    resultado_autenticacao = servicoPrincipal.autenticarRequisicaoInicial()
    if resultado_autenticacao is not True:
        return resultado_autenticacao
    return render_template("Index.html", **servicoPrincipal.obterContextoPaginaInicial())

@Inicio_BP.route('/mapa-conhecimento', methods=['GET'])
@LoginObrigatorio
def exibirMapaConhecimento():
    return render_template(
        "Components/MapaModulos.html",
        **servicoPrincipal.obterContextoMapaConhecimento(),
    )

@Inicio_BP.route('/reportar-problema', methods=['POST'])
@LoginObrigatorio
def reportarBug():
    resposta, codigo = servicoPrincipal.registrarReporte(
        session.get("user_id"), 
        request.get_json(silent=True) or {},
    )
    return jsonify(resposta), codigo

@Inicio_BP.route('/encerrar-sessao')
@LoginObrigatorio
def encerrarSessao():
    servicoPrincipal.encerrarSessaoAtual()
    return render_template("Auth/Logout.html")

# Routes/core/main.py (Refatorado)

from flask import Blueprint, current_app, jsonify, render_template, request, send_from_directory, session

from flask_login import login_required
from luftcore.extensions.flask_extension import api_error, require_ajax

from Config import IMAGES_DIR, VIDEOS_DIR
from Services.PermissaoService import ChavesPermissao, RequerPermissao
from Services.ServicoPrincipal import ServicoPrincipal

Inicio_BP = Blueprint("Inicio", __name__)
servicoPrincipal = ServicoPrincipal()

@Inicio_BP.context_processor
def injetarPermissoesGlobais():
    return servicoPrincipal.obterPermissoesGlobais()

@Inicio_BP.route('/data/img/<path:nome_arquivo>')
@RequerPermissao(ChavesPermissao.VISUALIZAR_MODULOS)
@login_required
def servirImagemDinamica(nome_arquivo):
    return send_from_directory(IMAGES_DIR, nome_arquivo)

@Inicio_BP.route('/data/videos/<path:nome_arquivo>')
@RequerPermissao(ChavesPermissao.VISUALIZAR_MODULOS)
@login_required
def servirVideo(nome_arquivo):
    # O 'send_from_directory' é usado para servir arquivos estáticos de forma segura, garantindo que apenas arquivos dentro do diretório especificado sejam acessíveis.
    return send_from_directory(VIDEOS_DIR, nome_arquivo)

@Inicio_BP.route('/', methods=['GET'])
def exibirInicio():
    resultado_auth = servicoPrincipal.autenticarRequisicaoInicial()
    if resultado_auth is not True:
        return resultado_auth
    return render_template("Index.html", **servicoPrincipal.obterContextoPaginaInicial())

@Inicio_BP.route('/mapa-conhecimento', methods=['GET'])
@RequerPermissao(ChavesPermissao.VISUALIZAR_MODULOS)
@login_required
def exibirMapaConhecimento():
    return render_template(
        "Components/MapaModulos.html",
        **servicoPrincipal.obterContextoMapaConhecimento(),
    )

@Inicio_BP.route('/reportar-problema', methods=['POST'])
@RequerPermissao(ChavesPermissao.VISUALIZAR_MODULOS)
@login_required
@require_ajax
def reportarBug():
    try:
        resposta, codigo = servicoPrincipal.registrarReporte(
            session.get("user_id"), 
            request.get_json(silent=True) or {},
        )
        return jsonify(resposta), codigo
    except Exception as exc:
        current_app.logger.exception("[Inicio] Erro ao registrar feedback: %s", exc)
        return api_error("Falha ao registrar o feedback.", status=500)

@Inicio_BP.route('/encerrar-sessao')
@login_required
def encerrarSessao():
    servicoPrincipal.encerrarSessaoAtual()
    return render_template("Auth/Logout.html")

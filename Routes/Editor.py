from flask import Blueprint, jsonify, redirect, render_template, url_for
from flask_login import login_required
from luftcore.extensions.flask_extension import require_ajax, render_404, render_500, render_no_permission

from Services.PermissaoService import ChavesPermissao, RequerPermissao
from Services.ServicoEditor import ServicoEditor

Editor_BP = Blueprint('Editor', __name__)
servicoEditor = ServicoEditor()


def _renderizar_erro_http(codigo, mensagem):
    if codigo == 403:
        return render_no_permission(mensagem)
    if codigo == 404:
        return render_404(mensagem)
    return render_500(mensagem)


def _resolverRespostaServico(resposta_servico):
    if resposta_servico["tipo"] == "erro":
        return _renderizar_erro_http(
            resposta_servico["codigo"],
            resposta_servico["mensagem"],
        )
    if resposta_servico["tipo"] == "redirecionar":
        return redirect(
            url_for(
                resposta_servico["endpoint"],
                **resposta_servico.get("parametros", {}),
            )
        )
    if resposta_servico["tipo"] == "json":
        return jsonify(resposta_servico["dados"]), resposta_servico.get("codigo", 200)
    return render_template(
        resposta_servico["template"],
        **resposta_servico.get("contexto", {}),
    )


@Editor_BP.route('/')
@RequerPermissao(ChavesPermissao.VISUALIZAR_EDITOR)
@login_required
def exibirPainelEditor():
    return _resolverRespostaServico(servicoEditor.obterRespostaPainelEditor())


@Editor_BP.route('/novo', methods=['GET', 'POST'])
@RequerPermissao(ChavesPermissao.CRIAR_MODULOS)
@login_required
def criarModulo():
    return _resolverRespostaServico(servicoEditor.obterRespostaCriacaoModulo())


@Editor_BP.route('/modulo/<mid>', methods=['GET', 'POST'])
@RequerPermissao(ChavesPermissao.EDITAR_MODULOS)
@login_required
def editarModulo(mid):
    return _resolverRespostaServico(servicoEditor.obterRespostaEdicaoModulo(mid))


@Editor_BP.route('/excluir/<mid>', methods=['POST'])
@RequerPermissao(ChavesPermissao.EXCLUIR_MODULOS)
@login_required
def excluirModulo(mid):
    return _resolverRespostaServico(servicoEditor.obterRespostaExclusaoModulo(mid))


@Editor_BP.route('/pendencias')
@RequerPermissao(ChavesPermissao.APROVAR_MODULOS)
@login_required
def exibirPendencias():
    return _resolverRespostaServico(servicoEditor.obterRespostaPendencias())


@Editor_BP.route('/aprovar/<mid>', methods=['POST'])
@RequerPermissao(ChavesPermissao.APROVAR_MODULOS)
@login_required
def aprovarModulo(mid):
    return _resolverRespostaServico(servicoEditor.obterRespostaAprovacaoModulo(mid))


@Editor_BP.route('/rejeitar/<mid>', methods=['POST'])
@RequerPermissao(ChavesPermissao.REJEITAR_MODULOS)
@login_required
def rejeitarModulo(mid):
    return _resolverRespostaServico(servicoEditor.obterRespostaRejeicaoModulo(mid))


@Editor_BP.route('/historico/<mid>', methods=['GET', 'POST'])
@RequerPermissao(ChavesPermissao.VERSIONAR_MODULOS)
@login_required
def exibirHistoricoModulo(mid):
    return _resolverRespostaServico(servicoEditor.obterRespostaHistoricoModulo(mid))


@Editor_BP.route('/opcoes', methods=['GET'])
@RequerPermissao(ChavesPermissao.VISUALIZAR_EDITOR)
@login_required
@require_ajax
def listarOpcoesEditor():
    return _resolverRespostaServico(servicoEditor.obterRespostaOpcoesEditor())


@Editor_BP.route('/upload-imagem/<modulo_id>', methods=['POST'])
@RequerPermissao(ChavesPermissao.VISUALIZAR_EDITOR)
@login_required
@require_ajax
def enviarImagemModulo(modulo_id):
    return _resolverRespostaServico(servicoEditor.obterRespostaUploadImagem(modulo_id))


@Editor_BP.route('/upload-video/<modulo_id>', methods=['POST'])
@RequerPermissao(ChavesPermissao.VISUALIZAR_EDITOR)
@login_required
@require_ajax
def enviarVideoModulo(modulo_id):
    return _resolverRespostaServico(servicoEditor.obterRespostaUploadVideo(modulo_id))


@Editor_BP.route('/upload-anexo', methods=['POST'])
@RequerPermissao(ChavesPermissao.VISUALIZAR_EDITOR)
@login_required
@require_ajax
def enviarAnexoModulo():
    return _resolverRespostaServico(servicoEditor.obterRespostaUploadAnexo())


@Editor_BP.route('/submodulos')
@RequerPermissao(ChavesPermissao.EDITAR_MODULOS)
@login_required
def listarSubmodulos():
    return _resolverRespostaServico(servicoEditor.obterRespostaListagemSubmodulos())


@Editor_BP.route('/excluir-submodulo', methods=['POST'])
@RequerPermissao(ChavesPermissao.EDITAR_MODULOS)
@login_required
def excluirSubmodulo():
    return _resolverRespostaServico(servicoEditor.obterRespostaExclusaoSubmodulo())


@Editor_BP.route('/criar-submodulo', methods=['POST'])
@RequerPermissao(ChavesPermissao.EDITAR_MODULOS)
@login_required
def criarSubmodulo():
    return _resolverRespostaServico(servicoEditor.obterRespostaCriacaoSubmodulo())


@Editor_BP.route('/submodulo/<path:submodulo_path>', methods=['GET', 'POST'])
@RequerPermissao(ChavesPermissao.EDITAR_MODULOS)
@login_required
def editarSubmodulo(submodulo_path):
    return _resolverRespostaServico(servicoEditor.obterRespostaEdicaoSubmodulo(submodulo_path))


@Editor_BP.route('/diff-pendente')
@RequerPermissao(ChavesPermissao.APROVAR_MODULOS)
@login_required
@require_ajax
def obterDiffPendente():
    return _resolverRespostaServico(servicoEditor.obterRespostaDiffPendente())


@Editor_BP.route('/diff-historico')
@RequerPermissao(ChavesPermissao.VERSIONAR_MODULOS)
@login_required
@require_ajax
def obterDiffHistorico():
    return _resolverRespostaServico(servicoEditor.obterRespostaDiffHistorico())


@Editor_BP.route('/obter-conteudo-historico')
@RequerPermissao(ChavesPermissao.VERSIONAR_MODULOS)
@login_required
@require_ajax
def obterConteudoHistorico():
    return _resolverRespostaServico(servicoEditor.obterRespostaConteudoHistorico())


@Editor_BP.route('/upload-anexo-submodulo', methods=['POST'])
@RequerPermissao(ChavesPermissao.EDITAR_MODULOS)
@login_required
@require_ajax
def enviarAnexoSubmodulo():
    return _resolverRespostaServico(servicoEditor.obterRespostaUploadAnexoSubmodulo())


@Editor_BP.route('/upload-video-submodulo', methods=['POST'])
@RequerPermissao(ChavesPermissao.EDITAR_MODULOS)
@login_required
@require_ajax
def enviarVideoSubmodulo():
    return _resolverRespostaServico(servicoEditor.obterRespostaUploadVideoSubmodulo())


@Editor_BP.route('/upload-imagem-submodulo', methods=['POST'])
@RequerPermissao(ChavesPermissao.EDITAR_MODULOS)
@login_required
@require_ajax
def enviarImagemSubmodulo():
    return _resolverRespostaServico(servicoEditor.obterRespostaUploadImagemSubmodulo())

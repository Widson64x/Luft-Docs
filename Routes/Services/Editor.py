from flask import Blueprint, abort, jsonify, redirect, render_template, url_for

from Services.ServicoEditor import ServicoEditor

editor_bp = Blueprint('editor', __name__, url_prefix='/editor')
servicoEditor = ServicoEditor()


def _resolverRespostaServico(resposta_servico):
    if resposta_servico["tipo"] == "erro":
        abort(resposta_servico["codigo"], resposta_servico["mensagem"])
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


@editor_bp.route('/')
def exibirPainelEditor():
    return _resolverRespostaServico(servicoEditor.obterRespostaPainelEditor())


@editor_bp.route('/novo', methods=['GET', 'POST'])
def criarModulo():
    return _resolverRespostaServico(servicoEditor.obterRespostaCriacaoModulo())


@editor_bp.route('/modulo/<mid>', methods=['GET', 'POST'])
def editarModulo(mid):
    return _resolverRespostaServico(servicoEditor.obterRespostaEdicaoModulo(mid))


@editor_bp.route('/delete/<mid>', methods=['POST'])
def excluirModulo(mid):
    return _resolverRespostaServico(servicoEditor.obterRespostaExclusaoModulo(mid))


@editor_bp.route('/pendentes')
def exibirPendencias():
    return _resolverRespostaServico(servicoEditor.obterRespostaPendencias())


@editor_bp.route('/aprovar/<mid>', methods=['POST'])
def aprovarModulo(mid):
    return _resolverRespostaServico(servicoEditor.obterRespostaAprovacaoModulo(mid))


@editor_bp.route('/rejeitar/<mid>', methods=['POST'])
def rejeitarModulo(mid):
    return _resolverRespostaServico(servicoEditor.obterRespostaRejeicaoModulo(mid))


@editor_bp.route('/historico/<mid>', methods=['GET', 'POST'])
def exibirHistoricoModulo(mid):
    return _resolverRespostaServico(servicoEditor.obterRespostaHistoricoModulo(mid))


@editor_bp.route('/options', methods=['GET'])
def listarOpcoesEditor():
    return _resolverRespostaServico(servicoEditor.obterRespostaOpcoesEditor())


@editor_bp.route('/upload_image/<modulo_id>', methods=['POST'])
def enviarImagemModulo(modulo_id):
    return _resolverRespostaServico(servicoEditor.obterRespostaUploadImagem(modulo_id))


@editor_bp.route('/upload_video/<modulo_id>', methods=['POST'])
def enviarVideoModulo(modulo_id):
    return _resolverRespostaServico(servicoEditor.obterRespostaUploadVideo(modulo_id))


@editor_bp.route('/upload_anexo', methods=['POST'])
def enviarAnexoModulo():
    return _resolverRespostaServico(servicoEditor.obterRespostaUploadAnexo())


@editor_bp.route('/submodulos')
def listarSubmodulos():
    return _resolverRespostaServico(servicoEditor.obterRespostaListagemSubmodulos())


@editor_bp.route('/deletar_submodulo', methods=['POST'])
def excluirSubmodulo():
    return _resolverRespostaServico(servicoEditor.obterRespostaExclusaoSubmodulo())


@editor_bp.route('/criar_submodulo', methods=['POST'])
def criarSubmodulo():
    return _resolverRespostaServico(servicoEditor.obterRespostaCriacaoSubmodulo())


@editor_bp.route('/submodulo/<path:submodulo_path>', methods=['GET', 'POST'])
def editarSubmodulo(submodulo_path):
    return _resolverRespostaServico(servicoEditor.obterRespostaEdicaoSubmodulo(submodulo_path))


@editor_bp.route('/diff_pendente')
def obterDiffPendente():
    return _resolverRespostaServico(servicoEditor.obterRespostaDiffPendente())


@editor_bp.route('/diff_historico')
def obterDiffHistorico():
    return _resolverRespostaServico(servicoEditor.obterRespostaDiffHistorico())


@editor_bp.route('/get_historical_content')
def obterConteudoHistorico():
    return _resolverRespostaServico(servicoEditor.obterRespostaConteudoHistorico())


@editor_bp.route('/upload_submodule_anexo', methods=['POST'])
def enviarAnexoSubmodulo():
    return _resolverRespostaServico(servicoEditor.obterRespostaUploadAnexoSubmodulo())


@editor_bp.route('/upload_submodule_video', methods=['POST'])
def enviarVideoSubmodulo():
    return _resolverRespostaServico(servicoEditor.obterRespostaUploadVideoSubmodulo())


@editor_bp.route('/upload_submodule_image', methods=['POST'])
def enviarImagemSubmodulo():
    return _resolverRespostaServico(servicoEditor.obterRespostaUploadImagemSubmodulo())

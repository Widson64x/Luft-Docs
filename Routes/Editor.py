from flask import Blueprint, abort, jsonify, redirect, render_template, url_for

from Services.ServicoEditor import ServicoEditor

Editor_BP = Blueprint('Editor', __name__)
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


@Editor_BP.route('/')
def exibirPainelEditor():
    return _resolverRespostaServico(servicoEditor.obterRespostaPainelEditor())


@Editor_BP.route('/novo', methods=['GET', 'POST'])
def criarModulo():
    return _resolverRespostaServico(servicoEditor.obterRespostaCriacaoModulo())


@Editor_BP.route('/modulo/<mid>', methods=['GET', 'POST'])
def editarModulo(mid):
    return _resolverRespostaServico(servicoEditor.obterRespostaEdicaoModulo(mid))


@Editor_BP.route('/excluir/<mid>', methods=['POST'])
def excluirModulo(mid):
    return _resolverRespostaServico(servicoEditor.obterRespostaExclusaoModulo(mid))


@Editor_BP.route('/pendencias')
def exibirPendencias():
    return _resolverRespostaServico(servicoEditor.obterRespostaPendencias())


@Editor_BP.route('/aprovar/<mid>', methods=['POST'])
def aprovarModulo(mid):
    return _resolverRespostaServico(servicoEditor.obterRespostaAprovacaoModulo(mid))


@Editor_BP.route('/rejeitar/<mid>', methods=['POST'])
def rejeitarModulo(mid):
    return _resolverRespostaServico(servicoEditor.obterRespostaRejeicaoModulo(mid))


@Editor_BP.route('/historico/<mid>', methods=['GET', 'POST'])
def exibirHistoricoModulo(mid):
    return _resolverRespostaServico(servicoEditor.obterRespostaHistoricoModulo(mid))


@Editor_BP.route('/opcoes', methods=['GET'])
def listarOpcoesEditor():
    return _resolverRespostaServico(servicoEditor.obterRespostaOpcoesEditor())


@Editor_BP.route('/upload-imagem/<modulo_id>', methods=['POST'])
def enviarImagemModulo(modulo_id):
    return _resolverRespostaServico(servicoEditor.obterRespostaUploadImagem(modulo_id))


@Editor_BP.route('/upload-video/<modulo_id>', methods=['POST'])
def enviarVideoModulo(modulo_id):
    return _resolverRespostaServico(servicoEditor.obterRespostaUploadVideo(modulo_id))


@Editor_BP.route('/upload-anexo', methods=['POST'])
def enviarAnexoModulo():
    return _resolverRespostaServico(servicoEditor.obterRespostaUploadAnexo())


@Editor_BP.route('/submodulos')
def listarSubmodulos():
    return _resolverRespostaServico(servicoEditor.obterRespostaListagemSubmodulos())


@Editor_BP.route('/excluir-submodulo', methods=['POST'])
def excluirSubmodulo():
    return _resolverRespostaServico(servicoEditor.obterRespostaExclusaoSubmodulo())


@Editor_BP.route('/criar-submodulo', methods=['POST'])
def criarSubmodulo():
    return _resolverRespostaServico(servicoEditor.obterRespostaCriacaoSubmodulo())


@Editor_BP.route('/submodulo/<path:submodulo_path>', methods=['GET', 'POST'])
def editarSubmodulo(submodulo_path):
    return _resolverRespostaServico(servicoEditor.obterRespostaEdicaoSubmodulo(submodulo_path))


@Editor_BP.route('/diff-pendente')
def obterDiffPendente():
    return _resolverRespostaServico(servicoEditor.obterRespostaDiffPendente())


@Editor_BP.route('/diff-historico')
def obterDiffHistorico():
    return _resolverRespostaServico(servicoEditor.obterRespostaDiffHistorico())


@Editor_BP.route('/obter-conteudo-historico')
def obterConteudoHistorico():
    return _resolverRespostaServico(servicoEditor.obterRespostaConteudoHistorico())


@Editor_BP.route('/upload-anexo-submodulo', methods=['POST'])
def enviarAnexoSubmodulo():
    return _resolverRespostaServico(servicoEditor.obterRespostaUploadAnexoSubmodulo())


@Editor_BP.route('/upload-video-submodulo', methods=['POST'])
def enviarVideoSubmodulo():
    return _resolverRespostaServico(servicoEditor.obterRespostaUploadVideoSubmodulo())


@Editor_BP.route('/upload-imagem-submodulo', methods=['POST'])
def enviarImagemSubmodulo():
    return _resolverRespostaServico(servicoEditor.obterRespostaUploadImagemSubmodulo())

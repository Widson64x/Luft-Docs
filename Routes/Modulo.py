from flask import Blueprint, redirect, render_template, request, url_for
from flask_login import login_required
from luftcore.extensions.flask_extension import render_404, render_500, render_no_permission

from Services.PermissaoService import ChavesPermissao, RequerPermissao
from Services.ServicoModulo import ServicoModulo

Modulo_BP = Blueprint("Modulo", __name__)
servicoModulo = ServicoModulo()


def _renderizar_erro_http(codigo, mensagem):
    if codigo == 403:
        return render_no_permission(mensagem)
    if codigo == 404:
        return render_404(mensagem)
    return render_500(mensagem)


def _resolverRespostaServico(resposta_servico):
    if resposta_servico["tipo"] == "redirecionar":
        return redirect(
            url_for(
                resposta_servico["endpoint"],
                **resposta_servico.get("parametros", {}),
            )
        )
    if resposta_servico["tipo"] == "erro":
        return _renderizar_erro_http(
            resposta_servico["codigo"],
            resposta_servico["mensagem"],
        )

    codigo = resposta_servico.get("codigo", 200)
    if codigo in {403, 404, 500}:
        mensagem = resposta_servico.get("contexto", {}).get("mensagem")
        mensagens_padrao = {
            403: "Você não tem permissão para acessar este conteúdo.",
            404: "O conteúdo solicitado não foi encontrado.",
            500: "Ocorreu um erro ao montar o conteúdo solicitado.",
        }
        return _renderizar_erro_http(codigo, mensagem or mensagens_padrao[codigo])

    return render_template(
        resposta_servico["template"],
        **resposta_servico.get("contexto", {}),
    ), codigo

@Modulo_BP.route('/', methods=['GET'])
@RequerPermissao(ChavesPermissao.VISUALIZAR_MODULOS)
@login_required
def exibirConteudoModulo():
    resposta_servico = servicoModulo.obterRespostaConteudo(
        idModulo=request.args.get("modulo", "").strip(),
        idModuloTecnico=request.args.get("modulo_tecnico", "").strip(),
        idSubmodulo=request.args.get("submodulo", "").strip(),
        consulta=request.args.get("q", "").strip(),
        token=request.args.get("token", "").strip(),
    )
    return _resolverRespostaServico(resposta_servico)
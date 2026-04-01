from flask import Blueprint, redirect, render_template, request, url_for
from flask_login import login_required
from luftcore.extensions.flask_extension import render_404, render_500, render_no_permission

from Services.PermissaoService import ChavesPermissao, RequerPermissao
from Services.ServicoSubModulo import ServicoSubModulo

Submodulo_BP = Blueprint("Submodulo", __name__)
servicoSubModulo = ServicoSubModulo()


def _renderizar_erro_http(codigo, mensagem):
    if codigo == 403:
        return render_no_permission(mensagem)
    if codigo == 404:
        return render_404(mensagem)
    return render_500(mensagem)

@Submodulo_BP.route('/', methods=['GET'])
@RequerPermissao(ChavesPermissao.VISUALIZAR_MODULOS)
@login_required
def exibirSubmodulo():
    resposta_servico = servicoSubModulo.obterRespostaSubmodulo(
        request.args.get("nome", "").strip()
    )
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
    return render_template(
        resposta_servico["template"],
        **resposta_servico.get("contexto", {}),
    ), resposta_servico.get("codigo", 200)
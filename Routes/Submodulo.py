from flask import Blueprint, abort, redirect, render_template, request, url_for

from Services.ServicoSubModulo import ServicoSubModulo
from Utils.auth.Autenticacao import LoginObrigatorio

Submodulo_BP = Blueprint("Submodulo", __name__)
servicoSubModulo = ServicoSubModulo()

@Submodulo_BP.route('/', methods=['GET'])
@LoginObrigatorio
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
        abort(resposta_servico["codigo"], resposta_servico["mensagem"])
    return render_template(
        resposta_servico["template"],
        **resposta_servico.get("contexto", {}),
    ), resposta_servico.get("codigo", 200)
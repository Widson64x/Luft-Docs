from flask import Blueprint, abort, redirect, render_template, request, url_for

from Services.ServicoModulo import ServicoModulo
from Utils.auth.Autenticacao import LoginObrigatorio

Modulo_BP = Blueprint("Modulo", __name__)
servicoModulo = ServicoModulo()


def _resolverRespostaServico(resposta_servico):
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

@Modulo_BP.route('/', methods=['GET'])
@LoginObrigatorio
def exibirConteudoModulo():
    resposta_servico = servicoModulo.obterRespostaConteudo(
        idModulo=request.args.get("modulo", "").strip(),
        idModuloTecnico=request.args.get("modulo_tecnico", "").strip(),
        idSubmodulo=request.args.get("submodulo", "").strip(),
        consulta=request.args.get("q", "").strip(),
        token=request.args.get("token", "").strip(),
    )
    return _resolverRespostaServico(resposta_servico)
# Certifique-se de que 'session' está importado para pegar o token no redirecionamento
from flask import Blueprint, redirect, render_template, url_for

from Forms.FormularioAvaliacao import FormularioAvaliacao
from Services.ServicoAvaliacao import ServicoAvaliacao

Avaliacao_BP = Blueprint('Avaliacao', __name__)
servicoAvaliacao = ServicoAvaliacao()

# Aplicando a sugestão de URL limpa: /avaliacao/nome-do-modulo
@Avaliacao_BP.route('/<string:document_id>', methods=['GET', 'POST'])
def avaliarDocumento(document_id):
    form = FormularioAvaliacao()
    resposta_servico = servicoAvaliacao.obterRespostaAvaliacao(document_id, form)
    if resposta_servico["tipo"] == "redirecionar":
        return redirect(
            url_for(
                resposta_servico["endpoint"],
                **resposta_servico.get("parametros", {}),
            )
        )
    return render_template(
        resposta_servico["template"],
        **resposta_servico.get("contexto", {}),
    )
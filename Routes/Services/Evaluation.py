# Certifique-se de que 'session' está importado para pegar o token no redirecionamento
from flask import Blueprint, redirect, render_template, url_for

from Routes.Components.FormEvaluation import EvaluationForm
from Services.ServicoAvaliacao import ServicoAvaliacao

evaluation_bp = Blueprint('evaluation', __name__, url_prefix='/evaluation')
servicoAvaliacao = ServicoAvaliacao()

# Aplicando a sugestão de URL limpa: /evaluation/nome-do-modulo
@evaluation_bp.route('/<string:document_id>', methods=['GET', 'POST'])
def avaliarDocumento(document_id):
    form = EvaluationForm()
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
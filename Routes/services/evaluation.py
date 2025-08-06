# Certifique-se de que 'session' está importado para pegar o token no redirecionamento
from flask import render_template, request, redirect, url_for, Blueprint, flash, session
from Routes.components.evaluation_form import EvaluationForm
from models import db, Evaluation

evaluation_bp = Blueprint('evaluation', __name__, url_prefix='/evaluation')

# Aplicando a sugestão de URL limpa: /evaluation/nome-do-modulo
@evaluation_bp.route('/<string:document_id>', methods=['GET', 'POST'])
def evaluation(document_id):
    form = EvaluationForm()
    
    # O token é pego da sessão, não mais da URL, para o redirecionamento
    token = session.get('token')

    if form.validate_on_submit():
        try:
            evaluation = Evaluation(
                document_id=document_id, 
                rating=form.rating.data, 
                feedback=form.feedback.data, 
                suggestions=form.suggestions.data, 
                techos=form.techos.data, 
                changes=form.changes.data
            )
            db.session.add(evaluation)
            db.session.commit()
            
            # 1. ADICIONADO: Cria a mensagem de sucesso.
            flash('Obrigado pela sua avaliação!', 'success')
            
            # 2. ALTERADO: Redireciona para a página do módulo, passando os parâmetros necessários.
            return redirect(url_for('modulo.ver_modulo_pela_raiz', modulo=document_id, token=token))

        except Exception as e:
            db.session.rollback()
            # A mensagem de erro continua igual.
            flash(f'Erro ao enviar avaliação: {e}', 'error')
            
    return render_template('evaluation.html', form=form, document_id=document_id)
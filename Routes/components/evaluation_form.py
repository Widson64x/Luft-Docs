from flask_wtf import FlaskForm
from wtforms import IntegerField, TextAreaField
from wtforms.validators import Optional, NumberRange

class EvaluationForm(FlaskForm):
    # Definição dos campos permanece a mesma
    rating = IntegerField('Avaliação', validators=[Optional(), NumberRange(min=1, max=5)])
    feedback = TextAreaField('Feedback')
    suggestions = TextAreaField('Sugestões de Melhorias')
    techos = TextAreaField('Techos')
    changes = TextAreaField('Mudanças Solicitadas')

    # ---- VALIDAÇÃO CUSTOMIZADA: "PELO MENOS 50 CARACTERES" ----
    def validate(self, extra_validators=None):
        if not super(EvaluationForm, self).validate(extra_validators):
            return False

        # 1. Verifica se a nota foi dada
        is_rating_empty = self.rating.data is None or self.rating.data == 0

        # 2. Função auxiliar para verificar o comprimento do texto
        def is_text_long_enough(field_data):
            # Retorna True se o campo tem 50 ou mais caracteres (ignorando espaços em branco no início/fim)
            return field_data and len(field_data.strip()) >= 50

        # 3. Verifica se PELO MENOS UM dos campos de texto atinge o comprimento mínimo
        is_any_text_valid = (
            is_text_long_enough(self.feedback.data) or
            is_text_long_enough(self.suggestions.data) or
            is_text_long_enough(self.techos.data) or
            is_text_long_enough(self.changes.data)
        )

        # 4. A validação falha se a nota está vazia E NENHUM texto é longo o suficiente
        if is_rating_empty and not is_any_text_valid:
            # A mensagem de erro agora reflete a nova regra de 50 caracteres
            self.rating.errors.append("Para enviar, dê uma nota ou escreva um comentário com no mínimo 50 caracteres.")
            return False
        
        return True
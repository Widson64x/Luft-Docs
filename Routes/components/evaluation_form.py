from flask_wtf import FlaskForm
from wtforms import IntegerField, TextAreaField
from wtforms.validators import Optional, NumberRange, Length

class EvaluationForm(FlaskForm):
    rating      = IntegerField('Avaliação',           validators=[Optional(), NumberRange(min=1, max=5)])
    feedback    = TextAreaField('Feedback',           validators=[Optional(), Length(min=50, message='Pelo menos 50 caracteres')])
    suggestions = TextAreaField('Sugestões de Melhoria', validators=[Optional(), Length(min=50, message='Pelo menos 50 caracteres')])
    techos      = TextAreaField('Techos',             validators=[Optional(), Length(min=50, message='Pelo menos 50 caracteres')])
    changes     = TextAreaField('Mudanças Solicitadas', validators=[Optional(), Length(min=50, message='Pelo menos 50 caracteres')])

    def validate(self, extra_validators=None):
        if not super().validate(extra_validators):
            return False

        is_rating_empty = not self.rating.data
        def long_enough(txt): return txt and len(txt.strip()) >= 50

        any_long = any([
            long_enough(self.feedback.data),
            long_enough(self.suggestions.data),
            long_enough(self.techos.data),
            long_enough(self.changes.data)
        ])

        if is_rating_empty and not any_long:
            self.rating.errors.append(
                "Para enviar, dê uma nota ou escreva um comentário com no mínimo 50 caracteres."
            )
            return False

        return True

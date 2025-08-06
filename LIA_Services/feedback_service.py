# /ai_services/feedback_service.py
from Utils.recommendation_service import log_ai_feedback as log_feedback_to_db

def save_feedback(response_id, user_id, rating, comment, user_question, model_used, context_sources):
    """
    Valida e salva o feedback do usuário no banco de dados.
    """
    if not all([response_id, user_id, rating is not None]):
        raise ValueError("Dados de feedback inválidos: response_id, user_id e rating são obrigatórios.")

    try:
        # A função `log_ai_feedback` já existe em `utils`, então apenas a chamamos.
        # Esta camada de serviço serve para validação e como um ponto centralizado de chamada.
        log_feedback_to_db(
            response_id=response_id,
            user_id=user_id,
            rating=rating,
            comment=comment,
            user_question=user_question,
            model_used=model_used,
            context_sources=context_sources
        )
        print(f"Feedback para response_id {response_id} registrado com sucesso.")
    except Exception as e:
        print(f"ERRO ao chamar log_ai_feedback: {e}")
        # Propaga a exceção para ser tratada na rota.
        raise
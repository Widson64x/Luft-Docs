# /ai_services/feedback_service.py
from Utils.ServicoRecomendacao import RegistrarFeedbackIA as registrarFeedbackNoBanco

def save_feedback(response_id, user_id, rating, comment, user_question, model_used, context_sources):
    """
    Valida e salva o feedback do usuário no banco de dados.
    """
    if not all([response_id, user_id, rating is not None]):
        raise ValueError("Dados de feedback inválidos: response_id, user_id e rating são obrigatórios.")

    try:
        registrarFeedbackNoBanco(
            identificadorResposta=response_id,
            identificadorUsuario=user_id,
            avaliacao=rating,
            comentario=comment,
            perguntaUsuario=user_question,
            modeloUtilizado=model_used,
            fontesContexto=context_sources,
        )
        print(f"Feedback para response_id {response_id} registrado com sucesso.")
    except Exception as e:
        print(f"ERRO ao registrar feedback da IA: {e}")
        # Propaga a exceção para ser tratada na rota.
        raise
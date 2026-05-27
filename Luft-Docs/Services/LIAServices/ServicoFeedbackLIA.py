from __future__ import annotations

from Utils.ServicoRecomendacao import RegistrarFeedbackIA


class ServicoFeedbackLIA:
    """Centraliza a persistencia do feedback gerado pela LIA."""

    def salvarFeedback(
        self,
        identificador_resposta: str,
        identificador_usuario: str,
        avaliacao: int,
        comentario: str | None,
        pergunta_usuario: str | None,
        modelo_utilizado: str | None,
        fontes_contexto: list[str] | None,
    ) -> None:
        """Valida e salva o feedback do usuario no banco de dados."""
        if not all(
            [identificador_resposta, identificador_usuario, avaliacao is not None]
        ):
            raise ValueError(
                "Dados de feedback invalidos: response_id, user_id e rating sao obrigatorios."
            )

        try:
            RegistrarFeedbackIA(
                identificadorResposta=identificador_resposta,
                identificadorUsuario=identificador_usuario,
                avaliacao=avaliacao,
                comentario=comentario,
                perguntaUsuario=pergunta_usuario,
                modeloUtilizado=modelo_utilizado,
                fontesContexto=fontes_contexto,
            )
            print(
                f"Feedback para response_id {identificador_resposta} registrado com sucesso."
            )
        except Exception as erro:
            print(f"ERRO ao registrar feedback da IA: {erro}")
            raise

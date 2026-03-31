from __future__ import annotations

from flask import flash, session

from Models import Evaluation, db


class ServicoAvaliacao:
    """Centraliza o fluxo de persistencia das avaliacoes de documentos."""

    def obterRespostaAvaliacao(
        self, document_id: str, formulario
    ) -> dict[str, object]:
        """Processa a submissao do formulario e retorna o proximo passo da rota."""
        if formulario.validate_on_submit():
            try:
                avaliacao = Evaluation(
                    document_id=document_id,
                    rating=formulario.rating.data,
                    feedback=formulario.feedback.data,
                    suggestions=formulario.suggestions.data,
                    techos=formulario.techos.data,
                    changes=formulario.changes.data,
                )
                db.session.add(avaliacao)
                db.session.commit()

                flash("Obrigado pela sua avaliacao!", "success")
                return {
                    "tipo": "redirecionar",
                    "endpoint": "Modulo.exibirConteudoModulo",
                    "parametros": {
                        "modulo": document_id,
                        "token": session.get("token"),
                    },
                }
            except Exception as erro:
                db.session.rollback()
                flash(f"Erro ao enviar avaliacao: {erro}", "error")

        return {
            "tipo": "renderizar",
            "template": "Components/evaluation.html",
            "contexto": {
                "form": formulario,
                "document_id": document_id,
            },
        }
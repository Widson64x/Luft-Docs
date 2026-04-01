from __future__ import annotations

from flask import flash, session

from Db.Connections import obterSessaoPostgres
from Models import AvaliacaoDocumento


class ServicoAvaliacao:
    """Centraliza o fluxo de persistencia das avaliacoes de documentos."""

    def obterRespostaAvaliacao(
        self, document_id: str, formulario
    ) -> dict[str, object]:
        """Processa a submissao do formulario e retorna o proximo passo da rota."""
        if formulario.validate_on_submit():
            sessao = obterSessaoPostgres()
            try:
                avaliacao = AvaliacaoDocumento(
                    DocumentoId=document_id,
                    Avaliacao=formulario.rating.data,
                    Comentario=formulario.feedback.data,
                    Sugestoes=formulario.suggestions.data,
                    Trechos=formulario.techos.data,
                    MudancasSolicitadas=formulario.changes.data,
                )
                sessao.add(avaliacao)
                sessao.commit()

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
                sessao.rollback()
                flash(f"Erro ao enviar avaliacao: {erro}", "error")
            finally:
                sessao.close()

        return {
            "tipo": "renderizar",
            "template": "Components/evaluation.html",
            "contexto": {
                "form": formulario,
                "document_id": document_id,
            },
        }
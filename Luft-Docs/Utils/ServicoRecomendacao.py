from __future__ import annotations

import json
import logging
import re
from typing import Any

from sqlalchemy import func

from Db.Connections import obterSessaoPostgres
from Models import AcessoDocumento, FeedbackIA, LogBusca

logger = logging.getLogger(__name__)


def RegistrarAcessoDocumento(identificadorDocumento: str) -> None:
    """Registra o acesso a um documento utilizando o ORM da aplicacao."""
    if not identificadorDocumento:
        return

    sessao = obterSessaoPostgres()
    try:
        documento = sessao.get(AcessoDocumento, identificadorDocumento)
        if documento:
            documento.QuantidadeAcessos += 1
        else:
            documento = AcessoDocumento(
                DocumentoId=identificadorDocumento,
                QuantidadeAcessos=1,
            )
            sessao.add(documento)
        sessao.commit()
    except Exception as erro:
        sessao.rollback()
        logger.exception("Erro ao registrar acesso ao documento: %s", erro)
    finally:
        sessao.close()


def RegistrarTermoBusca(termoBusca: str) -> None:
    """Registra um termo de busca normalizado para fins analiticos."""
    if not termoBusca:
        return

    termo_normalizado = termoBusca.strip().lower()
    sessao = obterSessaoPostgres()
    try:
        termo_existente = sessao.get(LogBusca, termo_normalizado)
        if termo_existente:
            termo_existente.QuantidadeBuscas += 1
        else:
            termo_existente = LogBusca(
                TermoBusca=termo_normalizado,
                QuantidadeBuscas=1,
            )
            sessao.add(termo_existente)
        sessao.commit()
    except Exception as erro:
        sessao.rollback()
        logger.exception("Erro ao registrar termo de busca: %s", erro)
    finally:
        sessao.close()


def ObterContagensAcesso(identificadoresDocumentos: list[str]) -> dict[str, int]:
    """Retorna a contagem de acessos para uma lista de documentos."""
    if not identificadoresDocumentos:
        return {}

    sessao = obterSessaoPostgres()
    try:
        acessos = sessao.query(AcessoDocumento).filter(
            AcessoDocumento.DocumentoId.in_(identificadoresDocumentos)
        ).all()
        return {acesso.DocumentoId: acesso.QuantidadeAcessos for acesso in acessos}
    finally:
        sessao.close()


def ObterMaisAcessados(limite: int = 5) -> list[dict[str, Any]]:
    """Retorna os documentos mais acessados em ordem decrescente."""
    sessao = obterSessaoPostgres()
    try:
        documentos = (
            sessao.query(AcessoDocumento)
            .order_by(AcessoDocumento.QuantidadeAcessos.desc())
            .limit(limite)
            .all()
        )
        return [
            {
                "document_id": documento.DocumentoId,
                "access_count": documento.QuantidadeAcessos,
            }
            for documento in documentos
        ]
    finally:
        sessao.close()


def ObterSugestoesAutocomplete(termo: str, limite: int = 5) -> list[str]:
    """Retorna sugestoes de autocomplete baseadas no historico de buscas."""
    if not termo:
        return []

    termo_pesquisa = f"{termo.strip().lower()}%"
    sessao = obterSessaoPostgres()
    try:
        resultados = (
            sessao.query(LogBusca)
            .filter(LogBusca.TermoBusca.like(termo_pesquisa))
            .order_by(LogBusca.QuantidadeBuscas.desc())
            .limit(limite)
            .all()
        )
        return [resultado.TermoBusca for resultado in resultados]
    finally:
        sessao.close()


def ObterBuscasPopulares(limite: int = 5) -> list[dict[str, Any]]:
    """Retorna os termos de busca mais populares registrados."""
    sessao = obterSessaoPostgres()
    try:
        buscas = (
            sessao.query(LogBusca)
            .order_by(LogBusca.QuantidadeBuscas.desc())
            .limit(limite)
            .all()
        )
        return [
            {"query_term": busca.TermoBusca, "search_count": busca.QuantidadeBuscas}
            for busca in buscas
        ]
    finally:
        sessao.close()


def ObterRecomendacoesHibridas(
    limite: int = 5,
    pesoAcesso: float = 0.6,
    pesoBusca: float = 0.4,
) -> list[dict[str, Any]]:
    """Calcula recomendacoes combinando acessos e relevancia por termos buscados."""
    sessao = obterSessaoPostgres()
    try:
        documentos = sessao.query(AcessoDocumento).all()
        if not documentos:
            return []

        buscas_populares = sessao.query(LogBusca).all()
        maior_contagem_acesso = (
            sessao.query(func.max(AcessoDocumento.QuantidadeAcessos)).scalar() or 1
        )
        maior_contagem_busca = (
            sessao.query(func.max(LogBusca.QuantidadeBuscas)).scalar() or 1
        )

        pontuacoes_busca = {
            busca.TermoBusca: busca.QuantidadeBuscas / maior_contagem_busca
            for busca in buscas_populares
        }

        pontuacoes_finais: dict[str, float] = {}
        for documento in documentos:
            pontuacao = (documento.QuantidadeAcessos / maior_contagem_acesso) * pesoAcesso
            relevancia = 0.0
            for termo, pontuacao_normalizada in pontuacoes_busca.items():
                palavras_busca = set(re.split(r"\s|_|-", termo))
                if any(
                    palavra in documento.DocumentoId.lower()
                    for palavra in palavras_busca
                    if len(palavra) > 2
                ):
                    relevancia += pontuacao_normalizada

            if pontuacoes_busca:
                pontuacao += (relevancia / len(pontuacoes_busca)) * pesoBusca

            pontuacoes_finais[documento.DocumentoId] = pontuacao

        documentos_ordenados = sorted(
            pontuacoes_finais.items(), key=lambda item: item[1], reverse=True
        )
        return [
            {"document_id": identificador, "score": pontuacao}
            for identificador, pontuacao in documentos_ordenados[:limite]
        ]
    finally:
        sessao.close()


def RegistrarFeedbackIA(
    identificadorResposta: str,
    identificadorUsuario: str,
    avaliacao: int,
    comentario: str | None = None,
    perguntaUsuario: str | None = None,
    modeloUtilizado: str | None = None,
    fontesContexto: list[str] | None = None,
) -> None:
    """Registra o feedback do usuario para uma resposta gerada pela IA."""
    sessao = obterSessaoPostgres()
    try:
        contexto_serializado = json.dumps(fontesContexto) if fontesContexto else None
        novo_feedback = FeedbackIA(
            RespostaId=identificadorResposta,
            UsuarioId=identificadorUsuario,
            PerguntaUsuario=perguntaUsuario,
            ModeloUtilizado=modeloUtilizado,
            FontesContexto=contexto_serializado,
            Avaliacao=avaliacao,
            Comentario=comentario,
        )
        sessao.add(novo_feedback)
        sessao.commit()
    except Exception as erro:
        sessao.rollback()
        logger.exception("Erro ao registrar feedback da IA: %s", erro)
        raise
    finally:
        sessao.close()
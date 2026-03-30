from __future__ import annotations

import json
import logging
import re
from typing import Any

from sqlalchemy import func

from Models import DocumentAccess, IAFeedback, SearchLog, db

logger = logging.getLogger(__name__)


def RegistrarAcessoDocumento(identificadorDocumento: str) -> None:
    """Registra o acesso a um documento utilizando o ORM da aplicacao."""
    if not identificadorDocumento:
        return

    try:
        documento = db.session.get(DocumentAccess, identificadorDocumento)
        if documento:
            documento.access_count += 1
        else:
            documento = DocumentAccess(
                document_id=identificadorDocumento,
                access_count=1,
            )
            db.session.add(documento)
        db.session.commit()
    except Exception as erro:
        db.session.rollback()
        logger.exception("Erro ao registrar acesso ao documento: %s", erro)


def RegistrarTermoBusca(termoBusca: str) -> None:
    """Registra um termo de busca normalizado para fins analiticos."""
    if not termoBusca:
        return

    termo_normalizado = termoBusca.strip().lower()
    try:
        termo_existente = db.session.get(SearchLog, termo_normalizado)
        if termo_existente:
            termo_existente.search_count += 1
        else:
            termo_existente = SearchLog(
                query_term=termo_normalizado,
                search_count=1,
            )
            db.session.add(termo_existente)
        db.session.commit()
    except Exception as erro:
        db.session.rollback()
        logger.exception("Erro ao registrar termo de busca: %s", erro)


def ObterContagensAcesso(identificadoresDocumentos: list[str]) -> dict[str, int]:
    """Retorna a contagem de acessos para uma lista de documentos."""
    if not identificadoresDocumentos:
        return {}

    acessos = DocumentAccess.query.filter(
        DocumentAccess.document_id.in_(identificadoresDocumentos)
    ).all()
    return {acesso.document_id: acesso.access_count for acesso in acessos}


def ObterMaisAcessados(limite: int = 5) -> list[dict[str, Any]]:
    """Retorna os documentos mais acessados em ordem decrescente."""
    documentos = (
        DocumentAccess.query.order_by(DocumentAccess.access_count.desc())
        .limit(limite)
        .all()
    )
    return [
        {"document_id": documento.document_id, "access_count": documento.access_count}
        for documento in documentos
    ]


def ObterSugestoesAutocomplete(termo: str, limite: int = 5) -> list[str]:
    """Retorna sugestoes de autocomplete baseadas no historico de buscas."""
    if not termo:
        return []

    termo_pesquisa = f"{termo.strip().lower()}%"
    resultados = (
        SearchLog.query.filter(SearchLog.query_term.like(termo_pesquisa))
        .order_by(SearchLog.search_count.desc())
        .limit(limite)
        .all()
    )
    return [resultado.query_term for resultado in resultados]


def ObterBuscasPopulares(limite: int = 5) -> list[dict[str, Any]]:
    """Retorna os termos de busca mais populares registrados."""
    buscas = SearchLog.query.order_by(SearchLog.search_count.desc()).limit(limite).all()
    return [
        {"query_term": busca.query_term, "search_count": busca.search_count}
        for busca in buscas
    ]


def ObterRecomendacoesHibridas(
    limite: int = 5,
    pesoAcesso: float = 0.6,
    pesoBusca: float = 0.4,
) -> list[dict[str, Any]]:
    """Calcula recomendacoes combinando acessos e relevancia por termos buscados."""
    documentos = DocumentAccess.query.all()
    if not documentos:
        return []

    buscas_populares = SearchLog.query.all()
    maior_contagem_acesso = db.session.query(func.max(DocumentAccess.access_count)).scalar() or 1
    maior_contagem_busca = db.session.query(func.max(SearchLog.search_count)).scalar() or 1

    pontuacoes_busca = {
        busca.query_term: busca.search_count / maior_contagem_busca
        for busca in buscas_populares
    }

    pontuacoes_finais: dict[str, float] = {}
    for documento in documentos:
        pontuacao = (documento.access_count / maior_contagem_acesso) * pesoAcesso
        relevancia = 0.0
        for termo, pontuacao_normalizada in pontuacoes_busca.items():
            palavras_busca = set(re.split(r"\s|_|-", termo))
            if any(
                palavra in documento.document_id.lower()
                for palavra in palavras_busca
                if len(palavra) > 2
            ):
                relevancia += pontuacao_normalizada

        if pontuacoes_busca:
            pontuacao += (relevancia / len(pontuacoes_busca)) * pesoBusca

        pontuacoes_finais[documento.document_id] = pontuacao

    documentos_ordenados = sorted(
        pontuacoes_finais.items(), key=lambda item: item[1], reverse=True
    )
    return [
        {"document_id": identificador, "score": pontuacao}
        for identificador, pontuacao in documentos_ordenados[:limite]
    ]


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
    try:
        contexto_serializado = json.dumps(fontesContexto) if fontesContexto else None
        novo_feedback = IAFeedback(
            response_id=identificadorResposta,
            user_id=identificadorUsuario,
            user_question=perguntaUsuario,
            model_used=modeloUtilizado,
            context_sources=contexto_serializado,
            rating=avaliacao,
            comment=comentario,
        )
        db.session.add(novo_feedback)
        db.session.commit()
    except Exception as erro:
        db.session.rollback()
        logger.exception("Erro ao registrar feedback da IA: %s", erro)
        raise
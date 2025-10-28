# /utils/recommendation_service.py (Refatorado com SQLAlchemy)
from datetime import datetime
import re
import json
from sqlalchemy import func

# Importe o objeto 'db' e os modelos necessários
from Models import db, DocumentAccess, SearchLog, IAFeedback

def log_document_access(document_id: str):
    """Registra um acesso a um documento usando o ORM."""
    if not document_id: return
    
    try:
        # Tenta encontrar o registro existente
        doc = DocumentAccess.query.get(document_id)
        
        if doc:
            # Se existe, incrementa o contador
            doc.access_count += 1
        else:
            # Se não existe, cria um novo registro
            doc = DocumentAccess(document_id=document_id, access_count=1)
            db.session.add(doc)
        
        # Salva as alterações no banco de dados
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao registrar acesso ao documento: {e}")

def log_search_term(query_term: str):
    """Registra um termo de busca usando o ORM."""
    if not query_term: return
    normalized_term = query_term.strip().lower()
    
    try:
        # Tenta encontrar o termo de busca existente
        search = SearchLog.query.get(normalized_term)
        
        if search:
            # Se existe, incrementa o contador
            search.search_count += 1
        else:
            # Se não existe, cria um novo registro
            search = SearchLog(query_term=normalized_term, search_count=1)
            db.session.add(search)
        
        # Salva as alterações
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao registrar termo de busca: {e}")

def get_access_counts(document_ids: list) -> dict:
    """Busca a contagem de acessos para uma lista de IDs de documentos."""
    if not document_ids: return {}
    
    # Executa uma consulta para buscar os registros cujos IDs estão na lista
    rows = DocumentAccess.query.filter(DocumentAccess.document_id.in_(document_ids)).all()
    return {row.document_id: row.access_count for row in rows}

def get_most_accessed(limit: int = 5) -> list:
    """Retorna os documentos mais acessados, ordenados por contagem de acessos."""
    # Ordena os resultados pela coluna 'access_count' em ordem decrescente e limita o resultado
    rows = DocumentAccess.query.order_by(DocumentAccess.access_count.desc()).limit(limit).all()
    return [{'document_id': row.document_id, 'access_count': row.access_count} for row in rows]

def get_autocomplete_suggestions(term: str, limit: int = 5) -> list:
    """Retorna sugestões de busca que começam com o termo fornecido."""
    if not term: return []
    search_term = f"{term.strip().lower()}%"
    
    # Usa o método 'like' para busca de padrões e ordena pela popularidade
    rows = SearchLog.query.filter(SearchLog.query_term.like(search_term)).order_by(SearchLog.search_count.desc()).limit(limit).all()
    return [row.query_term for row in rows]

def get_popular_searches(limit: int = 5) -> list:
    """Retorna os termos de busca mais populares."""
    rows = SearchLog.query.order_by(SearchLog.search_count.desc()).limit(limit).all()
    return [{'query_term': row.query_term, 'search_count': row.search_count} for row in rows]

def get_hybrid_recommendations(limit: int = 5, access_weight: float = 0.6, search_weight: float = 0.4) -> list:
    """Gera uma lista de documentos recomendados com base em um algoritmo híbrido."""
    # 1. Obter todos os documentos e suas contagens de acesso
    all_docs = DocumentAccess.query.all()
    if not all_docs:
        return []

    # 2. Obter os termos de busca mais populares
    popular_searches = SearchLog.query.all()

    # 3. Normalizar os scores, usando func.max do SQLAlchemy para eficiência
    max_access_count = db.session.query(func.max(DocumentAccess.access_count)).scalar() or 1
    max_search_count = db.session.query(func.max(SearchLog.search_count)).scalar() or 1
    
    # Pre-processar os termos de busca
    search_scores = {
        search.query_term: search.search_count / max_search_count
        for search in popular_searches
    }

    final_scores = {}

    # 4. Calcular o score final para cada documento
    for doc in all_docs:
        normalized_access_score = doc.access_count / max_access_count
        score = normalized_access_score * access_weight
        
        relevance_score = 0
        for term, normalized_search_score in search_scores.items():
            search_words = set(re.split(r'\s|_|-', term))
            if any(word in doc.document_id.lower() for word in search_words if len(word) > 2):
                relevance_score += normalized_search_score
        
        if len(search_scores) > 0:
            normalized_relevance_score = relevance_score / len(search_scores)
            score += normalized_relevance_score * search_weight
        
        final_scores[doc.document_id] = score

    # 5. Classificar e retornar as recomendações
    sorted_docs = sorted(final_scores.items(), key=lambda item: item[1], reverse=True)
    return [{'document_id': doc_id, 'score': score} for doc_id, score in sorted_docs[:limit]]

# A função log_ai_feedback permanece a mesma, pois já estava refatorada
def log_ai_feedback(response_id: str, user_id: str, rating: int, comment: str = None,
                    user_question: str = None, model_used: str = None, context_sources: list = None):
    try:
        serialized_context_sources = json.dumps(context_sources) if context_sources else None
        novo_feedback = IAFeedback(
            response_id=response_id, user_id=user_id, user_question=user_question,
            model_used=model_used, context_sources=serialized_context_sources,
            rating=rating, comment=comment
        )
        db.session.add(novo_feedback)
        db.session.commit()
        print(f"Feedback registrado via SQLAlchemy para response_id: {response_id} pelo usuário: {user_id}")
    except Exception as e:
        db.session.rollback()
        print(f"Erro ao registrar feedback da IA via SQLAlchemy: {e}")
        raise e

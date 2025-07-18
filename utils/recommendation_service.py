# /utils/recommendation_service.py
from datetime import datetime
import re
from .database_utils import get_db

def log_document_access(document_id: str):
    """Registra um acesso a um documento."""
    if not document_id: return
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT document_id FROM document_access WHERE document_id = ?", (document_id,))
    if cursor.fetchone():
        cursor.execute("UPDATE document_access SET access_count = access_count + 1, last_access = ? WHERE document_id = ?", (datetime.now(), document_id))
    else:
        cursor.execute("INSERT INTO document_access (document_id) VALUES (?)", (document_id,))
    db.commit()

def log_search_term(query_term: str):
    """Registra um termo de busca."""
    if not query_term: return
    normalized_term = query_term.strip().lower()
    db = get_db()
    cursor = db.cursor()
    cursor.execute("SELECT query_term FROM search_log WHERE query_term = ?", (normalized_term,))
    if cursor.fetchone():
        cursor.execute("UPDATE search_log SET search_count = search_count + 1, last_searched = ? WHERE query_term = ?", (datetime.now(), normalized_term))
    else:
        cursor.execute("INSERT INTO search_log (query_term) VALUES (?)", (normalized_term,))
    db.commit()

def get_access_counts(document_ids: list) -> dict:
    """Busca a contagem de acessos para uma lista de IDs de documentos."""
    if not document_ids: return {}
    db = get_db()
    placeholders = ','.join('?' for _ in document_ids)
    query = f"SELECT document_id, access_count FROM document_access WHERE document_id IN ({placeholders})"
    rows = db.execute(query, document_ids).fetchall()
    return {row['document_id']: row['access_count'] for row in rows}

def get_most_accessed(limit: int = 5) -> list:
    """Retorna os documentos mais acessados, ordenados por contagem de acessos."""
    db = get_db()
    query = "SELECT document_id, access_count FROM document_access ORDER BY access_count DESC LIMIT ?"
    rows = db.execute(query, (limit,)).fetchall()
    return [dict(row) for row in rows]

def get_autocomplete_suggestions(term: str, limit: int = 5) -> list:
    """Retorna sugestões de busca que começam com o termo fornecido."""
    if not term: return []
    db = get_db()
    search_term = f"{term.strip().lower()}%"
    query = "SELECT query_term FROM search_log WHERE query_term LIKE ? ORDER BY search_count DESC LIMIT ?"
    rows = db.execute(query, (search_term, limit)).fetchall()
    return [row['query_term'] for row in rows]

def get_popular_searches(limit: int = 5) -> list:
    """Retorna os termos de busca mais populares."""
    db = get_db()
    query = "SELECT query_term, search_count FROM search_log ORDER BY search_count DESC LIMIT ?"
    rows = db.execute(query, (limit,)).fetchall()
    return [dict(row) for row in rows]

# --- NOVO: Algoritmo de Recomendação Híbrida ---
def get_hybrid_recommendations(limit: int = 5, access_weight: float = 0.6, search_weight: float = 0.4) -> list:
    """
    Gera uma lista de documentos recomendados com base em um algoritmo híbrido.
    Este algoritmo combina a popularidade de acesso direto de um documento com a
    relevância de buscas populares que se relacionam com o ID do documento.

    :param limit: O número máximo de recomendações a serem retornadas.
    :param access_weight: O peso a ser dado à popularidade de acesso (0.0 a 1.0).
    :param search_weight: O peso a ser dado à relevância de busca (0.0 a 1.0).
    :return: Uma lista de dicionários, cada um contendo 'document_id' e 'score'.
    """
    db = get_db()

    # 1. Obter todos os documentos e suas contagens de acesso
    all_docs = db.execute("SELECT document_id, access_count FROM document_access").fetchall()
    if not all_docs:
        return []

    # 2. Obter os termos de busca mais populares
    popular_searches = db.execute("SELECT query_term, search_count FROM search_log").fetchall()

    # 3. Normalizar os scores para que fiquem entre 0 e 1, evitando divisão por zero
    max_access_count = max(doc['access_count'] for doc in all_docs) if all_docs else 1
    max_search_count = max(search['search_count'] for search in popular_searches) if popular_searches else 1
    
    if max_access_count == 0: max_access_count = 1
    if max_search_count == 0: max_search_count = 1

    # Pre-processar os termos de busca populares para busca eficiente
    search_scores = {
        search['query_term']: search['search_count'] / max_search_count
        for search in popular_searches
    }
    
    final_scores = {}

    # 4. Calcular o score final para cada documento
    for doc in all_docs:
        doc_id = doc['document_id']
        
        # Score base da popularidade de acesso
        normalized_access_score = doc['access_count'] / max_access_count
        score = normalized_access_score * access_weight
        
        # Adicionar score com base na relevância das buscas
        relevance_score = 0
        for term, normalized_search_score in search_scores.items():
            search_words = set(re.split(r'\s|_|-', term))
            if any(word in doc_id.lower() for word in search_words if len(word) > 2):
                relevance_score += normalized_search_score

        if len(search_scores) > 0:
            normalized_relevance_score = relevance_score / len(search_scores)
            score += normalized_relevance_score * search_weight

        final_scores[doc_id] = score

    # 5. Classificar os documentos pelo score final e retornar o top 'limit'
    sorted_docs = sorted(final_scores.items(), key=lambda item: item[1], reverse=True)
    
    recommendations = [
        {'document_id': doc_id, 'score': score}
        for doc_id, score in sorted_docs[:limit]
    ]

    return recommendations

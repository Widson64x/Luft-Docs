# /ai_services/context_service.py
import os
import re
import google.generativeai as genai
from LIA_Services.Configs.LLMConfig import get_client, are_components_available

# Constantes de permissão
RESTRICTED_PATHS = ["data/global/EDIs", "data/global/Integradores"]
RESTRICTED_FILENAME = "technical_documentation.md"

def _transform_query(user_question):
    # "Eu não estou entendendo nada, mas vou fingir que sim e perguntar
    # ao Gemini de 5 formas diferentes. Vai que uma cola."
    """
    Usa um LLM (Gemini) para expandir e gerar variações da pergunta do usuário.
    Esta função só deve ser chamada para buscas GERAIS (sem @).
    """
    print(f"Transformando a pergunta original para busca geral: '{user_question}'")
    
    expansion_prompt = f"""Sua tarefa é agir como um especialista em reformulação de perguntas para um sistema de busca interno.
Dada a pergunta de um usuário, gere 3 variações que mantenham a intenção original, mas use sinônimos e diferentes estruturas de frase.
Isso ajudará o sistema de busca a encontrar documentos mais relevantes.

PERGUNTA ORIGINAL: "{user_question}"

Retorne apenas as 3 variações, uma por linha. Não adicione cabeçalhos ou texto extra.
"""
    
    try:
        gemini_model = get_client('gemini_model')
        if not gemini_model:
            raise ConnectionError("Modelo Gemini não está disponível para transformação da query.")

        response = gemini_model.generate_content(expansion_prompt)
        variations = response.text.strip().split('\n')
        cleaned_variations = [v.strip() for v in variations if v.strip()]
        
        if not cleaned_variations:
            print("AVISO: Transformação da query não retornou variações. Usando apenas a original.")
            return [user_question]

        print(f"Variações geradas: {cleaned_variations}")
        return [user_question] + cleaned_variations
        
    except Exception as e:
        print(f"ERRO ao transformar a query: {e}. Usando apenas a pergunta original.")
        return [user_question]

def find_context_for_question(user_question, available_modules, user_perms):
    """
    Orquestra a busca de contexto. Agora decide se transforma a query com base na presença de um filtro de módulo.
    """
    if not are_components_available():
        raise ConnectionError("Componentes da IA (DB Vetorial ou Embedding) não estão disponíveis.")

    collection = get_client('db_collection')
    embedding_model = get_client('embedding_model')

    # ETAPA 1: DETECÇÃO DE MÓDULO PRIMEIRO
    clean_question, query_filter = _build_query_filter(user_question, available_modules)
    
    queries_for_embedding = []
    # **LÓGICA CORRIGIDA**: Só transforma a pergunta se NENHUM filtro de módulo foi criado.
    if not query_filter:
        # É uma busca geral, então usamos a transformação para melhorar os resultados.
        queries_for_embedding = _transform_query(clean_question)
    else:
        # É uma busca focada com '@', usamos apenas a pergunta limpa. É mais rápido.
        print("Busca focada com '@' detectada. Pulando a etapa de transformação da pergunta.")
        queries_for_embedding = [clean_question]
    
    # ETAPA 2: GERAÇÃO DOS EMBEDDINGS
    print(f"Gerando embeddings para: {queries_for_embedding}")
    embeddings = genai.embed_content(
        model=embedding_model,
        content=queries_for_embedding,
        task_type="RETRIEVAL_QUERY"
    )['embedding']
    
    # ETAPA 3: BUSCA VETORIAL
    relevant_chunks = collection.query(
        query_embeddings=embeddings, 
        n_results=10, 
        where=query_filter if query_filter else None,
        include=["metadatas", "documents"]
    )

    # Fallback (continua útil)
    if not relevant_chunks['documents'][0] and query_filter:
        print(f"Busca filtrada por {query_filter} não retornou resultados. Tentando busca geral como fallback.")
        relevant_chunks = collection.query(
            query_embeddings=embeddings, 
            n_results=10,
            include=["metadatas", "documents"]
        )

    initial_docs = relevant_chunks['documents'][0]
    initial_metas = relevant_chunks['metadatas'][0]

    # ETAPA 4: FILTRAGEM POR PERMISSÃO
    can_view_tecnico = user_perms.get('can_view_tecnico', False)
    final_documents, final_metadatas = _filter_context_by_permission(
        initial_docs,
        initial_metas,
        can_view_tecnico
    )

    was_blocked_by_perm = bool(initial_docs and not final_documents and not can_view_tecnico)

    return final_documents, final_metadatas, was_blocked_by_perm

def _build_query_filter(user_question, available_modules):
    """Analisa a pergunta para detectar módulos e retorna a pergunta limpa e o filtro do ChromaDB."""
    clean_question = user_question
    query_filter = {}
    found_modules = []

    module_pattern = re.compile(r'@([\w-]+)')
    mentioned_modules = module_pattern.findall(user_question)
    if mentioned_modules:
        print(f"Detecção explícita com '@' encontrada: {mentioned_modules}")
        valid_modules = [m for m in mentioned_modules if m in available_modules]
        if valid_modules:
            found_modules = valid_modules
            clean_question = module_pattern.sub('', user_question).strip()
            print(f"Módulos válidos encontrados: {valid_modules}. Pergunta limpa: '{clean_question}'")

    if not found_modules:
        print("Nenhuma menção explícita válida. Tentando detecção implícita...")
        question_lower = clean_question.lower()
        found_modules = [module for module in available_modules if module.replace('-', ' ') in question_lower]

    if found_modules:
        query_filter = {"$or": [{"module": name} for name in found_modules]} if len(found_modules) > 1 else {"module": found_modules[0]}
        print(f"Busca FOCADA ativada. Filtro: {query_filter}")
    else:
        print("Nenhum módulo específico mencionado. Realizando busca GERAL.")
        
    return clean_question, query_filter

def _filter_context_by_permission(documents, metadatas, can_view_tecnico):
    """Filtra uma lista de documentos e metadados com base na permissão do usuário."""
    if can_view_tecnico:
        return documents, metadatas

    print("Verificando permissões no contexto retornado...")
    safe_documents, safe_metadatas = [], []
    for doc, meta in zip(documents, metadatas):
        source = meta.get('source', '')
        is_restricted_file = os.path.basename(source) == RESTRICTED_FILENAME
        is_restricted_path = any(source.replace('\\', '/').startswith(p) for p in RESTRICTED_PATHS)

        if not is_restricted_file and not is_restricted_path:
            safe_documents.append(doc)
            safe_metadatas.append(meta)
        else:
            print(f"Filtrando documento restrito para usuário sem permissão: {source}")
    
    print(f"Contexto filtrado. Documentos permitidos: {len(safe_documents)} de {len(documents)}")
    return safe_documents, safe_metadatas
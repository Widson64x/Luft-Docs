# routes/ia.py
import os
import chromadb
import google.generativeai as genai
from flask import Blueprint, render_template, request, jsonify
from dotenv import load_dotenv

ia_bp = Blueprint('ia_bp', __name__)
load_dotenv()

# --- CONFIGURAÇÃO (sem alterações aqui) ---
try:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("Chave da API do Gemini não encontrada.")
    
    genai.configure(api_key=api_key)
    generation_model = genai.GenerativeModel('gemini-1.5-flash-latest')
    embedding_model = 'models/text-embedding-004'
    
    chroma_client = chromadb.PersistentClient(path="./chroma_db")
    collection = chroma_client.get_collection(name="luftdocs_collection")
    
    print("Módulo de IA: Modelos e Banco de Dados Vetorial carregados com sucesso.")

except Exception as e:
    print(f"ERRO CRÍTICO no módulo de IA: {e}")
    generation_model = None; embedding_model = None; collection = None

# --- ROTA PARA A PÁGINA DE TESTES (sem alterações) ---
@ia_bp.route('/test_ia')
def test_ia_page():
    return render_template('pages/test_ia.html')

# --- ENDPOINT DE API (COM A NOVA LÓGICA DE BUSCA) ---
@ia_bp.route('/api/ask_llm', methods=['POST'])
def ask_llm_api():
    if not generation_model or not collection:
        return jsonify({"error": "Componentes da IA não estão configurados."}), 500

    data = request.get_json()
    if not data or 'user_question' not in data:
        return jsonify({"error": "Requisição inválida. Faltando 'user_question'."}), 400

    user_question = data['user_question'].lower() # Converte para minúsculas para facilitar a busca

    # --- LÓGICA DE FILTRO INTELIGENTE ---
    query_filter = {}
    # Mapeia palavras-chave para nomes de módulos
    module_keywords = {
        "recebimento": "recebimento-intec",
        "agendamento": "agendamento",
        # Adicione outros mapeamentos aqui conforme necessário
        # "palavra-chave": "nome-do-modulo"
    }

    found_modules = []
    for keyword, module_name in module_keywords.items():
        if keyword in user_question:
            found_modules.append(module_name)
    
    if found_modules:
        # Se mais de um módulo for encontrado, usa o operador $or
        if len(found_modules) > 1:
            query_filter = {"$or": [{"module": name} for name in found_modules]}
        # Se apenas um for encontrado, faz um filtro simples
        else:
            query_filter = {"module": found_modules[0]}
        print(f"Busca filtrada ativada. Filtro: {query_filter}")
    # Se nenhuma palavra-chave for encontrada, a busca será feita em todos os documentos (query_filter continua vazio)
    # -----------------------------------

    question_embedding = genai.embed_content(
        model=embedding_model,
        content=user_question,
        task_type="RETRIEVAL_QUERY"
    )['embedding']

    relevant_chunks = collection.query(
        query_embeddings=[question_embedding],
        n_results=5,
        where=query_filter if query_filter else None # Aplica o filtro na query!
    )
    
    # Se a busca filtrada não retornar nada, tenta uma busca geral como fallback
    if not relevant_chunks['documents'][0]:
        print("Busca filtrada não retornou resultados. Tentando busca geral.")
        relevant_chunks = collection.query(
            query_embeddings=[question_embedding],
            n_results=5
        )

    context = "\n---\n".join(relevant_chunks['documents'][0])
    sources = [meta['source'] for meta in relevant_chunks['metadatas'][0]]
    unique_sources = sorted(list(set(sources)))
    
    # O PROMPT PODE CONTINUAR O MESMO, POIS AGORA O CONTEXTO SERÁ PURO
    prompt = f"""
    Você é o 'Lia', o assistente de conhecimento gente boa da LuftDocs. Sua missão é ser um especialista focado que vai direto ao ponto.
    Sua tarefa principal: Analise os TRECHOS RELEVANTES DA DOCUMENTAÇÃO abaixo e responda à pergunta do usuário.
    O contexto que você recebe já foi pré-filtrado para ser relevante. Responda de forma clara e direta.

    **Regras para sua resposta:**
    1.  **Foco Total:** Responda EXATAMENTE o que o usuário perguntou usando o contexto.
    2.  **Honestidade:** Se a informação não estiver nos trechos, diga que não encontrou detalhes sobre aquele tópico específico.
    3.  **Estrutura Clara (Use Markdown):** Organize a resposta com títulos (`## Título`), negrito (`**palavra**`) e listas (`* item`).
    4.  **Saudação e Tom:** Comece com uma saudação amigável e mantenha um tom de colega para colega.

    --- TRECHOS RELEVANTES DA DOCUMENTAÇÃO ---
    {context}
    --- FIM DOS TRECHOS ---

    **Pergunta do usuário:** "{user_question}"
    """

    try:
        response = generation_model.generate_content(prompt)
        return jsonify({"answer": response.text, "context_files": unique_sources})
    except Exception as e:
        return jsonify({"error": f"Erro ao gerar resposta: {e}"}), 500
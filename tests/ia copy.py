# routes/ia.py
import os
import re
import chromadb
import google.generativeai as genai
import groq
import openai
from flask import Blueprint, render_template, request, jsonify
from dotenv import load_dotenv

ia_bp = Blueprint('ia_bp', __name__)
load_dotenv()

# --- LÓGICA PARA DESCOBRIR MÓDULOS AUTOMATICAMENTE ---
def get_available_modules():
    """Verifica o diretório data/modules e retorna uma lista com os nomes dos módulos."""
    try:
        modules_path = os.path.join("data", "modules")
        if not os.path.exists(modules_path):
            print("AVISO: Diretório 'data/modules' não encontrado. O filtro dinâmico não funcionará.")
            return []
        available = [d for d in os.listdir(modules_path) if os.path.isdir(os.path.join(modules_path, d))]
        print(f"Módulos descobertos automaticamente: {available}")
        return available
    except Exception as e:
        print(f"ERRO CRÍTICO ao descobrir módulos: {e}")
        return []

AVAILABLE_MODULES = get_available_modules()
# -------------------------------------------------------------

# --- CONFIGURAÇÃO PARA TODOS OS MODELOS ---
try:
    # Gemini
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key: raise ValueError("Chave da API do Gemini não encontrada.")
    genai.configure(api_key=gemini_api_key)
    embedding_model = 'models/text-embedding-004'
    gemini_generation_model = genai.GenerativeModel('gemini-1.5-flash-latest')

    # Groq
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key: raise ValueError("Chave da API do Groq não encontrada.")
    groq_client = groq.Groq(api_key=groq_api_key)

    # OpenAI (mesmo que desabilitado no frontend, o backend está pronto)
    openai_api_key = os.getenv("OPENAI_API_KEY")
    openai_client = openai.OpenAI(api_key=openai_api_key) if openai_api_key else None
    
    # ChromaDB
    chroma_client = chromadb.PersistentClient(path="./chroma_db")
    collection = chroma_client.get_collection(name="luftdocs_collection")
    
    print("Módulo de IA: Modelos (OpenAI, Groq, Gemini) e DB Vetorial carregados com sucesso.")

except Exception as e:
    print(f"ERRO CRÍTICO no setup da IA: {e}")
    openai_client = None; groq_client = None; gemini_generation_model = None; collection = None

@ia_bp.route('/test_ia')
def test_ia_page():
    return render_template('test_ia.html')

@ia_bp.route('/api/ask_llm', methods=['POST'])
def ask_llm_api():
    if not all([groq_client, gemini_generation_model, collection]):
        return jsonify({"error": "Componentes da IA não estão configurados."}), 500

    data = request.get_json()
    if not data or 'user_question' not in data:
        return jsonify({"error": "Requisição inválida."}), 400

    user_question = data['user_question']
    selected_model = data.get('selected_model', 'groq-70b') 

    # --- ETAPA 1: BUSCA DE CONTEXTO COM FILTRO DINÂMICO ---
    question_embedding = genai.embed_content(model=embedding_model, content=user_question, task_type="RETRIEVAL_QUERY")['embedding']
    query_filter = {}
    question_lower = user_question.lower()
    found_modules = [module for module in AVAILABLE_MODULES if module.replace('-', ' ') in question_lower]
    if found_modules:
        query_filter = {"$or": [{"module": name} for name in found_modules]} if len(found_modules) > 1 else {"module": found_modules[0]}
        print(f"Busca filtrada DINÂMICA ativada. Filtro: {query_filter}")
    else:
        print("Nenhum módulo específico mencionado na pergunta, realizando busca geral.")
    relevant_chunks = collection.query(query_embeddings=[question_embedding], n_results=5, where=query_filter if query_filter else None)
    if not relevant_chunks['documents'][0] and query_filter:
        print(f"Busca filtrada por {query_filter} não retornou resultados. Tentando busca geral como fallback.")
        relevant_chunks = collection.query(query_embeddings=[question_embedding], n_results=5)
    context = "\n---\n".join(relevant_chunks['documents'][0])
    sources = [meta['source'] for meta in relevant_chunks['metadatas'][0]]
    unique_sources = sorted(list(set(sources)))
    
    answer = ""
    try:
        # --- ETAPA 2: GERAÇÃO DA RESPOSTA COM PROMPTS COMPLETOS ---
        system_prompt = """Você é a 'Lia', a assistente de conhecimento gente boa da LuftDocs. Sua missão é ajudar seus colegas de equipe a encontrar informações de forma clara, amigável e descomplicada. Pense e responda como se fosse um colega de trabalho brasileiro: prestativo, um pouco informal e que vai direto ao ponto sem ser robótico. Use um toque de "malemolência" e bom humor.

**Suas regras de ouro para responder:**

1.  **Personalidade:**
    * **Saudação:** Comece sempre com um "Opa, vamos lá!", "Beleza! Encontrei isso aqui pra você:" ou algo nesse estilo descontraído.
    * **Tom:** Mantenha um tom conversacional e prestativo. Use emojis para dar um toque de personalidade quando fizer sentido (😉, 👍).
    * **Despedida:** Termine com algo amigável como "Qualquer outra dúvida, é só chamar!" ou "Espero que ajude!".

2.  **Estrutura da Resposta (Use Markdown):**
    * **Síntese:** Comece com um parágrafo curto resumindo a resposta direta para a pergunta.
    * **Títulos e Destaques:** Use títulos com `##` para separar seções e negrito (`**palavra**`) para destacar termos importantes.
    * **Listas:** Se for um processo com passos, use listas com marcadores (`*`).
    * **REGRA CRÍTICA PARA IMAGENS:** Se o contexto contiver um caminho para uma imagem (ex: `/data/img/tela/foto.png`), É SUA OBRIGAÇÃO **INCLUIR O CAMINHO EXATO DO ARQUIVO COMO TEXTO** na sua resposta, perto da descrição da imagem. Deixe o caminho do arquivo visível no texto.

3.  **Foco e Honestidade:**
    * Responda usando **apenas** o contexto fornecido.
    * Se a informação não estiver lá, seja honesta de forma amigável. Diga algo como: "Olha, dei uma boa fuçada aqui nos documentos, mas não achei os detalhes sobre isso. 🙁"

Lembre-se: seja a colega de trabalho que todo mundo gostaria de ter para tirar uma dúvida!"""
        human_prompt = f"**Contexto da Documentação:**\n{context}\n\n**Pergunta do Usuário:** \"{user_question}\""

        if selected_model == 'groq-70b':
            print("Gerando resposta com Groq (Llama 3 70b - Poderoso)...")
            chat_completion = groq_client.chat.completions.create(messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": human_prompt}], model="llama3-70b-8192")
            answer = chat_completion.choices[0].message.content

        elif selected_model == 'groq-8b':
            print("Gerando resposta com Groq (Llama 3 8b - Rápido)...")
            chat_completion = groq_client.chat.completions.create(messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": human_prompt}], model="llama3-8b-8192")
            answer = chat_completion.choices[0].message.content
        
        elif selected_model == 'openai' and openai_client:
            print("Gerando resposta com OpenAI (GPT-4o)...")
            chat_completion = openai_client.chat.completions.create(messages=[{"role": "system", "content": system_prompt}, {"role": "user", "content": human_prompt}], model="gpt-4o")
            answer = chat_completion.choices[0].message.content

        elif selected_model == 'gemini':
            print("Gerando resposta com Gemini (1.5 Flash)...")
            gemini_prompt = f"{system_prompt}\n---\n{human_prompt}"
            response = gemini_generation_model.generate_content(gemini_prompt)
            answer = response.text
        
        else:
            return jsonify({"error": f"Modelo '{selected_model}' inválido ou não configurado."}), 400

        # --- ETAPA 3: PÓS-PROCESSAMENTO À PROVA DE FALHAS PARA IMAGENS ---
        def force_image_formatting(text):
            processed_text = text.replace('/data/img/', '/data/img/')
            image_pattern = r'(/data/img/[^\s\)<]+\.(png|jpg|jpeg|gif))'
            replacement_format = r'\n\n![Imagem do Documento](\1)\n\n'
            final_text = re.sub(image_pattern, replacement_format, processed_text)
            return final_text
        final_answer = force_image_formatting(answer)

        return jsonify({"answer": final_answer, "context_files": unique_sources})

    except Exception as e:
        return jsonify({"error": f"Erro ao gerar resposta com {selected_model}: {e}"}), 500
# /ai_services/response_generator.py
import re
from .Configs.LLMConfig import get_client

SYSTEM_PROMPT = """Você é a 'Lia', a assistente de conhecimento gente boa da Luft. Sua missão é ajudar seus colegas de equipe a encontrar informações de forma clara, amigável e descomplicada. Pense e responda como se fosse um colega de trabalho brasileiro: prestativo, um pouco informal e que vai direto ao ponto sem ser robótico. Use um toque de "malemolência" e bom humor. Você é a funcionária Luft que tem o dever de responder tudo que se sabe da Luft com base no contexto.

**Suas regras de ouro para responder:**

1.  **Personalidade:**
    * **Saudação:** Comece sempre com um "Opa, vamos lá!", "Beleza! Encontrei isso aqui pra você:" ou algo nesse estilo descontraído.
    * **Tom:** Mantenha um tom conversacional e prestativo. Use emojis para dar um toque de personalidade quando fizer sentido (😉, 👍).
    * **Despedida:** Termine com algo amigável como "Qualquer outra dúvida, é só chamar!" ou "Espero que ajude!".

2.  **Estrutura da Resposta (Use Markdown):**
    * **Síntese:** Comece com um parágrafo curto resumindo a resposta direta para a pergunta.
    * **Títulos e Destaques:** Use títulos com `##` para separar seções e negrito (`**palavra**`) para destacar termos importantes.
    * **Listas:** Se for um processo com passos, use listas com marcadores (`*`).
    * **REGRA CRÍTICA PARA IMAGENS:** Se o contexto contiver um caminho para uma imagem (ex: `/data/img/tela/foto.png`), É SUA OBRIGAÇÃO **INCLUIR O CAMINHO EXATO DO ARQUIVO COMO TEXTO SIMPLES** na sua resposta. NUNCA formate o caminho da imagem como Markdown (NÃO use '![alt](caminho)'). Apenas escreva o caminho do arquivo diretamente no texto. O sistema se encarregará da formatação final.

3.  **Foco e Honestidade:**
    * IMPORTANTE: NUNCA traga informações que não estejam explicitamente presentes no contexto acima.
    * Se não achar a resposta, apenas diga que não foi possível encontrar nos documentos.
    * Não chute, não deduza, não invente. Seja 100% fiel ao que está no contexto.

Lembre-se: seja a colega de trabalho que todo mundo gostaria de ter para tirar uma dúvida!"""
#PS: Às vezes eu me pergunto... quem veio primeiro, o ovo ou o deploy em produção? 🤔

def rerank_and_filter_context(question, documents, metadatas):
    """
    Usa um modelo de linguagem poderoso (reranker) para reclassificar os documentos,
    retornando o contexto mais relevante e suas fontes.
    """
    print(f"Iniciando re-ranking de {len(documents)} documentos candidatos...")
    if not documents:
        return "", []

    reranker_prompt = f"""
Sua tarefa é atuar como um rigoroso assistente de pesquisa. Analise a PERGUNTA DO USUÁRIO e a lista de DOCUMENTOS numerados abaixo.
Para cada documento, avalie o quão diretamente ele responde à pergunta do usuário. Sua avaliação deve ser crítica.

Responda com uma lista em Python dos números dos documentos que são MAIS RELEVANTES e ÚTEIS, em ordem de importância.
O formato da resposta deve ser apenas a lista, como: `[3, 1, 5]`

Não explique sua decisão. Se nenhum documento for relevante, retorne uma lista vazia `[]`.

---
PERGUNTA DO USUÁRIO: "{question}"
---
DOCUMENTOS:
"""
    for i, doc in enumerate(documents):
        source = metadatas[i].get('source', 'desconhecida')
        reranker_prompt += f"\n{i+1}. [Fonte: {source}]:\n\"\"\"\n{doc}\n\"\"\"\n"

    try:
        # Usamos um modelo poderoso para esta tarefa de raciocínio.
        print("Usando Groq (Llama 3.3 70b) como reranker...")
        groq_client = get_client('groq_client')
        if not groq_client:
            raise ConnectionError("Cliente Groq não disponível para re-ranking.")

        chat_completion = groq_client.chat.completions.create(
            messages=[{"role": "user", "content": reranker_prompt}],
            model="llama-3.3-70b-versatile", # <-- NOVA CORREÇÃO 1
            temperature=0.0, # Baixa temperatura para uma resposta focada e determinística
        )
        response_text = chat_completion.choices[0].message.content
        
        # Extrai a lista de números da resposta do modelo
        ranked_indices_str = re.findall(r'\d+', response_text)
        ranked_indices = [int(i) - 1 for i in ranked_indices_str] # Converte para índices base-0

        print(f"Ordem de relevância definida pelo reranker: {[i+1 for i in ranked_indices]}")

        # Pega os 4 melhores documentos, conforme a ordem do reranker
        top_k = 4
        final_docs = []
        final_metas = []
        for i in ranked_indices:
            if i < len(documents):
                final_docs.append(documents[i])
                final_metas.append(metadatas[i])
        
        final_docs = final_docs[:top_k]
        final_metas = final_metas[:top_k]

        if not final_docs:
            print("Reranker concluiu que nenhum documento é relevante.")
            return "", []

        final_context = "\n---\n".join(final_docs)
        final_sources = [meta['source'] for meta in final_metas]
        
        print(f"Contexto final construído a partir de {len(final_docs)} documentos re-rankeados.")
        return final_context, sorted(list(set(final_sources)))

    except Exception as e:
        print(f"ERRO no re-ranking: {e}. Usando os documentos originais como fallback.")
        # Fallback: se o re-ranking falhar, usa os 3 primeiros documentos da busca original
        top_k = 3
        fallback_context = "\n---\n".join(documents[:top_k])
        fallback_sources = [meta['source'] for meta in metadatas[:top_k]]
        return fallback_context, sorted(list(set(fallback_sources)))

def generate_llm_answer(model_name, context, question):
    """Gera uma resposta usando o modelo de linguagem selecionado e o contexto já refinado."""
    human_prompt = f"**Contexto da Documentação:**\n{context}\n\n**Pergunta do Usuário:** \"{question}\""
    answer = ""
    
    print(f"Gerando resposta com {model_name}...")

    if model_name == 'groq-70b':
        print("Gerando resposta com Groq (Llama 3.3 70b - Poderoso)...")
        groq_client = get_client('groq_client')
        chat_completion = groq_client.chat.completions.create(messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": human_prompt}], model="llama-3.3-70b-versatile") # <-- NOVA CORREÇÃO 2
        answer = chat_completion.choices[0].message.content

    elif model_name == 'kimi':
        print("Gerando resposta com Moonshot Kimi (via Groq)...")
        groq_client = get_client('groq_client')
        chat_completion = groq_client.chat.completions.create(messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": human_prompt}], model="moonshotai/kimi-k2-instruct")
        answer = chat_completion.choices[0].message.content

    elif model_name == 'groq-8b':
        print("Gerando resposta com Groq (Llama 3 8b - Rápido)...")
        groq_client = get_client('groq_client')
        chat_completion = groq_client.chat.completions.create(messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": human_prompt}], model="llama3-8b-8192")
        answer = chat_completion.choices[0].message.content

    elif model_name == 'openai' and get_client('openai_client'):
        print("Gerando resposta com OpenAI (GPT-4o)...")
        openai_client = get_client('openai_client')
        chat_completion = openai_client.chat.completions.create(messages=[{"role": "system", "content": SYSTEM_PROMPT}, {"role": "user", "content": human_prompt}], model="gpt-4o")
        answer = chat_completion.choices[0].message.content

    elif model_name == 'gemini':
        print("Gerando resposta com Gemini (1.5 Flash)...")
        gemini_model = get_client('gemini_model')
        gemini_prompt = f"{SYSTEM_PROMPT}\n---\n{human_prompt}"
        response = gemini_model.generate_content(gemini_prompt)
        answer = response.text

    # --- INÍCIO DA NOVA ADIÇÃO (OPENROUTER) ---
    # O 'model_name' aqui é o que você vai colocar no <option> do seu HTML
    elif model_name == 'openrouter-gemini' and get_client('openrouter_client'):
        print("Gerando resposta com OpenRouter (google/gemini-2.5-flash)...")
        openrouter_client = get_client('openrouter_client')
        
        # A chamada é idêntica à do OpenAI/Groq
        chat_completion = openrouter_client.chat.completions.create(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": human_prompt}
            ],
            model="google/gemini-2.5-flash" # Este é o nome do modelo que o OpenRouter espera
        )
        answer = chat_completion.choices[0].message.content
    # --- FIM DA NOVA ADIÇÃO ---

    else:
        raise ValueError(f"Modelo '{model_name}' inválido ou não configurado.")
    
    return _force_image_formatting(answer)

def _force_image_formatting(text):
    """Garante que os caminhos de imagem sejam formatados corretamente como Markdown."""
    
    # Este padrão agora encontra o caminho da imagem, mesmo que não tenha o prefixo /luft-docs
    # Ele captura o caminho a partir de "/data/img/..."
    image_pattern = r'(/data/img/[^\s\)<]+\.(png|jpg|jpeg|gif))'
    
    # Montamos a URL completa na substituição, adicionando o prefixo do servidor e o /luft-docs
    # O `\1` representa o caminho da imagem que foi encontrado (ex: /data/img/recebimento-intec/img2.png)
    replacement_format = r'\n\n![Imagem do Documento](http://127.0.0.1:9100/luft-docs\1)\n\n' or r'\n\n![Imagem do Documento](http://b2bi-apps.luftfarma.com.br/luft-docs\1)\n\n'
    
    # A função `re.sub` vai encontrar todos os caminhos e aplicar a formatação
    final_text = re.sub(image_pattern, replacement_format, text)
    
    return final_text
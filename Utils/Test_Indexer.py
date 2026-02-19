import os
import chromadb
from chromadb.config import Settings
import google.generativeai as genai
from dotenv import load_dotenv
import sys
from pathlib import Path

# Adiciona o diretório pai ao sys.path para importar o Config, igual no Indexer
sys.path.append(str(Path(__file__).parent.parent))
from Config import VECTOR_DB_DIR

load_dotenv()

try:
    api_key = os.getenv("GEMINI_API_KEY")
    genai.configure(api_key=api_key)
    embedding_model = "models/gemini-embedding-001"
except Exception as e:
    print(f"Erro ao configurar a API do Gemini: {e}")
    exit()

def buscar_documentos(pergunta, n_resultados=3):
    """
    Busca no banco de dados ChromaDB os textos mais relevantes para a pergunta.
    """
    try:
        # 1. Inicia a conexão com o banco de dados
        client = chromadb.PersistentClient(
            path=str(VECTOR_DB_DIR),
            settings=Settings(anonymized_telemetry=False)
        )
        
        # 2. Conecta na mesma coleção que o Indexer criou
        collection = client.get_collection(name="luftdocs_collection")
        
        # 3. Transforma a pergunta em vetor (embedding)
        result = genai.embed_content(
            model=embedding_model,
            content=pergunta,
            task_type="RETRIEVAL_QUERY" # Note que mudou de DOCUMENT para QUERY
        )
        pergunta_embedding = result['embedding']
        
        # 4. Faz a busca no ChromaDB pelos vetores mais próximos
        resultados = collection.query(
            query_embeddings=[pergunta_embedding],
            n_results=n_resultados
        )
        
        # 5. Formata os resultados para leitura
        documentos_encontrados = resultados['documents'][0]
        metadados_encontrados = resultados['metadatas'][0]
        
        print(f"\n--- Resultados da Busca para: '{pergunta}' ---\n")
        for i, doc in enumerate(documentos_encontrados):
            fonte = metadados_encontrados[i].get('source', 'Desconhecida')
            print(f"Resultado {i+1} (Fonte: {fonte}):")
            print(f"{doc}\n")
            print("-" * 50)
            
        return documentos_encontrados
        
    except Exception as e:
        print(f"Erro ao buscar documentos: {e}")
        return None

if __name__ == "__main__":
    # Teste prático! Substitua pela pergunta que deseja fazer aos seus documentos.
    minha_pergunta = "Onde está configurado essa aplicação do LuftconnectAir?"
    buscar_documentos(minha_pergunta)
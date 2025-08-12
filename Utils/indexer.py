import os
import re 
import chromadb
import google.generativeai as genai
from dotenv import load_dotenv
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from Config import VECTOR_DB_DIR

print("Carregando variáveis de ambiente...")
load_dotenv()

try:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("Chave da API do Gemini não encontrada no arquivo .env")
    genai.configure(api_key=api_key)
    embedding_model = "models/text-embedding-004"
    print(f"API do Gemini configurada. Usando o modelo de embedding: {embedding_model}")
except Exception as e:
    print(f"Erro ao configurar a API do Gemini: {e}")
    exit()

def create_vector_db():
    print("Iniciando cliente ChromaDB...")
    client = chromadb.PersistentClient(path=str(VECTOR_DB_DIR))

    collection_name = "luftdocs_collection"
    if collection_name in [c.name for c in client.list_collections()]:
        print(f"Coleção '{collection_name}' existente encontrada. Deletando para recriar do zero.")
        client.delete_collection(name=collection_name)
        
    collection = client.create_collection(name=collection_name)
    print(f"Coleção '{collection_name}' criada com sucesso.")

    documents = []
    metadatas = []
    ids = []
    doc_id_counter = 0

    root_directory = "data"
    print(f"Iniciando varredura do diretório: {root_directory}")

    for root, dirs, files in os.walk(root_directory):
        if 'history' in dirs:
            print(f"Ignorando diretório de histórico: {os.path.join(root, 'history')}")
            dirs.remove('history')

        for file in files:
            if file.endswith(".md"):
                file_path = os.path.join(root, file)
                try:
                    path_parts = file_path.split(os.sep)
                    module_name = "geral" 
                    if "modules" in path_parts:
                        module_index = path_parts.index("modules") + 1
                        if module_index < len(path_parts):
                            module_name = path_parts[module_index]
                    
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()

    
                        # Em vez de dividir por parágrafos, dividimos pelo início de cada título (linhas que começam com #, ##, etc.)
                        # Isso cria blocos maiores e com mais contexto.
                        # O '(?=...)' garante que o título não seja removido na divisão, mas sim que faça parte do bloco.
                        chunks = re.split(r'\n(?=#{1,6} )', content.strip())
                        
                        # Filtramos para garantir que os blocos não sejam vazios ou muito pequenos
                        valid_chunks = [chunk for chunk in chunks if chunk.strip() and len(chunk.strip()) > 50]

                        for i, chunk in enumerate(valid_chunks):
                            documents.append(chunk)
                            metadatas.append({'source': file_path, 'module': module_name})
                            ids.append(f"id_{doc_id_counter}_{i}")
                        
                        doc_id_counter += 1
                    print(f"Processado: {file_path} (Módulo: {module_name}) -> {len(valid_chunks)} blocos criados.")
                except Exception as e:
                    print(f"Erro ao ler {file_path}: {e}")
    
    if not documents:
        print("Nenhum documento encontrado para indexar.")
        return

    print(f"\nTotal de {len(documents)} blocos de texto para indexar.")
    
    result = genai.embed_content(
        model=embedding_model,
        content=documents,
        task_type="RETRIEVAL_DOCUMENT"
    )
    embeddings = result['embedding']

    print(f"Embeddings gerados. Adicionando {len(ids)} itens ao ChromaDB...")
    
    batch_size = 100
    for i in range(0, len(ids), batch_size):
        end_index = i + batch_size
        collection.add(
            embeddings=embeddings[i:end_index],
            documents=documents[i:end_index],
            metadatas=metadatas[i:end_index],
            ids=ids[i:end_index]
        )
        print(f"Adicionado lote {i//batch_size + 1} ao banco de dados.")

    print("\nIndexação focada concluída com sucesso!")
    print(f"Total de itens na coleção: {collection.count()}")

if __name__ == "__main__":
    create_vector_db()
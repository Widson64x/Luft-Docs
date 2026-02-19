"""
Esse troço aqui serve para criar um vetor de dados que a IA vai ler para trazer boas respostas,
Não mexe nele por que nem eu sei como eu fiz isso daqui.
"""

import os
import re 
import time # Importado para pausar a execução e respeitar limites de cota
import chromadb
from chromadb.config import Settings
import google.generativeai as genai
from dotenv import load_dotenv
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from Config import VECTOR_DB_DIR, DATA_ROOT

print("Carregando variáveis de ambiente...")
load_dotenv()

try:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("Chave da API do Gemini não encontrada no arquivo .env")
    genai.configure(api_key=api_key)
    
    embedding_model = "models/gemini-embedding-001" 
    print(f"API do Gemini configurada. Usando o modelo de embedding: {embedding_model}")
except Exception as e:
    print(f"Erro ao configurar a API do Gemini: {e}")
    exit()

def create_vector_db():
    print("Iniciando cliente ChromaDB...")
    """Cria um banco de dados vetorial usando ChromaDB e gera embeddings para os documentos.

        O ChromaDB é um banco de dados vetorial que armazena embeddings gerados a partir de documentos.
        Ele é usado para realizar buscas semânticas eficientes, permitindo que a IA encontre informações relevantes com base no conteúdo dos documentos.
    """
    client = chromadb.PersistentClient(
        path=str(VECTOR_DB_DIR),
        settings=Settings(anonymized_telemetry=False)
    )

    collection_name = "luftdocs_collection"
    # Verifica se a coleção já existe e, se sim, deleta para recriar do zero, OBS: Uma coleção se resume em uma pasta dentro do VECTOR_DB_DIR, então isso é seguro de fazer sem afetar outros dados
    if collection_name in [c.name for c in client.list_collections()]:
        print(f"Coleção '{collection_name}' existente encontrada. Deletando para recriar do zero.")
        client.delete_collection(name=collection_name)
        
    collection = client.create_collection(name=collection_name)
    print(f"Coleção '{collection_name}' criada com sucesso.")

    documents = []
    metadatas = []
    ids = []
    doc_id_counter = 0
    
    root_directory = DATA_ROOT
    print(f"Iniciando varredura do diretório: {root_directory}")

    # Para cada arquivo markdown encontrado, vamos ler o conteúdo, dividir em blocos menores e gerar embeddings para cada bloco, associando metadados como o caminho do arquivo e o módulo correspondente (se aplicável).
    # embbendings: São representações numéricas do conteúdo dos documentos, geradas pelo modelo de embedding do Gemini. Eles permitem que a IA compreenda o significado semântico dos textos e realizem buscas eficientes.
    for root, dirs, files in os.walk(root_directory):
        if 'history' in dirs:
            print(f"Ignorando diretório de histórico: {os.path.join(root, 'history')}")
            dirs.remove('history')

        for file in files:
            if file.endswith(".md"):
                file_path = os.path.join(root, file)
                try:
                    path_parts = file_path.split(os.sep)
                    lower_parts = [p.lower() for p in path_parts]
                    module_name = "geral"
                    if "modules" in lower_parts:
                        idx = lower_parts.index("modules") + 1
                        if idx < len(path_parts):
                            module_name = path_parts[idx].lower()

                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()

                    chunks = re.split(r'\n(?=#{1,6} )', content.strip())
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
    
    embeddings = []
    embed_batch_size = 80 # Margem segura para o limite de 100/min
    total_batches = (len(documents) + embed_batch_size - 1) // embed_batch_size
    
    print("\nIniciando geração de embeddings em lotes (respeitando a cota gratuita)...")
    for i in range(0, len(documents), embed_batch_size):
        batch_docs = documents[i : i + embed_batch_size]
        current_batch = (i // embed_batch_size) + 1
        print(f"Processando lote {current_batch} de {total_batches} ({len(batch_docs)} documentos)...")
        
        success = False
        while not success:
            try:
                result = genai.embed_content(
                    model=embedding_model,
                    content=batch_docs,
                    task_type="RETRIEVAL_DOCUMENT"
                )
                embeddings.extend(result['embedding'])
                success = True
            except Exception as e:
                # Se der erro 429, esperamos e tentamos o mesmo lote de novo
                if "429" in str(e) or "ResourceExhausted" in str(e):
                    print("Limite de cota atingido (Erro 429). Aguardando 60 segundos para tentar novamente...")
                    time.sleep(60)
                else:
                    raise e
        
        # Pausa preventiva antes do próximo lote, a menos que seja o último
        if i + embed_batch_size < len(documents):
            print("Sucesso! Aguardando 60 segundos antes do próximo lote para evitar bloqueio...")
            time.sleep(60)

    print(f"\nTodos os embeddings gerados! Adicionando {len(ids)} itens ao ChromaDB...")
    
    # Adicionando ao ChromaDB em lotes para não sobrecarregar a memória
    db_batch_size = 100
    for i in range(0, len(ids), db_batch_size):
        end_index = i + db_batch_size
        collection.add(
            embeddings=embeddings[i:end_index],
            documents=documents[i:end_index],
            metadatas=metadatas[i:end_index],
            ids=ids[i:end_index]
        )
        print(f"Adicionado lote {i//db_batch_size + 1} ao banco de dados ChromaDB.")

    print("\nIndexação focada concluída com sucesso!")
    print(f"Total de itens na coleção: {collection.count()}")

if __name__ == "__main__":
    create_vector_db()
# /ai_services/llm_config.py
import os
import chromadb
from chromadb.config import Settings  # <--- Importação para telemetria
import google.generativeai as genai
import groq
import openai
from dotenv import load_dotenv
from Config import VECTOR_DB_DIR

# Constrói o caminho para o arquivo .env na raiz do projeto
project_root = os.path.join(os.path.dirname(__file__), '..', '..')
dotenv_path = os.path.join(project_root, '.env')
load_dotenv(dotenv_path=dotenv_path)

# Dicionário para armazenar clientes e modelos inicializados
clients = {}

try:
    # Gemini
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key: raise ValueError("Chave da API do Gemini não encontrada.")
    genai.configure(api_key=gemini_api_key)
    
    # --- ATUALIZADO: Usando o modelo correto de embedding ---
    clients['embedding_model'] = 'models/gemini-embedding-001'
    clients['gemini_model'] = genai.GenerativeModel('gemini-flash-latest')

    # Groq
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key: raise ValueError("Chave da API do Groq não encontrada.")
    clients['groq_client'] = groq.Groq(api_key=groq_api_key)

    # OpenAI
    openai_api_key = os.getenv("OPENAI_API_KEY")
    clients['openai_client'] = openai.OpenAI(api_key=openai_api_key) if openai_api_key else None

    # OpenRouter
    openrouter_api_key = os.getenv("OPEN_ROUTER_API_KEY")
    if openrouter_api_key:
        clients['openrouter_client'] = openai.OpenAI(
            api_key=openrouter_api_key,
            base_url="https://openrouter.ai/api/v1"
        )
    else:
        clients['openrouter_client'] = None

    # ChromaDB
    print("Configurando ChromaDB (Telemetria Desativada)...")
    chroma_settings = Settings(
        anonymized_telemetry=False
    )
    
    chroma_client = chromadb.PersistentClient(
        path=str(VECTOR_DB_DIR),
        settings=chroma_settings
    )
    
    # --- ATUALIZADO: Guardamos a conexão principal, não a coleção fixa ---
    clients['chroma_client'] = chroma_client

    print("Módulo de IA: Modelos (OpenAI, Groq, Gemini, OpenRouter) e DB Vetorial carregados com sucesso.")

except Exception as e:
    print(f"ERRO CRÍTICO no setup da IA: {e}")
    # Define todos como None em caso de erro para verificação posterior
    clients = {key: None for key in [
        'embedding_model', 'gemini_model', 'groq_client', 'openai_client', 
        'openrouter_client', 'chroma_client'
    ]}

def get_client(name):
    """Retorna um cliente, modelo ou configuração inicializada pelo nome."""
    
    # --- ATUALIZADO: Busca a coleção em tempo real (on-time) ---
    if name == 'db_collection':
        cliente_banco = clients.get('chroma_client')
        if cliente_banco:
            # Pega a versão mais recente da coleção direto do disco
            return cliente_banco.get_collection(name="luftdocs_collection")
        return None
        
    return clients.get(name)

def are_components_available():
    """
    Verifica se os componentes essenciais da IA estão disponíveis.
    """
    return all([
        get_client('groq_client'),
        get_client('gemini_model'),
        get_client('db_collection') # Isso vai acionar a busca real-time acima
    ])
    
""" Configurações Anteriores....

# /ai_services/llm_config.py
import os
import chromadb
import google.generativeai as genai
import groq
import openai
from dotenv import load_dotenv
from Config import VECTOR_DB_DIR

# --- INÍCIO DA CORREÇÃO ---
# Constrói o caminho para o arquivo .env na raiz do projeto
project_root = os.path.join(os.path.dirname(__file__), '..', '..')
dotenv_path = os.path.join(project_root, '.env')
load_dotenv(dotenv_path=dotenv_path)
# --- FIM DA CORREÇÃO ---

# O código original que carrega o .env (load_dotenv()) foi substituído pelo de cima

# Dicionário para armazenar clientes e modelos inicializados
clients = {}

try:
    # Gemini
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key: raise ValueError("Chave da API do Gemini não encontrada.")
    genai.configure(api_key=gemini_api_key)
    clients['embedding_model'] = 'models/text-embedding-004'
    clients['gemini_model'] = genai.GenerativeModel('gemini-flash-latest')

    # Groq
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key: raise ValueError("Chave da API do Groq não encontrada.")
    clients['groq_client'] = groq.Groq(api_key=groq_api_key)

    # OpenAI
    openai_api_key = os.getenv("OPENAI_API_KEY")
    clients['openai_client'] = openai.OpenAI(api_key=openai_api_key) if openai_api_key else None

    # ChromaDB
    chroma_client = chromadb.PersistentClient(path=str(VECTOR_DB_DIR))
    clients['db_collection'] = chroma_client.get_collection(name="luftdocs_collection")

    print("Módulo de IA: Modelos (OpenAI, Groq, Gemini) e DB Vetorial carregados com sucesso.")

except Exception as e:
    print(f"ERRO CRÍTICO no setup da IA: {e}")
    # Define todos como None em caso de erro para verificação posterior
    clients = {key: None for key in ['embedding_model', 'gemini_model', 'groq_client', 'openai_client', 'db_collection']}

def get_client(name):
    # Retorna um cliente, modelo ou configuração inicializada pelo nome.
    return clients.get(name)

def are_components_available():
    # Verifica se os componentes essenciais da IA estão disponíveis.
    return all([
        get_client('groq_client'),
        get_client('gemini_model'),
        get_client('db_collection')
    ])
"""
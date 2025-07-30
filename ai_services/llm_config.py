# /ai_services/llm_config.py
import os
import chromadb
import google.generativeai as genai
import groq
import openai
from dotenv import load_dotenv

load_dotenv()

# Dicionário para armazenar clientes e modelos inicializados
clients = {}

try:
    # Gemini
    gemini_api_key = os.getenv("GEMINI_API_KEY")
    if not gemini_api_key: raise ValueError("Chave da API do Gemini não encontrada.")
    genai.configure(api_key=gemini_api_key)
    clients['embedding_model'] = 'models/text-embedding-004'
    clients['gemini_model'] = genai.GenerativeModel('gemini-1.5-flash-latest')

    # Groq
    groq_api_key = os.getenv("GROQ_API_KEY")
    if not groq_api_key: raise ValueError("Chave da API do Groq não encontrada.")
    clients['groq_client'] = groq.Groq(api_key=groq_api_key)

    # OpenAI
    openai_api_key = os.getenv("OPENAI_API_KEY")
    clients['openai_client'] = openai.OpenAI(api_key=openai_api_key) if openai_api_key else None

    # ChromaDB
    chroma_client = chromadb.PersistentClient(path="./chroma_db")
    clients['db_collection'] = chroma_client.get_collection(name="luftdocs_collection")

    print("Módulo de IA: Modelos (OpenAI, Groq, Gemini) e DB Vetorial carregados com sucesso.")

except Exception as e:
    print(f"ERRO CRÍTICO no setup da IA: {e}")
    # Define todos como None em caso de erro para verificação posterior
    clients = {key: None for key in ['embedding_model', 'gemini_model', 'groq_client', 'openai_client', 'db_collection']}

def get_client(name):
    """Retorna um cliente, modelo ou configuração inicializada pelo nome."""
    return clients.get(name)

def are_components_available():
    """Verifica se os componentes essenciais da IA estão disponíveis."""
    return all([
        get_client('groq_client'),
        get_client('gemini_model'),
        get_client('db_collection')
    ])
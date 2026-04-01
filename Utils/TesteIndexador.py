from __future__ import annotations

import os
import sys
from pathlib import Path

import chromadb
import google.generativeai as genai
from chromadb.config import Settings
from dotenv import load_dotenv

sys.path.append(str(Path(__file__).parent.parent))

from Config import VECTOR_DB_DIR

load_dotenv()

CHAVE_API_GEMINI = os.getenv("GEMINI_API_KEY")
MODELO_EMBEDDING = "models/gemini-embedding-001"

if not CHAVE_API_GEMINI:
    raise ValueError("Chave da API do Gemini nao encontrada no arquivo .env")

genai.configure(api_key=CHAVE_API_GEMINI)


def BuscarDocumentos(pergunta: str, quantidadeResultados: int = 3) -> list[str] | None:
    """Busca os trechos mais relevantes no banco vetorial da aplicacao."""
    try:
        cliente = chromadb.PersistentClient(
            path=str(VECTOR_DB_DIR),
            settings=Settings(anonymized_telemetry=False),
        )
        colecao = cliente.get_collection(name="luftdocs_collection")
        resultado_embedding = genai.embed_content(
            model=MODELO_EMBEDDING,
            content=pergunta,
            task_type="RETRIEVAL_QUERY",
        )
        pergunta_embedding = resultado_embedding["embedding"]
        resultados = colecao.query(
            query_embeddings=[pergunta_embedding],
            n_results=quantidadeResultados,
        )
        return resultados["documents"][0]
    except Exception as erro:
        print(f"Erro ao buscar documentos: {erro}")
        return None


if __name__ == "__main__":
    BuscarDocumentos("Onde esta configurado essa aplicacao do LuftconnectAir?")
from __future__ import annotations

import os
from typing import Any

import chromadb
import google.generativeai as genai
import groq
import openai
from chromadb.config import Settings
from dotenv import load_dotenv

from Config import VECTOR_DB_DIR


class ConfiguracaoLLM:
    """Centraliza a configuracao e o acesso aos clientes da infraestrutura da LIA."""

    _clientes: dict[str, Any] | None = None

    @classmethod
    def obterCliente(cls, nome: str) -> Any:
        """Retorna um cliente ou modelo da infraestrutura da LIA pelo nome."""
        cls._garantirInicializacao()
        assert cls._clientes is not None

        if nome == "db_collection":
            cliente_banco = cls._clientes.get("chroma_client")
            if cliente_banco:
                return cliente_banco.get_collection(name="luftdocs_collection")
            return None

        return cls._clientes.get(nome)

    @classmethod
    def componentesDisponiveis(cls) -> bool:
        """Verifica se os componentes minimos para atender a LIA estao disponiveis."""
        return all(
            [
                cls.obterCliente("groq_client"),
                cls.obterCliente("gemini_model"),
                cls.obterCliente("db_collection"),
            ]
        )

    @classmethod
    def _garantirInicializacao(cls) -> None:
        if cls._clientes is not None:
            return

        load_dotenv(dotenv_path=cls._obterCaminhoDotenv())
        clientes: dict[str, Any] = {}

        try:
            chave_gemini = os.getenv("GEMINI_API_KEY")
            if not chave_gemini:
                raise ValueError("Chave da API do Gemini nao encontrada.")
            genai.configure(api_key=chave_gemini)
            clientes["embedding_model"] = "models/gemini-embedding-001"
            clientes["gemini_model"] = genai.GenerativeModel("gemini-flash-latest")

            chave_groq = os.getenv("GROQ_API_KEY")
            if not chave_groq:
                raise ValueError("Chave da API do Groq nao encontrada.")
            clientes["groq_client"] = groq.Groq(api_key=chave_groq)

            chave_openai = os.getenv("OPENAI_API_KEY")
            clientes["openai_client"] = (
                openai.OpenAI(api_key=chave_openai) if chave_openai else None
            )

            chave_openrouter = os.getenv("OPEN_ROUTER_API_KEY")
            clientes["openrouter_client"] = (
                openai.OpenAI(
                    api_key=chave_openrouter,
                    base_url="https://openrouter.ai/api/v1",
                )
                if chave_openrouter
                else None
            )

            configuracoes_chroma = Settings(anonymized_telemetry=False)
            clientes["chroma_client"] = chromadb.PersistentClient(
                path=str(VECTOR_DB_DIR),
                settings=configuracoes_chroma,
            )
            print(
                "Modulo de IA: modelos e DB vetorial carregados com sucesso."
            )
        except Exception as erro:
            print(f"ERRO CRITICO no setup da IA: {erro}")
            clientes = {
                chave: None
                for chave in [
                    "embedding_model",
                    "gemini_model",
                    "groq_client",
                    "openai_client",
                    "openrouter_client",
                    "chroma_client",
                ]
            }

        cls._clientes = clientes

    @staticmethod
    def _obterCaminhoDotenv() -> str:
        raiz_projeto = os.path.join(os.path.dirname(__file__), "..", "..")
        return os.path.join(os.path.abspath(raiz_projeto), ".env")

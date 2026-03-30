"""Ferramenta de indexacao vetorial utilizada pelos servicos de IA da aplicacao."""

from __future__ import annotations

import os
import re
import sys
import time
from pathlib import Path

import chromadb
import google.generativeai as genai
from chromadb.config import Settings
from dotenv import load_dotenv

sys.path.append(str(Path(__file__).parent.parent))

from Config import DATA_ROOT, VECTOR_DB_DIR

load_dotenv()

CHAVE_API_GEMINI = os.getenv("GEMINI_API_KEY")
MODELO_EMBEDDING = "models/gemini-embedding-001"

if not CHAVE_API_GEMINI:
    raise ValueError("Chave da API do Gemini nao encontrada no arquivo .env")

genai.configure(api_key=CHAVE_API_GEMINI)


def CriarBancoVetorial() -> None:
    """Recria o banco vetorial a partir dos documentos markdown da base."""
    cliente = chromadb.PersistentClient(
        path=str(VECTOR_DB_DIR),
        settings=Settings(anonymized_telemetry=False),
    )

    nome_colecao = "luftdocs_collection"
    if nome_colecao in [colecao.name for colecao in cliente.list_collections()]:
        cliente.delete_collection(name=nome_colecao)

    colecao = cliente.create_collection(name=nome_colecao)
    documentos: list[str] = []
    metadados: list[dict[str, str]] = []
    identificadores: list[str] = []
    contador_documentos = 0

    for raiz, diretorios, arquivos in os.walk(DATA_ROOT):
        if "history" in diretorios:
            diretorios.remove("history")

        for arquivo in arquivos:
            if not arquivo.endswith(".md"):
                continue

            caminho_arquivo = os.path.join(raiz, arquivo)
            try:
                partes_caminho = caminho_arquivo.split(os.sep)
                partes_minusculas = [parte.lower() for parte in partes_caminho]
                nome_modulo = "geral"
                if "modules" in partes_minusculas:
                    indice_modulo = partes_minusculas.index("modules") + 1
                    if indice_modulo < len(partes_caminho):
                        nome_modulo = partes_caminho[indice_modulo].lower()

                with open(caminho_arquivo, "r", encoding="utf-8") as arquivo_markdown:
                    conteudo = arquivo_markdown.read()

                blocos = re.split(r"\n(?=#{1,6} )", conteudo.strip())
                blocos_validos = [
                    bloco for bloco in blocos if bloco.strip() and len(bloco.strip()) > 50
                ]

                for indice_bloco, bloco in enumerate(blocos_validos):
                    documentos.append(bloco)
                    metadados.append({"source": caminho_arquivo, "module": nome_modulo})
                    identificadores.append(f"id_{contador_documentos}_{indice_bloco}")

                contador_documentos += 1
            except Exception as erro:
                print(f"Erro ao ler {caminho_arquivo}: {erro}")

    if not documentos:
        return

    embeddings = []
    tamanho_lote_embeddings = 80
    for indice in range(0, len(documentos), tamanho_lote_embeddings):
        lote_documentos = documentos[indice : indice + tamanho_lote_embeddings]
        sucesso = False
        while not sucesso:
            try:
                resultado = genai.embed_content(
                    model=MODELO_EMBEDDING,
                    content=lote_documentos,
                    task_type="RETRIEVAL_DOCUMENT",
                )
                embeddings.extend(resultado["embedding"])
                sucesso = True
            except Exception as erro:
                if "429" in str(erro) or "ResourceExhausted" in str(erro):
                    time.sleep(60)
                else:
                    raise

        if indice + tamanho_lote_embeddings < len(documentos):
            time.sleep(60)

    tamanho_lote_banco = 100
    for indice in range(0, len(identificadores), tamanho_lote_banco):
        fim_lote = indice + tamanho_lote_banco
        colecao.add(
            embeddings=embeddings[indice:fim_lote],
            documents=documentos[indice:fim_lote],
            metadatas=metadados[indice:fim_lote],
            ids=identificadores[indice:fim_lote],
        )


if __name__ == "__main__":
    CriarBancoVetorial()
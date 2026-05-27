from __future__ import annotations

import os
import re
from typing import Any

from flask import current_app

from Config import GLOBAL_DATA_DIR
from Utils.data.UtilitariosModulo import (
    CarregarMarkdown,
    CarregarMarkdownTecnico,
    CarregarModulos,
)

PASTAS_SUBMODULOS_RESTRITAS = ["Integradores"]


def ExtrairPreviaMidia(conteudo: str) -> dict[str, Any] | None:
    """Extrai a primeira imagem ou video de um conteudo para uso como previa."""

    def EhUrlAbsoluta(url: str) -> bool:
        return url.startswith(("http://", "https://", "//"))

    def ObterCaminhoRelativo(caminho: str, pastaTipoMidia: str) -> str | None:
        alvo = f"/data/{pastaTipoMidia}/"
        if alvo in caminho:
            return caminho.split(alvo)[-1]
        return None

    correspondencia_video = re.search(
        r'<video.*?>.*?<source.*?src=["\'](.*?)["\'].*?</video>',
        conteudo,
        re.IGNORECASE | re.DOTALL,
    )
    if correspondencia_video:
        caminho = correspondencia_video.group(1)
        if EhUrlAbsoluta(caminho):
            return {"type": "video", "path": caminho, "is_absolute": True}
        caminho_relativo = ObterCaminhoRelativo(caminho, "videos")
        if caminho_relativo:
            return {"type": "video", "path": caminho_relativo, "is_absolute": False}

    correspondencia_imagem = re.search(
        r'<img.*?src=["\'](.*?)["\']', conteudo, re.IGNORECASE
    )
    if correspondencia_imagem:
        caminho = correspondencia_imagem.group(1)
        if EhUrlAbsoluta(caminho):
            return {"type": "image", "path": caminho, "is_absolute": True}
        caminho_relativo = ObterCaminhoRelativo(caminho, "img")
        if caminho_relativo:
            return {"type": "image", "path": caminho_relativo, "is_absolute": False}

    correspondencia_imagem_markdown = re.search(r'!\[.*?\]\((.*?)\)', conteudo)
    if correspondencia_imagem_markdown:
        caminho = correspondencia_imagem_markdown.group(1)
        if EhUrlAbsoluta(caminho):
            return {"type": "image", "path": caminho, "is_absolute": True}
        caminho_relativo = ObterCaminhoRelativo(caminho, "img")
        if caminho_relativo:
            return {"type": "image", "path": caminho_relativo, "is_absolute": False}

    correspondencia_video_markdown = re.search(
        r'\[video\]\((.*?)\)', conteudo, re.IGNORECASE
    )
    if correspondencia_video_markdown:
        caminho = correspondencia_video_markdown.group(1)
        if EhUrlAbsoluta(caminho):
            return {"type": "video", "path": caminho, "is_absolute": True}
        caminho_relativo = ObterCaminhoRelativo(caminho, "videos")
        if caminho_relativo:
            return {"type": "video", "path": caminho_relativo, "is_absolute": False}

    return None


def BuscarTodosDocumentos(
    consulta: str,
    token: str,
    filtroModulo: str | None = None,
    podeVerTecnico: bool = False,
) -> list[dict[str, Any]]:
    """Realiza a busca textual em modulos principais, tecnicos e submodulos."""
    if not consulta:
        return []

    consulta_segura = re.escape(consulta)
    todos_modulos, _ = CarregarModulos()
    resultados = []
    parametro_token = f"&token={token}" if token else ""

    modulos_busca = todos_modulos
    if filtroModulo:
        modulos_busca = [modulo for modulo in todos_modulos if modulo["id"] == filtroModulo]

    for modulo in modulos_busca:
        identificador_modulo = modulo["id"]
        conteudo_documentacao = CarregarMarkdown(identificador_modulo)
        if conteudo_documentacao and re.search(
            consulta_segura, conteudo_documentacao, re.IGNORECASE
        ):
            resultados.append(
                {
                    "module_id": identificador_modulo,
                    "module_nome": modulo["nome"],
                    "module_icon": modulo.get("icon", "fas fa-file-alt"),
                    "doc_type": "Documentacao",
                    "url": f"/modulo?modulo={identificador_modulo}&q={consulta}{parametro_token}",
                    "content": conteudo_documentacao,
                    "preview": ExtrairPreviaMidia(conteudo_documentacao),
                }
            )

        if podeVerTecnico:
            conteudo_tecnico = CarregarMarkdownTecnico(identificador_modulo)
            if conteudo_tecnico and re.search(
                consulta_segura, conteudo_tecnico, re.IGNORECASE
            ):
                resultados.append(
                    {
                        "module_id": identificador_modulo,
                        "module_nome": modulo["nome"],
                        "module_icon": modulo.get("icon", "fas fa-cogs"),
                        "doc_type": "Tecnico",
                        "url": f"/modulo?modulo_tecnico={identificador_modulo}&q={consulta}{parametro_token}",
                        "content": conteudo_tecnico,
                        "preview": ExtrairPreviaMidia(conteudo_tecnico),
                    }
                )

    if filtroModulo:
        return resultados

    for raiz, _, arquivos in os.walk(GLOBAL_DATA_DIR):
        if not podeVerTecnico:
            componentes = raiz.replace("\\", "/").split("/")
            if any(pasta in componentes for pasta in PASTAS_SUBMODULOS_RESTRITAS):
                continue

        for arquivo in arquivos:
            if not arquivo.endswith(".md"):
                continue
            try:
                caminho_completo = os.path.join(raiz, arquivo)
                with open(caminho_completo, "r", encoding="utf-8") as arquivo_markdown:
                    conteudo = arquivo_markdown.read()

                if not re.search(consulta_segura, conteudo, re.IGNORECASE):
                    continue

                caminho_relativo = os.path.relpath(raiz, GLOBAL_DATA_DIR)
                identificador_arquivo = os.path.splitext(arquivo)[0]
                caminho_submodulo = os.path.join(caminho_relativo, identificador_arquivo).replace(
                    "\\", "/"
                )
                if caminho_submodulo.startswith("./"):
                    caminho_submodulo = caminho_submodulo[2:]

                resultados.append(
                    {
                        "module_id": caminho_submodulo,
                        "module_nome": identificador_arquivo.replace("_", " ").capitalize(),
                        "module_icon": "fas fa-globe",
                        "doc_type": os.path.basename(raiz),
                        "url": f"/modulo?submodulo={caminho_submodulo}&q={consulta}{parametro_token}",
                        "content": conteudo,
                        "preview": ExtrairPreviaMidia(conteudo),
                    }
                )
            except Exception as erro:
                current_app.logger.error(
                    "Erro ao ler o arquivo de submodulo %s: %s", arquivo, erro
                )

    return resultados
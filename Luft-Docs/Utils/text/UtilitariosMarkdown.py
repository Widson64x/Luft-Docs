from __future__ import annotations

import re
from urllib.parse import quote

import markdown
from flask import has_request_context, url_for

from Config import BASE_PREFIX, GLOBAL_DATA_DIR


def ConstruirUrlInterna(endpoint: str, **parametros: str | int) -> str:
    if has_request_context():
        return url_for(endpoint, **parametros)

    token = quote(str(parametros.get("token", "")), safe="")

    if endpoint == "Submodulo.exibirSubmodulo":
        nome = quote(str(parametros["nome"]), safe="")
        return f"{BASE_PREFIX}/submodulo/?nome={nome}&token={token}"

    if endpoint == "Modulo.exibirConteudoModulo":
        modulo = quote(str(parametros["modulo"]), safe="")
        return f"{BASE_PREFIX}/modulo/?modulo={modulo}&token={token}"

    raise RuntimeError(f"Endpoint nao suportado para links internos: {endpoint}")


def ConverterWikiLinks(
    conteudoMarkdown: str, modulos: list[dict], palavrasGlobais: dict[str, str]
) -> str:
    """Converte wikilinks em links HTML, tooltips ou texto simples."""

    def ConstruirLinkWiki(correspondencia: re.Match[str]) -> str:
        nome = correspondencia.group(1).strip()
        nome_arquivo = nome.replace(" ", "_") + ".md"

        if next(GLOBAL_DATA_DIR.rglob(nome_arquivo), None):
            return (
                f'<a href="{ConstruirUrlInterna("Submodulo.exibirSubmodulo", nome=nome, token="__TOKEN_PLACEHOLDER__")}">'
                f"{nome}</a>"
            )

        for modulo in modulos:
            if modulo["nome"].lower() == nome.lower():
                identificador_modulo = modulo["id"]
                return (
                    f'<a href="{ConstruirUrlInterna("Modulo.exibirConteudoModulo", modulo=identificador_modulo, token="__TOKEN_PLACEHOLDER__")}">'
                    f"{nome}</a>"
                )

        if nome in palavrasGlobais:
            tooltip = palavrasGlobais[nome]
            return f'<span class="tooltip" title="{tooltip}">{nome}</span>'

        return nome

    conteudo_com_links = re.sub(r"\[\[([^\]]+)\]\]", ConstruirLinkWiki, conteudoMarkdown)
    return markdown.markdown(conteudo_com_links, extensions=["extra"])
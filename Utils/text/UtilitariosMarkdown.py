from __future__ import annotations

import re

import markdown

from Config import GLOBAL_DATA_DIR


def ConverterWikiLinks(
    conteudoMarkdown: str, modulos: list[dict], palavrasGlobais: dict[str, str]
) -> str:
    """Converte wikilinks em links HTML, tooltips ou texto simples."""

    def ConstruirLinkWiki(correspondencia: re.Match[str]) -> str:
        nome = correspondencia.group(1).strip()
        nome_arquivo = nome.replace(" ", "_") + ".md"

        if next(GLOBAL_DATA_DIR.rglob(nome_arquivo), None):
            return (
                f'<a href="/luft-docs/submodule?nome={nome}&token=__TOKEN_PLACEHOLDER__">'
                f"{nome}</a>"
            )

        for modulo in modulos:
            if modulo["nome"].lower() == nome.lower():
                identificador_modulo = modulo["id"]
                return (
                    f'<a href="/luft-docs/modulo?modulo={identificador_modulo}&token=__TOKEN_PLACEHOLDER__">'
                    f"{nome}</a>"
                )

        if nome in palavrasGlobais:
            tooltip = palavrasGlobais[nome]
            return f'<span class="tooltip" title="{tooltip}">{nome}</span>'

        return nome

    conteudo_com_links = re.sub(r"\[\[([^\]]+)\]\]", ConstruirLinkWiki, conteudoMarkdown)
    return markdown.markdown(conteudo_com_links, extensions=["extra"])
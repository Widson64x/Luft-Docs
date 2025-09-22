# utils/text/markdown_utils.py

import re
import markdown
from pathlib import Path
from Config import GLOBAL_DATA_DIR

# Define o diretório base para submódulos para reuso e clareza.
GLOBAL_DATA_DIR = GLOBAL_DATA_DIR  # ou remova a definição local

def parser_wikilinks(conteudo_md, modulos, palavras_globais):
    """
    Converte wikilinks [[Nome]] em links HTML ou tooltips.

    - Converte para:
      - <a href="/submodule?nome=Nome&token=...">Nome</a> se 'Nome' for um submódulo.
      - <a href="/modulo?modulo=ID&token=...">Nome</a> se 'Nome' for um módulo.
      - <span class="tooltip" title="definição">Nome</span> se 'Nome' for uma palavra global.
    - Caso contrário, mantém apenas o texto 'Nome'.
    - O placeholder __TOKEN_PLACEHOLDER__ será substituído no template.
    """
    def link_modulo(match):
        nome = match.group(1).strip()
        nome_arquivo = nome.replace(" ", "_") + ".md"

        # --- LÓGICA DE BUSCA E GERAÇÃO DE LINK ATUALIZADA ---

        # 1) Verifica se é um submódulo (arquivo existe em data/global/**)
        if next(GLOBAL_DATA_DIR.rglob(nome_arquivo), None):
            # --- CORREÇÃO: Gera a URL com o prefixo /submodule e parâmetro 'nome' ---
            return f'<a href="/submodule?nome={nome}&token=__TOKEN_PLACEHOLDER__">{nome}</a>'

        # 2) Verifica se é um módulo
        for m in modulos:
            if m['nome'].lower() == nome.lower():
                # --- CORREÇÃO: Gera a URL com o prefixo /modulo ---
                return f'<a href="/modulo?modulo={m["id"]}&token=__TOKEN_PLACEHOLDER__">{nome}</a>'

        # 3) Se for uma palavra global, cria um tooltip
        if nome in palavras_globais:
            tooltip = palavras_globais[nome]
            return f'<span class="tooltip" title="{tooltip}">{nome}</span>'

        # 4) Caso contrário, retorna apenas o texto
        return nome

    # Substitui os [[wikilinks]] pelos links HTML corretos.
    conteudo_com_links = re.sub(r'\[\[([^\]]+)\]\]', link_modulo, conteudo_md)
    
    # Converte o Markdown restante (cabeçalhos, listas, etc.) para HTML.
    html_final = markdown.markdown(conteudo_com_links, extensions=['extra'])
    
    return html_final
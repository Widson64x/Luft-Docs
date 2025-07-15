# utils/markdown_utils.py

import re
import markdown
from pathlib import Path # <--- MODIFICAÇÃO: Importa a classe Path

# --- MODIFICAÇÃO: Define o diretório base como uma constante para reuso e clareza ---
GLOBAL_DATA_DIR = Path('data', 'global')

def parser_wikilinks(conteudo_md, modulos, palavras_globais):
    """
    - Converte [[Nome]] em:
      • <a href="/?token=__TOKEN_PLACEHOLDER__&submodulo=Nome">Nome</a> se Nome.md existir em data/global/ ou em suas subpastas. # <--- MODIFICAÇÃO: Docstring atualizada
      • <a href="/?token=__TOKEN_PLACEHOLDER__&modulo=<id>">Nome</a> se Nome for nome de módulo
      • <span class="tooltip" title="definição">Nome</span> se Nome estiver em palavras_globais
      • caso contrário, apenas o texto Nome.
    - O marcador __TOKEN_PLACEHOLDER__ será substituído no template pelo token real.
    """
    def link_modulo(match):
        nome = match.group(1).strip()
        nome_arquivo = nome.replace(" ", "_") + ".md"

        # --- LÓGICA DE BUSCA ATUALIZADA ---
        # 1) Se for submódulo (arquivo existe em data/global ou subpastas)
        # Usamos rglob para buscar recursivamente e next() para pegar o primeiro resultado.
        # Se nada for encontrado, o resultado é None.
        if next(GLOBAL_DATA_DIR.rglob(nome_arquivo), None):
            # O 'nome' na URL deve ser o original (com espaços), pois é o que a view espera.
            return f'<a href="/?token=__TOKEN_PLACEHOLDER__&submodulo={nome}">{nome}</a>'

        # 2) Se Nome corresponder a um módulo (comparando pelo campo 'nome' em modulos)
        for m in modulos:
            if m['nome'].lower() == nome.lower():
                return f'<a href="/?token=__TOKEN_PLACEHOLDER__&modulo={m["id"]}">{nome}</a>'

        # 3) Se Nome estiver em palavras_globais, exibir tooltip
        if nome in palavras_globais:
            tooltip = palavras_globais[nome]
            return f'<span class="tooltip" title="{tooltip}">{nome}</span>'

        # 4) Caso contrário, retornar apenas o texto
        return nome

    # Primeiro, substituímos os wikilinks [[...]] pelos respectivos links HTML.
    conteudo_com_links = re.sub(r'\[\[([^\]]+)\]\]', link_modulo, conteudo_md)
    
    # Em seguida, convertemos o Markdown resultante em HTML.
    html_final = markdown.markdown(conteudo_com_links, extensions=['extra'])
    
    return html_final
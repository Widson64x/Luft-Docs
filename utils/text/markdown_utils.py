# utils/markdown_utils.py

import os
import re
import markdown

def parser_wikilinks(conteudo_md, modulos, palavras_globais):
    """
    - Converte [[Nome]] em:
      • <a href="/?token=__TOKEN_PLACEHOLDER__&submodulo=Nome">Nome</a> se existir data/global/Nome.md
      • <a href="/?token=__TOKEN_PLACEHOLDER__&modulo=<id>">Nome</a> se Nome for nome de módulo
      • <span class="tooltip" title="definição">Nome</span> se Nome estiver em palavras_globais
      • caso contrário, apenas o texto Nome.
    - O marcador __TOKEN_PLACEHOLDER__ será substituído no template pelo token real.
    """
    def link_modulo(match):
        nome = match.group(1).strip()
        # Converte espaços em underscores para nomes de arquivo, uma prática comum.
        nome_arquivo = nome.replace(" ", "_") + ".md"
        submodulo_path = os.path.join('data', 'global', nome_arquivo)

        # 1) Se for submódulo (arquivo existe em data/global)
        if os.path.exists(submodulo_path):
            # O 'nome' na URL deve ser o original (com espaços, se houver),
            # pois é o que a view espera receber como parâmetro.
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
    # A extensão 'extra' habilita tabelas, listas, etc.
    # A extensão 'nl2br' foi REMOVIDA para permitir a renderização correta das listas.
    html_final = markdown.markdown(conteudo_com_links, extensions=['extra'])
    
    return html_final
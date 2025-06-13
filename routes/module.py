# routes/module.py

from flask import Blueprint, render_template, request, abort, session
from utils.data.module_utils import (
    carregar_modulos,
    get_modulo_by_id,
    carregar_markdown,
    carregar_markdown_tecnico,
    carregar_markdown_submodulo
)
from utils.text.markdown_utils import parser_wikilinks
from utils.data.module_access import register_access
from utils.text.advanced_filter import FiltroAvancado
from utils.auth.auth_utils import login_required

modulo_bp = Blueprint('modulo', __name__)
filtro = None

@modulo_bp.route('/', methods=['GET'])
@login_required
def ver_modulo_pela_raiz():
    """
    Agora, todo acesso a módulo ou submódulo ocorrerá via query string, por exemplo:
      - /?token=<TOKEN>&modulo=coordenacao
      - /?token=<TOKEN>&modulo/submodulo=CRM

    1) Primeiro, verificamos se veio parâmetro 'modulo/submodulo'; se sim, carregamos o submódulo.
    2) Caso contrário, tentamos obter 'modulo'; se vier, carregamos o módulo.
    3) Se nenhum dos dois parâmetros existir, devolvemos None para que outro handler (index) trate.
    """

    # 1) Tratamento de submódulo (prioritário sobre módulo)
    chave_sub = request.args.get('modulo/submodulo', '').strip()
    if chave_sub:
        modulos, palavras_globais = carregar_modulos()
        md_content = carregar_markdown_submodulo(chave_sub)
        if not md_content:
            return "<h2>Submódulo não encontrado.</h2>", 404

        register_access(chave_sub)
        conteudo_html = parser_wikilinks(md_content, modulos, palavras_globais)
        return render_template(
            'submodulo.html',
            nome=chave_sub,
            conteudo=conteudo_html,
            modulos=modulos
        )

    # 2) Tratamento de módulo
    modulo_id = request.args.get('modulo', '').strip()
    if not modulo_id:
        # Se não vier nem 'modulo/submodulo' nem 'modulo', deixamos passar para outro handler (index)
        return None

    # Carregar lista de módulos e palavras globais
    modulos, palavras_globais = carregar_modulos()
    global filtro
    if filtro is None:
        filtro = FiltroAvancado(palavras_globais)

    # Verificar se o módulo existe
    modulo = get_modulo_by_id(modulos, modulo_id)
    if not modulo:
        abort(404)

    # Registrar acesso e carregar o markdown correspondente
    register_access(modulo_id)

    # **AQUI**: seleção entre usuário comum e ADM
    nivel = session.get('permission', None)
    if nivel == 'ADM':
        # Apenas administradores carregam a documentação técnica
        md_content = carregar_markdown_tecnico(modulo_id)
        if not md_content:
            # Opcional: retornar 404 ou página específica caso não exista versão técnica
            return render_template('conteudo_nao_encontrado.html'), 404
    else:
        # Usuários não-ADM carregam a documentação geral
        md_content = carregar_markdown(modulo_id)
        if not md_content:
            return render_template('conteudo_nao_encontrado.html'), 404

    # Se houver pesquisa interna (query 'q'), faz filtro em md_content
    query = request.args.get('q', '').strip()
    if query:
        resultados = filtro.busca_avancada(md_content, query)
        if resultados:
            md_filtrado = "\n\n---\n\n".join(resultados)
            conteudo_html = parser_wikilinks(md_filtrado, modulos, palavras_globais)
            resultado_highlight = True
        else:
            conteudo_html = "<p class='text-danger'>Nenhum resultado encontrado.</p>"
            resultado_highlight = True
    else:
        conteudo_html = parser_wikilinks(md_content, modulos, palavras_globais)
        resultado_highlight = False

    # Identificar módulos relacionados
    relacionados = [m for m in modulos if m['id'] in modulo.get('relacionados', [])]

    # Renderiza o template de módulo
    return render_template(
        'modulo.html',
        modulo=modulo,
        conteudo=conteudo_html,
        relacionados=relacionados,
        modulos=modulos,
        modulo_atual=modulo,
        query=query,
        resultado_highlight=resultado_highlight
    )

from flask import Blueprint, render_template, request, abort
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
    Acessa módulo ou submódulo via query string:
      - /?token=<TOKEN>&modulo=submodulo
      - /?token=<TOKEN>&modulo_tecnico=agendamento
    """
    # 1) Submódulo (prioritário)
    chave_sub = request.args.get('modulo/submodulo', '').strip()
    if chave_sub:
        modulos, palavras_globais = carregar_modulos()
        md_content = carregar_markdown_submodulo(chave_sub)
        if not md_content:
            return "<h2>Submódulo não encontrado.</h2>", 404
        register_access(chave_sub)
        conteudo_html = parser_wikilinks(md_content, modulos, palavras_globais)
        return render_template(
            'submodule.html',
            nome=chave_sub,
            conteudo=conteudo_html,
            modulos=modulos
        )

    # 2) Módulo normal ou técnico
    param_mod = request.args.get('modulo', '').strip()
    param_tech = request.args.get('modulo_tecnico', '').strip()
    if not param_mod and not param_tech:
        # Sem parâmetro, delega para outro handler (index)
        return None

    is_tech = bool(param_tech)
    modulo_id = param_tech if is_tech else param_mod

    # Carregar módulos e inicializar filtro
    modulos, palavras_globais = carregar_modulos()
    global filtro
    if filtro is None:
        filtro = FiltroAvancado(palavras_globais)

    # Verificar existência do módulo
    modulo = get_modulo_by_id(modulos, modulo_id)
    if not modulo:
        abort(404)

    # Registrar acesso
    register_access(modulo_id)

    # Carregar conteúdo markdown conforme tipo
    if is_tech:
        md_content = carregar_markdown_tecnico(modulo_id)
        if not md_content:
            return "<h2>Módulo técnico não encontrado.</h2>", 404
    else:
        md_content = carregar_markdown(modulo_id)
        if not md_content:
            return "<h2>Módulo não encontrado.</h2>", 404

    # Busca interna (filtro)
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

    # Módulos relacionados
    relacionados = [m for m in modulos if m['id'] in modulo.get('relacionados', [])]

    # Renderizar template de módulo
    return render_template(
        'module.html',
        modulo=modulo,
        conteudo=conteudo_html,
        relacionados=relacionados,
        modulos=modulos,
        modulo_atual=modulo,
        query=query,
        resultado_highlight=resultado_highlight
    )

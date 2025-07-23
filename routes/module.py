# routes/module.py

from flask import Blueprint, render_template, request, abort, redirect, url_for, session
from utils.data.module_utils import (
    carregar_modulos,
    get_modulo_by_id,
    carregar_markdown,
    carregar_markdown_tecnico,
    carregar_markdown_submodulo
)
from utils.text.markdown_utils import parser_wikilinks
from utils.auth.auth_utils import login_required
from utils.text.service_filter import ContentFilterService
from utils.recommendation_service import log_document_access
from routes.permissions import get_user_group

# ✅ PASSO 1: Importe a lista de exceções, assim como fizemos antes.
from utils.permissions_config import MODULOS_TECNICOS_VISIVEIS

modulo_bp = Blueprint('modulo', __name__)
filter_service = ContentFilterService()

@modulo_bp.route('/', methods=['GET'])
@login_required
def ver_modulo_pela_raiz():
    """
    Renderiza o conteúdo de um módulo ou submódulo e regista o acesso
    com um ID único para documentos técnicos.
    """
    param_mod = request.args.get('modulo', '').strip()
    param_tech = request.args.get('modulo_tecnico', '').strip()
    param_sub = request.args.get('submodulo', '').strip()
    query = request.args.get('q', '').strip()

    modulos, palavras_globais = carregar_modulos()

    # --- Lógica para Submódulo (não alterada) ---
    if param_sub:
        md_content = carregar_markdown_submodulo(param_sub)
        if not md_content:
            abort(404, "Submódulo não encontrado.")
        log_document_access(param_sub)
        if query and md_content:
            md_content = filter_service.filter_submodule_content(md_content, query)
        conteudo_html = parser_wikilinks(md_content, modulos, palavras_globais)
        return render_template('submodule.html', nome=param_sub, conteudo=conteudo_html, modulos=modulos, query=query)

    # --- Lógica para Módulo Principal ---
    if not param_mod and not param_tech:
        return redirect(url_for('index.index'))

    is_tech = bool(param_tech)
    modulo_id = param_tech if is_tech else param_mod

    # ✅ PASSO 2: Implementa a verificação de permissão com a regra de exceção
    if is_tech:
        get_user_group() 
        user_perms = session.get('permissions', {})
        
        # Pega a permissão do usuário
        tem_permissao = user_perms.get('can_view_tecnico', False)
        
        # Verifica se o módulo solicitado está na lista de exceções
        eh_modulo_de_excecao = modulo_id in MODULOS_TECNICOS_VISIVEIS
        
        # BLOQUEIA o acesso SOMENTE SE o usuário NÃO tiver a permissão E o módulo NÃO for uma exceção.
        if not tem_permissao and not eh_modulo_de_excecao:
            # Se o usuário não tem permissão e o módulo não é uma exceção, negue o acesso.
            # Caso contrário (se ele tiver permissão OU se o módulo for uma exceção), o código continua normalmente.
            return render_template('access_denied.html'), 403

    modulo = get_modulo_by_id(modulos, modulo_id)
    if not modulo:
        abort(404, "Módulo não encontrado.")

    # (o restante do código permanece o mesmo)
    md_content = None
    if is_tech:
        md_content = carregar_markdown_tecnico(modulo_id)
        if query and md_content:
            md_content = filter_service.filter_technical_documentation(md_content, query)
    else:
        md_content = carregar_markdown(modulo_id)
        if query and md_content:
            md_content = filter_service.filter_documentation(md_content, query)

    if not md_content:
        return render_template('conteudo_nao_encontrado.html'), 404
    
    document_id_to_log = f"tech_{modulo_id}" if is_tech else modulo_id
    log_document_access(document_id_to_log)
    
    conteudo_html = parser_wikilinks(md_content, modulos, palavras_globais)
    relacionados_ids = modulo.get('relacionados', [])
    relacionados = [m for m in modulos if m['id'] in relacionados_ids]

    return render_template(
        'module.html',
        modulo=modulo,
        conteudo=conteudo_html,
        relacionados=relacionados,
        modulos=modulos,
        modulo_atual=modulo,
        query=query,
        resultado_highlight=bool(query)
    )
# routes/module.py

# Importa a biblioteca datetime para manipulação de datas e horas
from datetime import datetime
from flask import Blueprint, render_template, request, abort, redirect, url_for, session
from Utils.data.module_utils import (
    carregar_modulos,
    get_modulo_by_id,
    carregar_markdown,
    carregar_markdown_tecnico,
    carregar_markdown_submodulo
)
from Utils.text.markdown_utils import parser_wikilinks
from Utils.auth.auth_utils import login_required
from Utils.text.service_filter import ContentFilterService
from Utils.recommendation_service import log_document_access
from Routes.api.permissions import get_user_group

# Importa a lista de exceções para módulos técnicos
from Utils.permissions_config import MODULOS_TECNICOS_VISIVEIS

modulo_bp = Blueprint('modulo', __name__)
filter_service = ContentFilterService()

@modulo_bp.route('/', methods=['GET'])
@login_required
def ver_modulo_pela_raiz():
    """
    Renderiza o conteúdo de um módulo ou submódulo, processa informações de
    versão e registra o acesso ao documento, buscando dados do banco.
    """
    param_mod = request.args.get('modulo', '').strip()
    param_tech = request.args.get('modulo_tecnico', '').strip()
    param_sub = request.args.get('submodulo', '').strip()
    query = request.args.get('q', '').strip()

    # Carrega todos os módulos e palavras globais uma vez, para serem usados em todo o escopo
    # Esta é a maneira mais eficiente, pois evita múltiplas chamadas ao banco para a mesma requisição.
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
        return render_template('modules/submodule.html', nome=param_sub, conteudo=conteudo_html, modulos=modulos, query=query)

    # --- Lógica para Módulo Principal ---
    if not param_mod and not param_tech:
        return redirect(url_for('index.index'))

    is_tech = bool(param_tech)
    modulo_id = param_tech if is_tech else param_mod

    # --- Lógica de Permissões (não alterada) ---
    if is_tech:
        get_user_group() 
        user_perms = session.get('permissions', {})
        tem_permissao = user_perms.get('can_view_tecnico', False)
        eh_modulo_de_excecao = modulo_id in MODULOS_TECNICOS_VISIVEIS
        
        if not tem_permissao and not eh_modulo_de_excecao:
            return render_template('auth/access_denied.html'), 403

    # CORREÇÃO: A função get_modulo_by_id agora busca no banco usando apenas o ID.
    # No entanto, vamos filtrar a lista já carregada para evitar outra chamada ao banco.
    modulo = next((m for m in modulos if m["id"] == modulo_id), None)
    
    if not modulo:
        abort(404, "Módulo não encontrado.")

    # --- O restante da lógica de processamento de versão e renderização permanece o mesmo ---
    # A estrutura do dicionário 'modulo' é a mesma de antes, então o código subsequente
    # para extrair 'version_info', 'edit_history', etc., funcionará como esperado.

    versao_info = {
        'versao_atual': "N/A", 'data_aprovacao': "N/A", 'editor': "N/A"
    }
    version_data = modulo.get('version_info')
    edit_history = modulo.get('edit_history', [])

    if version_data:
        versao_atual = version_data.get('current_version')
        data_aprovacao_str = version_data.get('last_approved_on')
        data_aprovacao_formatada = "Data indisponível"
        if data_aprovacao_str:
            try:
                data_obj = datetime.fromisoformat(data_aprovacao_str)
                data_aprovacao_formatada = data_obj.strftime('%d/%m/%Y às %H:%M')
            except (ValueError, TypeError):
                pass
        
        editor_versao = "Não encontrado"
        for entrada in edit_history:
            if entrada.get('version') == versao_atual:
                editor_versao = entrada.get('editor') or entrada.get('user', 'Não encontrado')
                break
        
        versao_info.update({
            'versao_atual': versao_atual,
            'data_aprovacao': data_aprovacao_formatada,
            'editor': editor_versao
        })
    
    ultima_edicao = modulo.get('ultima_edicao')
    if ultima_edicao and 'data' in ultima_edicao and ultima_edicao['data']:
        try:
            data_obj = datetime.fromisoformat(ultima_edicao['data'])
            ultima_edicao['data_formatada'] = data_obj.strftime('%d/%m/%Y às %H:%M')
        except (ValueError, TypeError):
            ultima_edicao['data_formatada'] = "Data indisponível"

    md_content = carregar_markdown_tecnico(modulo_id) if is_tech else carregar_markdown(modulo_id)
    if query and md_content:
        if is_tech:
            md_content = filter_service.filter_technical_documentation(md_content, query)
        else:
            md_content = filter_service.filter_documentation(md_content, query)

    if not md_content:
        return render_template('auth/em_desenvolvimento.html'), 404
    
    log_document_access(f"tech_{modulo_id}" if is_tech else modulo_id)
    
    conteudo_html = parser_wikilinks(md_content, modulos, palavras_globais)
    relacionados_ids = modulo.get('relacionados', [])
    relacionados = [m for m in modulos if m['id'] in relacionados_ids]

    token = request.args.get('token', '')
    
    return render_template(
        'modules/module.html',
        modulo=modulo,
        conteudo=conteudo_html,
        relacionados=relacionados,
        modulos=modulos,
        modulo_atual=modulo,
        query=query,
        resultado_highlight=bool(query),
        versao_info=versao_info,
        proactive_module_name=modulo.get('nome', 'id'),
        proactive_module_id=modulo.get('id', ''),
        id_do_modulo=modulo_id ,
        token=token
    )

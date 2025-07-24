# routes/module.py

# Importa a biblioteca datetime para manipulação de datas e horas
from datetime import datetime
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

# Importa a lista de exceções para módulos técnicos
from utils.permissions_config import MODULOS_TECNICOS_VISIVEIS

modulo_bp = Blueprint('modulo', __name__)
filter_service = ContentFilterService()

@modulo_bp.route('/', methods=['GET'])
@login_required
def ver_modulo_pela_raiz():
    """
    Renderiza o conteúdo de um módulo ou submódulo, processa informações de
    versão e registra o acesso ao documento.
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

    # --- Lógica de Permissões (não alterada) ---
    if is_tech:
        get_user_group() 
        user_perms = session.get('permissions', {})
        
        tem_permissao = user_perms.get('can_view_tecnico', False)
        eh_modulo_de_excecao = modulo_id in MODULOS_TECNICOS_VISIVEIS
        
        if not tem_permissao and not eh_modulo_de_excecao:
            return render_template('access_denied.html'), 403

    modulo = get_modulo_by_id(modulos, modulo_id)
    if not modulo:
        abort(404, "Módulo não encontrado.")

    # --- INÍCIO DA NOVA LÓGICA DE VERSÃO ---
    # 1. Definimos um dicionário com valores padrão para as informações de versão.
    #    Isso evita erros caso o módulo não tenha essas informações no JSON.
    versao_info = {
        'versao_atual': "N/A",
        'data_aprovacao': "N/A",
        'editor': "N/A"
    }

    # 2. Acessamos os dados de 'version_info' e 'edit_history' do módulo.
    version_data = modulo.get('version_info')
    edit_history = modulo.get('edit_history', [])

    if version_data:
        # 3. Extraímos a versão atual e a data de aprovação.
        versao_atual = version_data.get('current_version')
        data_aprovacao_str = version_data.get('last_approved_on')

        # 4. Formatamos a data para um formato mais legível (dd/mm/aaaa às HH:MM).
        data_aprovacao_formatada = "Data indisponível"
        if data_aprovacao_str:
            try:
                data_obj = datetime.fromisoformat(data_aprovacao_str)
                data_aprovacao_formatada = data_obj.strftime('%d/%m/%Y às %H:%M')
            except (ValueError, TypeError):
                # Se a data estiver em um formato inválido, mantém o valor padrão.
                pass
        
        # 5. Procuramos pelo editor correspondente no histórico de edições.
        editor_versao = "Não encontrado"
        for entrada in edit_history:
            # Comparamos a versão da entrada do histórico com a versão atual do módulo.
            if entrada.get('version') == versao_atual:
                # O editor pode estar na chave 'editor' (para eventos de 'aprovado') 
                # ou 'user' (para eventos de 'criado').
                editor_versao = entrada.get('editor') or entrada.get('user', 'Não encontrado')
                break # Encontramos, então podemos sair do loop.

        # 6. Atualizamos o dicionário 'versao_info' com os dados corretos.
        versao_info.update({
            'versao_atual': versao_atual,
            'data_aprovacao': data_aprovacao_formatada,
            'editor': editor_versao
        })
    # --- FIM DA NOVA LÓGICA DE VERSÃO ---

    # --- Lógica de formatação de data da 'ultima_edicao' (código original mantido) ---
    ultima_edicao = modulo.get('ultima_edicao')
    if ultima_edicao and 'data' in ultima_edicao and ultima_edicao['data']:
        try:
            data_obj = datetime.fromisoformat(ultima_edicao['data'])
            ultima_edicao['data_formatada'] = data_obj.strftime('%d/%m/%Y às %H:%M')
        except (ValueError, TypeError):
            ultima_edicao['data_formatada'] = "Data indisponível"

    # --- Carregamento do conteúdo Markdown ---
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

    # --- Renderização final do Template ---
    # Passamos o novo dicionário 'versao_info' para o template HTML.
    return render_template(
        'module.html',
        modulo=modulo,
        conteudo=conteudo_html,
        relacionados=relacionados,
        modulos=modulos,
        modulo_atual=modulo,
        query=query,
        resultado_highlight=bool(query),
        versao_info=versao_info  # <<< Informações da versão adicionadas aqui
    )
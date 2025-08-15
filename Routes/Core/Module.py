# routes/module.py

# Importa a biblioteca datetime para manipulação de datas e horas
from datetime import datetime
from flask import Blueprint, render_template, request, abort, redirect, url_for, session
from sqlalchemy.orm import joinedload

# Importa os modelos do banco de dados e as funções utilitárias
from models import Modulo
from Utils.data.module_utils import (
    carregar_modulos,
    carregar_markdown,
    carregar_markdown_tecnico,
    carregar_markdown_submodulo
)
from Utils.text.markdown_utils import parser_wikilinks
from Utils.auth.auth_utils import login_required
from Utils.text.service_filter import ContentFilterService
from Utils.recommendation_service import log_document_access
from Routes.API.Permissions import get_user_group
from Utils.permissions_config import MODULOS_TECNICOS_VISIVEIS

# Criação do Blueprint e do serviço de filtro
modulo_bp = Blueprint('modulo', __name__)
filter_service = ContentFilterService()

@modulo_bp.route('/', methods=['GET'])
@login_required
def ver_modulo_pela_raiz():
    """
    Renderiza o conteúdo de um módulo ou submódulo, processa informações de
    versão e registra o acesso ao documento, buscando dados do banco.
    """
    # --- Bloco 1: Captura de Parâmetros (Mantido) ---
    param_mod = request.args.get('modulo', '').strip()
    param_tech = request.args.get('modulo_tecnico', '').strip()
    param_sub = request.args.get('submodulo', '').strip()
    query = request.args.get('q', '').strip()

    # Carrega a lista de módulos (dicionários) para o parser de wikilinks
    modulos_lista_dict, palavras_globais = carregar_modulos()

    # --- Bloco 2: Lógica para Submódulo (Mantido) ---
    if param_sub:
        md_content = carregar_markdown_submodulo(param_sub)
        if not md_content:
            abort(404, "Submódulo não encontrado.")
        log_document_access(param_sub)
        if query and md_content:
            md_content = filter_service.filter_submodule_content(md_content, query)
        conteudo_html = parser_wikilinks(md_content, modulos_lista_dict, palavras_globais)
        return render_template('Modules/SubModule.html', nome=param_sub, conteudo=conteudo_html, modulos=modulos_lista_dict, query=query)

    # --- Bloco 3: Lógica para Módulo Principal (Com todas as Correções) ---
    if not param_mod and not param_tech:
        return redirect(url_for('index.index'))

    is_tech = bool(param_tech)
    modulo_id = param_tech if is_tech else param_mod

    # --- Lógica de Permissões (Mantido) ---
    if is_tech:
        get_user_group()
        user_perms = session.get('permissions', {})
        tem_permissao = user_perms.get('can_view_tecnico', False)
        eh_modulo_de_excecao = modulo_id in MODULOS_TECNICOS_VISIVEIS
        if not tem_permissao and not eh_modulo_de_excecao:
            return render_template('Auth/AccessDenied.html'), 403

    # --- Busca de Dados Corrigida ---
    # Busca o objeto Modulo e seus relacionamentos diretamente do banco.
    modulo = Modulo.query.options(
        joinedload(Modulo.roteiros),
        joinedload(Modulo.relacionados),
        joinedload(Modulo.edit_history)
    ).filter_by(id=modulo_id).first()

    if not modulo:
        abort(404, "Módulo não encontrado.")

    # --- Processamento de Versão Corrigido ---
    versao_info = {
        'versao_atual': "N/A", 'data_aprovacao': "N/A", 'editor': "N/A"
    }
    
    versao_atual = modulo.current_version
    data_aprovacao_str = modulo.last_approved_on
    edit_history = modulo.edit_history

    if versao_atual and data_aprovacao_str:
        data_aprovacao_formatada = "Data indisponível"
        try:
            data_obj = datetime.fromisoformat(data_aprovacao_str)
            data_aprovacao_formatada = data_obj.strftime('%d/%m/%Y às %H:%M')
        except (ValueError, TypeError):
            pass

        editor_versao = "Não encontrado"
        for entrada in edit_history:
            if entrada.version == versao_atual:
                editor_versao = entrada.editor or "Não encontrado"
                break

        versao_info.update({
            'versao_atual': versao_atual,
            'data_aprovacao': data_aprovacao_formatada,
            'editor': editor_versao
        })

    # --- Lógica de Conteúdo (Mantido) ---
    md_content = carregar_markdown_tecnico(modulo_id) if is_tech else carregar_markdown(modulo_id)
    if query and md_content:
        if is_tech:
            md_content = filter_service.filter_technical_documentation(md_content, query)
        else:
            md_content = filter_service.filter_documentation(md_content, query)

    if not md_content:
        return render_template('Auth/Dev.html'), 404

    log_document_access(f"tech_{modulo_id}" if is_tech else modulo_id)

    conteudo_html = parser_wikilinks(md_content, modulos_lista_dict, palavras_globais)
    
    relacionados = modulo.relacionados
    
    #===================================================================
    # INÍCIO DA CORREÇÃO FINAL - ORDEM DA LÓGICA
    #===================================================================

    # 1. PREPARA OS DADOS DOS ROTEIROS - SEMPRE, PARA TODOS OS USUÁRIOS
    roteiros_data = [roteiro.to_dict() for roteiro in modulo.roteiros]
    
    # 2. VERIFICA A PERMISSÃO - APENAS PARA A FLAG DE CONTROLE
    get_user_group() # Garante que as permissões estejam na sessão
    user_perms = session.get('permissions', {})
    can_edit_scripts = user_perms.get('can_edit_scripts', False)

    token = request.args.get('token', '')

    # 3. RENDERIZA O TEMPLATE - ENVIANDO OS DADOS E A FLAG SEPARADAMENTE
    return render_template(
        'Modules/Module.html',
        modulo=modulo,
        conteudo=conteudo_html,
        relacionados=relacionados,
        modulos=modulos_lista_dict,
        query=query,
        resultado_highlight=bool(query),
        versao_info=versao_info,
        id_do_modulo=modulo_id,
        token=token,
        modulo_icone=modulo.icone or 'bi-box',
        modulo_atual=modulo,
        proactive_module_name=modulo.nome,
        proactive_module_id=modulo.id,
        
        # A lista de roteiros é enviada completa
        roteiros_data=roteiros_data,
        
        # A permissão é enviada para controlar os botões
        can_edit_scripts=can_edit_scripts
    )
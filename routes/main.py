import math
from flask import (
    Blueprint, render_template, session, redirect,
    url_for, request, send_from_directory, current_app
)
import os
from utils.data.module_utils import (
    carregar_modulos_aprovados,
    carregar_markdown
)
from utils.auth.auth_utils import authenticate_initial_request, logout_user, login_required
from utils.permissions_config import MODULOS_RESTRITOS, MODULOS_TECNICOS_VISIVEIS
from routes.permissions import get_user_group

# Define o Blueprint
index_bp = Blueprint('index', __name__)

CARDS_PER_PAGE = 10

@index_bp.context_processor
def inject_global_permissions():
    """Injeta permissões do usuário em todos os templates renderizados por este blueprint."""
    user_perms = session.get('permissions', {})
    return dict(
        can_view_tecnico=user_perms.get('can_view_tecnico', False),
        can_view_tools_in_development = user_perms.get('can_view_tools_in_development', False)
    )

@index_bp.route('/data/img/<path:nome_arquivo>')
def serve_imagem_dinamica(nome_arquivo):
    """Serve imagens da pasta /data/img."""
    caminho_base = os.path.join(current_app.root_path, 'data', 'img')
    return send_from_directory(caminho_base, nome_arquivo)

@index_bp.route('/data/videos/<path:nome_arquivo>')
def serve_video(nome_arquivo):
    """Serve vídeos da pasta /data/videos."""
    caminho_base = os.path.join(current_app.root_path, 'data', 'videos')
    return send_from_directory(caminho_base, nome_arquivo)


@index_bp.route('/', methods=['GET'])
def index():
    """
    Página inicial da aplicação.
    Apenas renderiza a estrutura base da página. Os módulos são carregados via API.
    """
    # 1. Autenticação continua igual
    resultado_auth = authenticate_initial_request()
    if resultado_auth is not True:
        return resultado_auth

    # 2. Permissões para os botões do cabeçalho
    user_perms = session.get('permissions', {})
    can_access_editor = user_perms.get('can_access_editor', False)
    can_access_permissions_menu = user_perms.get('can_access_permissions_menu', False)
    can_create_modules = user_perms.get('can_create_modules', False)
    can_view_tools_in_development = user_perms.get('can_view_tools_in_development', False)

    # 3. Renderiza o template base, sem passar a lista de módulos
    return render_template(
        'index.html',
        # Essas permissões ainda são necessárias para os botões no topo da página
        can_access_editor=can_access_editor,
        can_access_permissions_menu=can_access_permissions_menu,
        can_create_modules=can_create_modules, 
        can_view_tools_in_development=can_view_tools_in_development,
        menus=[]
    )

@index_bp.route('/mapa', methods=['GET'])
@login_required
def mapa_conhecimento():
    """
    Renderiza a página com o mapa de conhecimento interativo.
    """
    # 1. Autenticação garantida pelo decorator

    # 2. Permissões
    user_perms = session.get('permissions', {})
    can_access_editor = user_perms.get('can_access_editor', False)
    can_view_tecnico = user_perms.get('can_view_tecnico', False)
    can_access_permissions_menu = user_perms.get('can_access_permissions_menu', False)
    can_see_restricted_module = user_perms.get('can_see_restricted_module', False)

    # 3. Carrega e filtra os módulos visíveis
    modulos_aprovados, _ = carregar_modulos_aprovados()
    modulos_visiveis = []
    for m in modulos_aprovados:
        if m.get('id') in MODULOS_RESTRITOS:
            if can_see_restricted_module:
                modulos_visiveis.append(m)
        else:
            modulos_visiveis.append(m)
    
    # 4. Prepara dados para o mapa e a lógica do botão técnico
    ids_modulos_visiveis = {m['id'] for m in modulos_visiveis}
    for m in modulos_visiveis:
        if m.get('relacionados'):
            m['relacionados_visiveis'] = [rel_id for rel_id in m['relacionados'] if rel_id in ids_modulos_visiveis]
        else:
            m['relacionados_visiveis'] = []
            
        # ✅ PASSO 3: Replica a mesma lógica na rota do mapa para consistência
        m['show_tecnico_button'] = m['id'] in MODULOS_TECNICOS_VISIVEIS or can_view_tecnico

    # 5. Renderiza o template do mapa
    return render_template(
        'mapa.html', 
        modulos=modulos_visiveis,
        can_access_editor=can_access_editor,
        can_access_permissions_menu=can_access_permissions_menu,
        can_view_tecnico=can_view_tecnico
    )


@index_bp.route('/logout')
@login_required
def logout():
    """Realiza o logout do usuário e redireciona para a tela de logout."""
    logout_user()
    return render_template('logout.html')
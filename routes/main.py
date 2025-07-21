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
from utils.restricted_modules import MODULOS_RESTRITOS
from routes.permissions import get_user_group

# Define o Blueprint para a rota principal
index_bp = Blueprint('index', __name__)

# As rotas para servir arquivos estáticos como imagens e vídeos foram mantidas,
# pois são independentes da lógica principal.
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
    Autentica o usuário e exibe a lista de módulos disponíveis,
    preparando dados para as visualizações de card e mapa.
    """
    # 1. Autenticação
    resultado_auth = authenticate_initial_request()
    if resultado_auth is not True:
        return resultado_auth

    # 2. Permissões
    _, user_name = get_user_group()
    user_perms = session.get('permissions', {})
    can_access_editor = user_perms.get('can_access_editor', False)
    can_view_tecnico = user_perms.get('can_view_tecnico', False)
    can_access_permissions_menu = user_perms.get('can_access_permissions_menu', False)
    can_create_modules = user_perms.get('can_create_modules', False)
    can_see_restricted_module = user_perms.get('can_see_restricted_module', False)

    # 3. Carrega e filtra os módulos visíveis (mesma lógica de antes)
    modulos_aprovados, _ = carregar_modulos_aprovados()
    modulos_visiveis = []
    for m in modulos_aprovados:
        if m['id'] in MODULOS_RESTRITOS:
            if can_see_restricted_module:
                modulos_visiveis.append(m)
        else:
            modulos_visiveis.append(m)

    # 4. ✅ PREPARA OS DADOS PARA AMBAS AS VISUALIZAÇÕES
    ids_modulos_visiveis = {m['id'] for m in modulos_visiveis}
    for m in modulos_visiveis:
        # Para a visão de cards
        md_content = carregar_markdown(m['id'])
        m['has_content'] = bool(md_content and md_content.strip())
        
        # Para a visão de mapa
        if m.get('relacionados'):
            m['relacionados_visiveis'] = [rel_id for rel_id in m['relacionados'] if rel_id in ids_modulos_visiveis]
        else:
            m['relacionados_visiveis'] = []

    # 5. Renderiza o template, agora com todos os dados prontos
    return render_template(
        'index.html', 
        modulos=modulos_visiveis,
        can_access_editor=can_access_editor,
        can_view_tecnico=can_view_tecnico,
        can_access_permissions_menu=can_access_permissions_menu,
        can_create_modules=can_create_modules,
        menus=[]
    )

@index_bp.route('/mapa', methods=['GET'])
@login_required
def mapa_conhecimento():
    """
    Renderiza a página com o mapa de conhecimento interativo,
    seguindo o mesmo padrão de carregamento de dados e permissões da index.
    """
    # 1. Autenticação é garantida pelo decorator @login_required

    # 2. Permissões (carregadas no mesmo padrão da index)
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
    
    # 4. Prepara dados para o mapa (conexões)
    ids_modulos_visiveis = {m['id'] for m in modulos_visiveis}
    for m in modulos_visiveis:
        if m.get('relacionados'):
            m['relacionados_visiveis'] = [rel_id for rel_id in m['relacionados'] if rel_id in ids_modulos_visiveis]
        else:
            m['relacionados_visiveis'] = []

    # 5. Renderiza o template do mapa, passando a lista final de módulos e permissões
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
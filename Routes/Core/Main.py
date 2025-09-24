# Routes/core/main.py (Refatorado)

from flask import (
    Blueprint, render_template, session,
    url_for, request, send_from_directory, current_app, jsonify
)
import os
from Utils.data.module_utils import carregar_modulos_aprovados
from Utils.auth.auth_utils import authenticate_initial_request, logout_user, login_required
from Utils.permissions_config import MODULOS_RESTRITOS, MODULOS_TECNICOS_VISIVEIS
from Config import IMAGES_DIR, VIDEOS_DIR

# 1. Importe o objeto 'db' e o novo modelo 'BugReport'
from models import db, BugReport

# Define o Blueprint
index_bp = Blueprint('index', __name__)

@index_bp.context_processor
def inject_global_permissions():
    user_perms = session.get('permissions', {})
    return dict(
        can_view_tecnico=user_perms.get('can_view_tecnico', False),
        can_view_tools_in_development = user_perms.get('can_view_tools_in_development', False)
    )

@index_bp.route('/data/img/<path:nome_arquivo>')
def serve_imagem_dinamica(nome_arquivo):
    resp = send_from_directory(IMAGES_DIR, nome_arquivo)
    # resp.cache_control.max_age = 3600  # opcional
    return resp

@index_bp.route('/data/videos/<path:nome_arquivo>')
def serve_video(nome_arquivo):
    return send_from_directory(VIDEOS_DIR, nome_arquivo)

@index_bp.route('/', methods=['GET'])
def index():
    resultado_auth = authenticate_initial_request()
    if resultado_auth is not True:
        return resultado_auth

    user_perms = session.get('permissions', {})
    can_access_editor = user_perms.get('can_access_editor', False)
    can_access_permissions_menu = user_perms.get('can_access_permissions_menu', False)
    can_create_modules = user_perms.get('can_create_modules', False)
    can_view_tools_in_development = user_perms.get('can_view_tools_in_development', False)

    return render_template(
        'Index.html',
        can_access_editor=can_access_editor,
        can_access_permissions_menu=can_access_permissions_menu,
        can_create_modules=can_create_modules, 
        can_view_tools_in_development=can_view_tools_in_development,
        menus=[]
    )

@index_bp.route('/mapa', methods=['GET'])
@login_required
def mapa_conhecimento():
    user_perms = session.get('permissions', {})
    can_access_editor = user_perms.get('can_access_editor', False)
    can_view_tecnico = user_perms.get('can_view_tecnico', False)
    can_access_permissions_menu = user_perms.get('can_access_permissions_menu', False)
    can_see_restricted_module = user_perms.get('can_see_restricted_module', False)

    modulos_aprovados, _ = carregar_modulos_aprovados()
    modulos_visiveis = []
    for m in modulos_aprovados:
        if m.get('id') in MODULOS_RESTRITOS:
            if can_see_restricted_module:
                modulos_visiveis.append(m)
        else:
            modulos_visiveis.append(m)
    
    ids_modulos_visiveis = {m['id'] for m in modulos_visiveis}
    for m in modulos_visiveis:
        if m.get('relacionados'):
            m['relacionados_visiveis'] = [rel_id for rel_id in m['relacionados'] if rel_id in ids_modulos_visiveis]
        else:
            m['relacionados_visiveis'] = []
        m['show_tecnico_button'] = m['id'] in MODULOS_TECNICOS_VISIVEIS or can_view_tecnico

    return render_template(
        'Components/mapa.html', 
        modulos=modulos_visiveis,
        can_access_editor=can_access_editor,
        can_access_permissions_menu=can_access_permissions_menu,
        can_view_tecnico=can_view_tecnico
    )

@index_bp.route('/report-bug', methods=['POST'])
@login_required
def report_bug():
    """
    Recebe um reporte de bug e salva no banco de dados usando o ORM SQLAlchemy.
    """
    user_id = session.get('user_id')
    if not user_id:
        return jsonify({'success': False, 'message': 'Sessão inválida. Por favor, faça login novamente.'}), 403

    data = request.get_json()
    report_type = data.get('report_type')
    target_entity = data.get('target_entity')
    description = data.get('description')
    error_category = data.get('error_category')

    # --- Validações (sem alteração) ---
    if not report_type or report_type not in ['tela', 'modulo', 'geral', 'sugestao']:
        return jsonify({'success': False, 'message': 'O tipo de feedback é inválido.'}), 400
    if report_type in ['tela', 'modulo'] and not target_entity:
        return jsonify({'success': False, 'message': 'Para este tipo de feedback, é necessário especificar o alvo.'}), 400
    if report_type in ['tela', 'modulo'] and not error_category:
        return jsonify({'success': False, 'message': 'Por favor, selecione a categoria do problema.'}), 400
    if not description or len(description.strip()) < 10:
        return jsonify({'success': False, 'message': 'A descrição é obrigatória e deve conter pelo menos 10 caracteres.'}), 400

    try:
        # 2. Crie uma instância do seu modelo BugReport com os dados validados.
        novo_report = BugReport(
            user_id=user_id,
            report_type=report_type,
            target_entity=target_entity,
            error_category=error_category,
            description=description
            # O status e a data de criação são definidos por padrão no modelo.
        )
        
        # 3. Adicione o novo objeto à sessão do banco de dados e salve (commit).
        db.session.add(novo_report)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Feedback enviado com sucesso! Agradecemos sua colaboração.'}), 201

    except Exception as e:
        # 4. Em caso de erro, reverta a transação para não deixar o banco em estado inconsistente.
        db.session.rollback()
        current_app.logger.error(f"Erro ao inserir bug report para user_id {user_id}: {e}") 
        return jsonify({'success': False, 'message': 'Ocorreu um erro interno ao salvar seu feedback. Tente novamente mais tarde.'}), 500

@index_bp.route('/logout')
@login_required
def logout():
    """Realiza o logout do usuário e redireciona para a tela de logout."""
    logout_user()
    return render_template('Auth/Logout.html')

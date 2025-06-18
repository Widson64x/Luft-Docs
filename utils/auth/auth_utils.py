# utils/auth/auth_utils.py

from functools import wraps
from flask import session, request, redirect, url_for, render_template, current_app
import requests

from utils.auth.user_provider import get_user_by_credentials, get_user_by_token
from config import USER_API_URL
from utils.auth.user_field_map import USER_FIELD_MAP

# -----------------------------------------
# Autenticação e Sessão de Usuário
# -----------------------------------------

def map_user_fields(user_api):
    """Mapeia os campos do usuário da API para os nomes internos da aplicação."""
    return {USER_FIELD_MAP.get(k, k): v for k, v in user_api.items()}


def _populate_user_session(user_data_api):
    """
    Valida dados da API e popula sessão com usuário, grupo e permissões.
    """
    if not user_data_api or 'usuario' not in user_data_api:
        return False

    # --- Dados do Usuário ---
    user_api = user_data_api['usuario']
    user = map_user_fields(user_api)
    session['user_name'] = user.get('name')
    session['user_id'] = user.get('id')
    session['email'] = user.get('email')
    session['full_name'] = user.get('full_name')

    # --- Dados do Grupo ---
    group_api = user_data_api.get('grupo', {})
    session['user_group'] = {
        'group_code': group_api.get('codigo_usuariogrupo'),
        'acronym': group_api.get('Sigla_UsuarioGrupo'),
        'description': group_api.get('Descricao_UsuarioGrupo'),
    }

    # --- Permissões ---
    from routes.permissions import load_permissions
    perms_def = load_permissions()
    grupo = session['user_group']['acronym']
    usuario = session['user_name']
    session['permissions'] = {}
    for perm_name, info in perms_def.items():
        session['permissions'][perm_name] = (
            grupo in info.get('groups', []) or
            usuario in info.get('users', [])
        )

    # --- Token & Validade ---
    session['token'] = user_data_api.get('token')
    session['token_expiry'] = user_data_api.get('token_expira_em')
    session.permanent = False

    # DEBUG: imprime todo o conteúdo da sessão no console
    print("DEBUG SESSION ->", dict(session))

    return True


def validate_user_by_credentials():
    user_name = request.args.get('user_name', '').strip()
    if not user_name:
        return False
    user_data = get_user_by_credentials(user_name)
    return _populate_user_session(user_data)


def validate_user_by_token():
    token_raw = request.args.get('token', '').strip()
    if not token_raw:
        return False
    user_data = get_user_by_token(token_raw)
    return _populate_user_session(user_data)


def authenticate_initial_request():
    # Tenta token primeiro
    if validate_user_by_token():
        return True
    # Depois credenciais
    if validate_user_by_credentials():
        token = session.get('token')
        if token:
            return redirect(f"/?token={token}")
        return True
    # Falha
    return render_template("info_login.html"), 403


def login_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if 'user_name' not in session or 'user_id' not in session:
            return redirect(url_for('index.index'))
        return f(*args, **kwargs)
    return wrapped


def logout_user():
    token = session.get('token')
    if token:
        try:
            url = f"{USER_API_URL}/logout_token"
            resp = requests.post(url, json={"token": token}, timeout=3)
            resp.raise_for_status()
        except requests.RequestException as e:
            current_app.logger.error(f"Falha ao revogar token na API: {e}")
    session.clear()
    return True
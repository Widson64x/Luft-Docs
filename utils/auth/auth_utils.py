from functools import wraps
from flask import session, request, redirect, url_for, abort, render_template, current_app
from utils.auth.user_provider import get_user_by_credentials, get_user_by_token
from config import USER_API_URL
import requests
from utils.auth.user_field_map import USER_FIELD_MAP
from utils.auth.menu_map import MENU_MAP

def map_user_fields(usuario):
    """Mapeia os campos do usuário da API para os nomes internos."""
    return {USER_FIELD_MAP.get(k, k): v for k, v in usuario.items()}

def map_menus(menus_api):
    """Mapeia os menus da API para nomes internos."""
    return [MENU_MAP.get(menu.get("Codigo_Menu")) for menu in menus_api if menu.get("Codigo_Menu") in MENU_MAP]


def validar_usuario_por_credenciais():
    user_name = request.args.get('user_name', '').strip()
    if not user_name:
        return False
    user = get_user_by_credentials(user_name)
    print("DEBUG user:", user)
    if not user or 'usuario' not in user:
        return False
    usuario_api = user['usuario']
    usuario = map_user_fields(usuario_api)
    session['user_name'] = usuario.get('name')
    session['user_id']   = usuario.get('id')
    session['email']     = usuario.get('email')
    session['full_name'] = usuario.get('full_name')
    session['token']     = user.get('token')
    session['token_expira_em'] = user.get('token_expira_em')
    session['menus'] = map_menus(user.get('menus', []))
    session.permanent = False
    return True

def validar_usuario_por_token():
    token_raw = request.args.get('token', '').strip()
    if not token_raw:
        return False
    user = get_user_by_token(token_raw)
    print("DEBUG user by token:", user)
    if not user or 'usuario' not in user:
        return False
    usuario_api = user['usuario']
    usuario = map_user_fields(usuario_api)
    session['user_name'] = usuario.get('name')
    session['user_id']   = usuario.get('id')
    session['email']     = usuario.get('email')
    session['full_name'] = usuario.get('full_name')
    session['token']     = user.get('token')
    session['token_expira_em'] = user.get('token_expira_em')
    session['menus'] = map_menus(user.get('menus', []))
    session.permanent = False
    return True


def autenticar_request_inicial():
    """
    Tenta autenticar o usuário em duas etapas:
      1) Via token (se ?token= for fornecido)
      2) Via credenciais (se ?user_name= for fornecido)
    Se autenticar por credenciais, redireciona para URL com token.
    """
    if validar_usuario_por_token():
        return True
    if validar_usuario_por_credenciais():
        token = session.get('token')
        if token:
            return redirect(f"/?token={token}")
        return True
    # Se falhar, retorna página de acesso restrito
    return render_template("info_login.html"), 403


def login_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if 'user_name' not in session or 'user_id' not in session:
            return redirect(url_for('index.index'))
        return f(*args, **kwargs)
    return wrapped


def requires_permission(*cargos_permitidos):
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            cargo = session.get('permission')
            # Permite aceitar nomes internos ou usar a função can()
            if not cargo or cargo not in cargos_permitidos:
                return abort(403)
            return f(*args, **kwargs)
        return wrapped
    return decorator


def logout_user():
    """
    Revoga o token da API e limpa a sessão do usuário.
    """
    token = session.get('token')
    if token:
        try:
            url = f"{USER_API_URL}/logout_token"
            # current_app.logger.debug(f"Revocando token em {url}")
            resp = requests.post(url, json={"token": token}, timeout=2)
            resp.raise_for_status()
            print("DEBUG: Token revogado com sucesso.")
            print("URL DE LOGOUT:", url)
        except requests.RequestException as e:
            current_app.logger.error(f"Falha ao revogar token: {e}")
    session.clear()
    return True
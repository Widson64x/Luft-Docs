import os
import json
from flask import (
    Blueprint, session, jsonify, abort,
    request, render_template, redirect, url_for, flash
)
from Utils.auth.auth_utils import login_required
from Config import PERMISSION_PATH
from Utils.database_utils import get_db

permissions_bp = Blueprint('permissions', __name__, url_prefix='/permissions')

def load_permissions():
    with open(PERMISSION_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_permissions(data):
    with open(PERMISSION_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def get_user_group():
    group = session.get("user_group", {}).get("acronym", "")
    user_name = session.get("user_name", "")
    return group, user_name

@permissions_bp.route('/check/<permission>', methods=['GET'])
@login_required
def check_permission(permission):
    group, user_name = get_user_group()
    permissions = load_permissions()
    perm_info = permissions.get(permission, {})
    allowed = (
        group in perm_info.get("groups", []) or
        user_name in perm_info.get("users", [])
    )
    return jsonify({"allowed": allowed})

@permissions_bp.route('/my-group', methods=['GET'])
@login_required
def my_group():
    group, user_name = get_user_group()
    permissions = load_permissions()
    group_perms = {
        perm: info
        for perm, info in permissions.items()
        if group in info.get("groups", []) or user_name in info.get("users", [])
    }
    return jsonify({
        "user": user_name,
        "group": group,
        "permissions": group_perms,
    })

@permissions_bp.route('/', methods=['GET', 'POST'])
@login_required
def manage_permissions():
    # 1) captura e exige o token em todos os acessos
    token = request.args.get('token', '').strip()
    if not token:
        abort(401, description="Token JWT é obrigatório para acessar esta página")

    permissions = load_permissions()

    if request.method == "POST":
        action = request.values.get('action', '').strip()

        if action == 'update_perm':
            perm_name = request.form.get('perm_name', '').strip()
            if perm_name in permissions:
                # atualiza descrição
                description = request.form.get('description', '').strip()
                permissions[perm_name]['description'] = description

                # atualiza grupos
                groups = request.form.get('groups', '')
                permissions[perm_name]['groups'] = [
                    g.strip() for g in groups.split(',') if g.strip()
                ]
                # atualiza usuários
                users = request.form.get('users', '')
                permissions[perm_name]['users'] = [
                    u.strip() for u in users.split(',') if u.strip()
                ]
                save_permissions(permissions)
                flash(f"Permissão '{perm_name}' atualizada.", "success")
            else:
                flash("Permissão não encontrada.", "danger")

        elif action == 'add_perm':
            perm_name = request.form.get('new_perm_name', '').strip()
            description = request.form.get('new_perm_desc', '').strip()
            if perm_name and perm_name not in permissions:
                permissions[perm_name] = {
                    "description": description,
                    "groups": [],
                    "users": []
                }
                save_permissions(permissions)
                flash(f"Permissão '{perm_name}' criada.", "success")
            else:
                flash("Permissão inválida ou já existe.", "danger")

        elif action == 'delete_perm':
            perm_name = request.form.get('delete_perm', '').strip()
            if perm_name in permissions:
                del permissions[perm_name]
                save_permissions(permissions)
                flash(f"Permissão '{perm_name}' removida.", "success")
            else:
                flash("Permissão não encontrada.", "danger")

        # 2) redireciona repassando o token
        return redirect(
            url_for('permissions.manage_permissions', token=token)
        )

    # 3) renderiza o template, também passando o token para os links internos
    return render_template(
        'modules/manage_permissions.html',
        permissions=permissions,
        token=token
    )

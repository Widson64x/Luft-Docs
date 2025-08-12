# permissions.py (Refatorado com SQLAlchemy)

from flask import (
    Blueprint, session, jsonify, abort,
    request, render_template, redirect, url_for, flash
)
from Utils.auth.auth_utils import login_required
# Importa o objeto 'db' e os models do seu novo arquivo de modelos
from models import db, Permissao, Grupo, Usuario, permissoes_grupos, permissoes_usuarios

permissions_bp = Blueprint('permissions', __name__, url_prefix='/permissions')

def load_permissions():
    """
    Carrega todas as permissões do banco de dados usando o ORM e as formata 
    em um dicionário, como na versão original.
    """
    # Consulta todos os objetos Permissao, ordenados por nome.
    todas_permissoes = Permissao.query.order_by(Permissao.nome).all()
    
    # Constrói o dicionário no formato que o template espera.
    permissions_dict = {
        p.nome: {
            "description": p.descricao,
            # O ORM facilita o acesso a dados relacionados.
            "groups": [g.nome for g in p.grupos],
            "users": [u.nome for u in p.usuarios]
        } for p in todas_permissoes
    }
    return permissions_dict

def save_permissions(data):
    """
    ATENÇÃO: Esta função recria todo o banco de dados de permissões a partir de um dicionário.
    Ela foi mantida para compatibilidade com a estrutura original, mas é um padrão
    MUITO INEFICIENTE e NÃO RECOMENDADO para produção.
    A nova rota 'manage_permissions' faz as alterações de forma muito mais otimizada.
    """
    try:
        # Apaga todos os dados existentes em cascata.
        db.session.query(permissoes_grupos).delete()
        db.session.query(permissoes_usuarios).delete()
        db.session.query(Grupo).delete()
        db.session.query(Usuario).delete()
        db.session.query(Permissao).delete()
        
        # Recria tudo a partir do dicionário 'data'.
        for perm_name, perm_info in data.items():
            # Cria a permissão
            permissao_obj = Permissao(nome=perm_name, descricao=perm_info.get("description", ""))
            
            # Adiciona os grupos
            for group_name in perm_info.get("groups", []):
                grupo_obj = Grupo.query.filter_by(nome=group_name).first() or Grupo(nome=group_name)
                permissao_obj.grupos.append(grupo_obj)

            # Adiciona os usuários
            for user_name in perm_info.get("users", []):
                usuario_obj = Usuario.query.filter_by(nome=user_name).first() or Usuario(nome=user_name)
                permissao_obj.usuarios.append(usuario_obj)
            
            db.session.add(permissao_obj)
        
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        raise e

def get_user_group():
    """
    Obtém o grupo e o nome de usuário da sessão atual. (Sem alterações)
    """
    group = session.get("user_group", {}).get("acronym", "")
    user_name = session.get("user_name", "")
    return group, user_name

@permissions_bp.route('/check/<permission_name>', methods=['GET'])
@login_required
def check_permission(permission_name):
    """
    Verifica se o usuário atual tem uma permissão específica usando o ORM.
    """
    group_name, user_name = get_user_group()
    
    # A consulta com 'any' é a forma eficiente do SQLAlchemy de verificar relacionamentos.
    permissao_existe = db.session.query(Permissao.query.filter(
        Permissao.nome == permission_name,
        db.or_(
            Permissao.grupos.any(nome=group_name),
            Permissao.usuarios.any(nome=user_name)
        )
    ).exists()).scalar()

    return jsonify({"allowed": permissao_existe})

@permissions_bp.route('/my-group', methods=['GET'])
@login_required
def my_group():
    """
    Retorna todas as permissões associadas ao grupo ou usuário atual.
    """
    group_name, user_name = get_user_group()

    permissoes = Permissao.query.filter(
        db.or_(
            Permissao.grupos.any(nome=group_name),
            Permissao.usuarios.any(nome=user_name)
        )
    ).all()

    group_perms = {
        p.nome: {
            "description": p.descricao,
            "groups": [g.nome for g in p.grupos],
            "users": [u.nome for u in p.usuarios]
        } for p in permissoes
    }
    
    return jsonify({
        "user": user_name,
        "group": group_name,
        "permissions": group_perms,
    })

@permissions_bp.route('/', methods=['GET', 'POST'])
@login_required
def manage_permissions():
    """
    Página para gerenciar permissões. Agora usa o ORM para todas as operações.
    """
    token = request.args.get('token', '').strip()
    if not token:
        abort(401, description="Token JWT é obrigatório para acessar esta página")

    if request.method == "POST":
        action = request.values.get('action', '').strip()
        
        try:
            if action == 'update_perm':
                perm_name = request.form.get('perm_name', '').strip()
                permissao = Permissao.query.filter_by(nome=perm_name).first()
                if permissao:
                    permissao.descricao = request.form.get('description', '').strip()

                    group_names = {g.strip() for g in request.form.get('groups', '').split(',') if g.strip()}
                    permissao.grupos = [Grupo.query.filter_by(nome=name).first() or Grupo(nome=name) for name in group_names]

                    user_names = {u.strip() for u in request.form.get('users', '').split(',') if u.strip()}
                    permissao.usuarios = [Usuario.query.filter_by(nome=name).first() or Usuario(nome=name) for name in user_names]
                    
                    db.session.commit()
                    flash(f"Permissão '{perm_name}' atualizada.", "success")
                else:
                    flash("Permissão não encontrada.", "danger")

            elif action == 'add_perm':
                perm_name = request.form.get('new_perm_name', '').strip()
                if perm_name and not Permissao.query.filter_by(nome=perm_name).first():
                    nova_permissao = Permissao(
                        nome=perm_name, 
                        descricao=request.form.get('new_perm_desc', '').strip()
                    )
                    db.session.add(nova_permissao)
                    db.session.commit()
                    flash(f"Permissão '{perm_name}' criada.", "success")
                else:
                    flash("Permissão inválida ou já existe.", "danger")

            elif action == 'delete_perm':
                perm_name = request.form.get('delete_perm', '').strip()
                permissao = Permissao.query.filter_by(nome=perm_name).first()
                if permissao:
                    db.session.delete(permissao)
                    db.session.commit()
                    flash(f"Permissão '{perm_name}' removida.", "success")
                else:
                    flash("Permissão não encontrada.", "danger")
            
        except Exception as e:
            db.session.rollback()
            flash(f"Ocorreu um erro no banco de dados: {e}", "danger")

        return redirect(url_for('permissions.manage_permissions', token=token))

    # Na requisição GET, carrega as permissões para exibir na página.
    permissions_data = load_permissions()

    return render_template(
        'Pages/MG_Permissions.html',
        permissions=permissions_data,
        token=token
    )

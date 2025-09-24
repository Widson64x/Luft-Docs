# routes/Roteiros.py
from flask import Blueprint, request, jsonify, session
from models import db, Roteiro, Modulo, RoteiroAuditLog
from Utils.auth.auth_utils import login_required

# Blueprint SEM prefixo interno; o app.py define /luft-docs/api/roteiros
roteiros_bp = Blueprint('roteiros', __name__)


def serialize_roteiro(roteiro, include_modulos=False):
    """Serializa um Roteiro para o front, com datas ISO-8601 (via to_dict())."""
    data = roteiro.to_dict()
    if include_modulos:
        data['modulos_vinculados'] = [m.id for m in roteiro.modulos]
    return data


# ============== CREATE =======================================================
@roteiros_bp.route('/', methods=['POST'])
@login_required
def criar_roteiro():
    user_perms = session.get('permissions', {})
    if not user_perms.get('can_edit_scripts', False):
        return jsonify({'status': 'error', 'message': 'Acesso negado.'}), 403

    data = request.get_json() or {}
    if not data.get('titulo') or not data.get('conteudo'):
        return jsonify({'status': 'error', 'message': 'Título e conteúdo são obrigatórios.'}), 400

    novo_roteiro = Roteiro(
        titulo=data['titulo'],
        tipo=data.get('tipo', 'link'),
        conteudo=data['conteudo'],
        icone=data.get('icone'),
        ordem=data.get('ordem', 0),
    )
    db.session.add(novo_roteiro)

    db.session.add(RoteiroAuditLog(
        roteiro=novo_roteiro,
        user_id=session.get('user_id'),
        user_name=session.get('user_name'),
        action='CREATE'
    ))

    db.session.commit()
    db.session.refresh(novo_roteiro)

    return jsonify({
        'status': 'success',
        'message': 'Roteiro criado com sucesso!',
        'roteiro': serialize_roteiro(novo_roteiro, include_modulos=True)
    }), 201


# ============== LINK TO MODULE(S) ===========================================
@roteiros_bp.route('/vincular', methods=['POST'])
@login_required
def vincular_roteiro_a_modulo():
    user_perms = session.get('permissions', {})
    if not user_perms.get('can_edit_scripts', False):
        return jsonify({'status': 'error', 'message': 'Acesso negado. Você não tem permissão para vincular roteiros.'}), 403

    data = request.get_json() or {}
    roteiro_id = data.get('roteiro_id')
    modulo_ids = data.get('modulo_ids')

    if not roteiro_id or not modulo_ids:
        return jsonify({'status': 'error', 'message': 'ID do roteiro e lista de módulos são obrigatórios.'}), 400

    roteiro = Roteiro.query.get(roteiro_id)
    if not roteiro:
        return jsonify({'status': 'error', 'message': 'Roteiro não encontrado.'}), 404

    modulos = Modulo.query.filter(Modulo.id.in_(modulo_ids)).all()
    for modulo in modulos:
        if modulo not in roteiro.modulos:
            roteiro.modulos.append(modulo)

    db.session.commit()
    db.session.refresh(roteiro)

    return jsonify({
        'status': 'success',
        'message': f'Roteiro "{roteiro.titulo}" vinculado a {len(modulos)} módulo(s).',
        'roteiro': serialize_roteiro(roteiro, include_modulos=True)
    }), 200


# ============== READ (DETAIL) ===============================================
@roteiros_bp.route('/<int:roteiro_id>', methods=['GET'])
@login_required
def get_roteiro(roteiro_id):
    roteiro = Roteiro.query.get(roteiro_id)
    if not roteiro:
        return jsonify({'status': 'error', 'message': 'Roteiro não encontrado.'}), 404
    return jsonify(serialize_roteiro(roteiro, include_modulos=True)), 200


# ============== UPDATE =======================================================
@roteiros_bp.route('/<int:roteiro_id>', methods=['PUT'])
@login_required
def atualizar_roteiro(roteiro_id):
    user_perms = session.get('permissions', {})
    if not user_perms.get('can_edit_scripts', False):
        return jsonify({'status': 'error', 'message': 'Acesso negado.'}), 403

    roteiro = Roteiro.query.get(roteiro_id)
    if not roteiro:
        return jsonify({'status': 'error', 'message': 'Roteiro não encontrado.'}), 404

    data = request.get_json() or {}
    roteiro.titulo = data.get('titulo', roteiro.titulo)
    roteiro.descricao = data.get('descricao', roteiro.descricao)
    roteiro.tipo = data.get('tipo', roteiro.tipo)
    roteiro.conteudo = data.get('conteudo', roteiro.conteudo)
    roteiro.icone = data.get('icone', roteiro.icone)
    roteiro.ordem = data.get('ordem', roteiro.ordem)

    db.session.add(RoteiroAuditLog(
        roteiro_id=roteiro.id,
        user_id=session.get('user_id'),
        user_name=session.get('user_name'),
        action='UPDATE'
    ))

    db.session.commit()
    db.session.refresh(roteiro)

    return jsonify({
        'status': 'success',
        'message': 'Roteiro atualizado com sucesso!',
        'roteiro': serialize_roteiro(roteiro, include_modulos=True)
    }), 200


# ============== DELETE =======================================================
@roteiros_bp.route('/<int:roteiro_id>', methods=['DELETE'])
@login_required
def excluir_roteiro(roteiro_id):
    user_perms = session.get('permissions', {})
    if not user_perms.get('can_edit_scripts', False):
        return jsonify({'status': 'error', 'message': 'Acesso negado. Você não tem permissão para excluir roteiros.'}), 403

    roteiro = Roteiro.query.get(roteiro_id)
    if not roteiro:
        return jsonify({'status': 'error', 'message': 'Roteiro não encontrado.'}), 404

    db.session.add(RoteiroAuditLog(
        roteiro_id=roteiro.id,
        user_id=session.get('user_id'),
        user_name=session.get('user_name'),
        action='DELETE'
    ))

    db.session.delete(roteiro)
    db.session.commit()

    return jsonify({'status': 'success', 'message': 'Roteiro excluído com sucesso!'}), 200

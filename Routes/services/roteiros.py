from flask import Blueprint, request, jsonify, session
from models import db, Roteiro, Modulo, RoteiroAuditLog
from Utils.auth.auth_utils import login_required

roteiros_bp = Blueprint('roteiros', __name__, url_prefix='/api/roteiros')

def serialize_roteiro(roteiro, include_modulos=False):
    """Serializa um Roteiro para o front, com datas ISO-8601."""
    data = roteiro.to_dict()
    if include_modulos:
        data['modulos_vinculados'] = [m.id for m in roteiro.modulos]
    return data

# --- CRIAR ---
@roteiros_bp.route('/', methods=['POST'])
@login_required
def criar_roteiro():
    user_perms = session.get('permissions', {})
    if not user_perms.get('can_edit_scripts', False):
        return jsonify({'status': 'error', 'message': 'Acesso negado.'}), 403

    data = request.get_json()
    if not data or not data.get('titulo') or not data.get('conteudo'):
        return jsonify({'status': 'error', 'message': 'Título e conteúdo são obrigatórios.'}), 400

    novo_roteiro = Roteiro(
        titulo=data['titulo'],
        tipo=data.get('tipo', 'link'),
        conteudo=data['conteudo'],
        icone=data.get('icone'),
        ordem=data.get('ordem', 0)
    )
    db.session.add(novo_roteiro)

    log_entry = RoteiroAuditLog(
        roteiro=novo_roteiro,
        user_id=session.get('user_id'),
        user_name=session.get('user_name'),
        action='CREATE'
    )
    db.session.add(log_entry)

    db.session.commit()
    # IMPORTANTE: recarrega para trazer created_at/updated_at definidos pelos triggers
    db.session.refresh(novo_roteiro)

    return jsonify({
        'status': 'success',
        'message': 'Roteiro criado com sucesso!',
        'roteiro': serialize_roteiro(novo_roteiro, include_modulos=True)
    }), 201

# --- VINCULAR A MÓDULOS ---
@roteiros_bp.route('/vincular', methods=['POST'])
@login_required
def vincular_roteiro_a_modulo():
    user_perms = session.get('permissions', {})
    if not user_perms.get('can_edit_scripts', False):
        return jsonify({'status': 'error', 'message': 'Acesso negado. Você não tem permissão para vincular roteiros.'}), 403

    data = request.get_json()
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
    # updated_at pode ter mudado por causa do UPDATE: recarregar
    db.session.refresh(roteiro)

    return jsonify({
        'status': 'success',
        'message': f'Roteiro "{roteiro.titulo}" vinculado a {len(modulos)} módulo(s).',
        'roteiro': serialize_roteiro(roteiro, include_modulos=True)
    }), 200

# --- OBTER (EDIÇÃO/DETALHE) ---
@roteiros_bp.route('/<int:roteiro_id>', methods=['GET'])
@login_required
def get_roteiro(roteiro_id):
    roteiro = Roteiro.query.get_or_404(roteiro_id)
    return jsonify(serialize_roteiro(roteiro, include_modulos=True)), 200

# --- ATUALIZAR ---
@roteiros_bp.route('/<int:roteiro_id>', methods=['PUT'])
@login_required
def atualizar_roteiro(roteiro_id):
    user_perms = session.get('permissions', {})
    if not user_perms.get('can_edit_scripts', False):
        return jsonify({'status': 'error', 'message': 'Acesso negado.'}), 403

    roteiro = Roteiro.query.get_or_404(roteiro_id)
    data = request.get_json() or {}

    roteiro.titulo = data.get('titulo', roteiro.titulo)
    roteiro.descricao = data.get('descricao', roteiro.descricao)
    roteiro.tipo = data.get('tipo', roteiro.tipo)
    roteiro.conteudo = data.get('conteudo', roteiro.conteudo)
    roteiro.icone = data.get('icone', roteiro.icone)
    roteiro.ordem = data.get('ordem', roteiro.ordem)

    log_entry = RoteiroAuditLog(
        roteiro_id=roteiro.id,
        user_id=session.get('user_id'),
        user_name=session.get('user_name'),
        action='UPDATE'
    )
    db.session.add(log_entry)

    db.session.commit()
    # triggers atualizam updated_at -> precisamos recarregar
    db.session.refresh(roteiro)

    return jsonify({
        'status': 'success',
        'message': 'Roteiro atualizado com sucesso!',
        'roteiro': serialize_roteiro(roteiro, include_modulos=True)
    }), 200

# --- EXCLUIR ---
@roteiros_bp.route('/<int:roteiro_id>', methods=['DELETE'])
@login_required
def excluir_roteiro(roteiro_id):
    user_perms = session.get('permissions', {})
    if not user_perms.get('can_edit_scripts', False):
        return jsonify({'status': 'error', 'message': 'Acesso negado. Você não tem permissão para excluir roteiros.'}), 403

    roteiro = Roteiro.query.get_or_404(roteiro_id)

    log_entry = RoteiroAuditLog(
        roteiro_id=roteiro.id,
        user_id=session.get('user_id'),
        user_name=session.get('user_name'),
        action='DELETE'
    )
    db.session.add(log_entry)

    db.session.delete(roteiro)
    db.session.commit()

    return jsonify({'status': 'success', 'message': 'Roteiro excluído com sucesso!'}), 200

# app/routes/learning_plan.py
import sqlite3
from flask import (
    Blueprint, render_template, session, abort, jsonify, request
)

# --- CONFIGURAÇÃO DO BLUEPRINT ---
learning_plan_bp = Blueprint(
    'learning_plan',
    __name__,
    template_folder='../templates'
)

# --- FUNÇÃO AUXILIAR DE BANCO DE DADOS ---
def get_db_connection():
    """Cria e retorna uma conexão com o banco de dados."""
    conn = sqlite3.connect('recommendations.db')
    conn.row_factory = sqlite3.Row
    return conn

# ===================================================================
# ROTA PRINCIPAL - SERVE A PÁGINA DO DASHBOARD
# ===================================================================

@learning_plan_bp.route('/dashboard')
def show_focused_dashboard():
    """Serve a página HTML principal e unificada do dashboard de aprendizado."""
    # Apenas renderiza a página. O JavaScript fará o resto.
    return render_template('learning_plan/learning_page.html', token=request.args.get('token'))

# ===================================================================
# ROTAS DE API - FORNECEM DADOS PARA O FRONT-END INTERATIVO
# ===================================================================

@learning_plan_bp.route('/api/navigator-data')
def get_navigator_data():
    """Retorna os dados iniciais para popular a barra lateral (Navegador de Trilhas)."""
    user_id = session.get('user_id')
    user_info = session.get('user_info', {}) # Pega o dicionário de user_info
    if not user_id:
        abort(403, "Acesso negado: Usuário não autenticado.")

    conn = get_db_connection()
    user_progress = conn.execute("SELECT xp, level FROM user_progress WHERE user_id = ?", (user_id,)).fetchone()
    custom_trails = conn.execute("SELECT id, trail_name FROM learning_trails WHERE created_by_user_id = ? ORDER BY trail_name", (user_id,)).fetchall()
    conn.close()

    trail_list = [{"id": "recommended", "name": "Trilha Recomendada"}]
    trail_list.extend([{"id": row['id'], "name": row['trail_name']} for row in custom_trails])

    # Construindo o JSON de resposta
    response_data = {
        # ADICIONAMOS O NOME DO USUÁRIO AQUI
        "user_name": user_info.get('name', 'Usuário'), 
        "user_progress": dict(user_progress) if user_progress else {"xp": 0, "level": 1},
        "trails": trail_list
    }

    return jsonify(response_data)

@learning_plan_bp.route('/api/trail-data/<path:trail_identifier>')
def get_trail_data(trail_identifier):
    """Retorna os nós e arestas para UMA trilha específica para o Cytoscape."""
    user_id = session.get('user_id')
    user_group_info = session.get('user_group')
    if not user_id or not user_group_info: abort(403, "Acesso negado: Informações de sessão ausentes.")

    conn = get_db_connection()
    completed_module_ids = {row['module_id'] for row in conn.execute("SELECT module_id FROM user_module_completion WHERE user_id = ?", (user_id,)).fetchall()}
    
    modules_in_trail = []
    trail_name = ""
    module_ids_in_order = []


    if trail_identifier == 'recommended':
        user_group_name = user_group_info.get('acronym')
        # CORREÇÃO: Altere g.group_acronym para g.group_name
        modules_in_trail = conn.execute("SELECT m.id, m.module_name, m.description FROM learning_modules m JOIN recommendations r ON m.id = r.module_id JOIN user_groups g ON g.id = r.group_id WHERE g.group_name = ?", (user_group_name,)).fetchall()
        trail_name = "Trilha Recomendada"

    else:
        try:
            trail_id = int(trail_identifier)

            # Adicione esta linha para depuração
            print(f"--- DEBUG: Buscando trilha ID={trail_id} para o usuário ID={user_id} ---")

            trail_info = conn.execute("SELECT trail_name FROM learning_trails WHERE id = ? AND created_by_user_id = ?", (trail_id, user_id)).fetchone()
            if not trail_info: abort(404, "Trilha não encontrada.")
            trail_name = trail_info['trail_name']
            
            query_result = conn.execute(
                "SELECT m.id, m.module_name, m.description FROM trail_modules tm JOIN learning_modules m ON tm.module_id = m.id WHERE tm.trail_id = ? ORDER BY tm.step_order",
                (trail_id,)
            ).fetchall()
            modules_in_trail = query_result
            module_ids_in_order = [row['id'] for row in query_result]

        except (ValueError, TypeError):
            abort(400, "Identificador de trilha inválido.")

    # Dados para o Cytoscape
    elements = [{'data': {'id': f'trail_{trail_identifier}', 'label': trail_name, 'type': 'trail_center'}}]
    for module in modules_in_trail:
        elements.append({'data': {'id': f"module_{module['id']}", 'label': module['module_name'], 'description': module['description']}, 'classes': 'completed' if module['id'] in completed_module_ids else ''})
        elements.append({'data': {'source': f"module_{module['id']}", 'target': f'trail_{trail_identifier}'}})
        
    conn.close()
    
    # Retorna também os dados da trilha para o modal de edição
    return jsonify({
        "trail_name": trail_name,
        "module_ids": module_ids_in_order, # Lista ordenada de IDs dos módulos
        "cytoscape_elements": elements # Dados para o gráfico
    })

# Rota existente...
@learning_plan_bp.route('/api/trails', methods=['POST'])
def create_trail_api():
    """API para criar uma nova trilha personalizada."""
    user_id = session.get('user_id')
    if not user_id: abort(403)
    
    trail_name = request.json.get('trail_name')
    if not trail_name: abort(400, "O nome da trilha é obrigatório.")

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT INTO learning_trails (trail_name, created_by_user_id) VALUES (?, ?)", (trail_name, user_id))
    trail_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return jsonify({"status": "success", "message": "Trilha criada com sucesso!", "new_trail": {"id": trail_id, "name": trail_name}}), 201
    
# Rota existente...
@learning_plan_bp.route('/api/trails/<int:trail_id>', methods=['DELETE'])
def delete_trail_api(trail_id):
    """API para deletar uma trilha personalizada."""
    user_id = session.get('user_id')
    if not user_id: abort(403)

    conn = get_db_connection()
    trail_owner = conn.execute("SELECT 1 FROM learning_trails WHERE id = ? AND created_by_user_id = ?", (trail_id, user_id)).fetchone()
    if not trail_owner:
        conn.close()
        abort(403, "Você não tem permissão para deletar esta trilha.")

    try:
        conn.execute("BEGIN TRANSACTION")
        conn.execute("DELETE FROM trail_modules WHERE trail_id = ?", (trail_id,))
        conn.execute("DELETE FROM learning_trails WHERE id = ?", (trail_id,))
        conn.commit()
    except sqlite3.Error as e:
        conn.rollback()
        return jsonify({"status": "error", "message": str(e)}), 500
    finally:
        conn.close()

    return jsonify({"status": "success", "message": "Trilha deletada com sucesso."})

# --- INÍCIO DO NOVO CÓDIGO ---

@learning_plan_bp.route('/api/all-modules', methods=['GET'])
def get_all_modules():
    """Retorna uma lista de todos os módulos de aprendizado disponíveis no sistema."""
    user_id = session.get('user_id')
    if not user_id: abort(403) # Protege o endpoint

    conn = get_db_connection()
    all_modules = conn.execute("SELECT id, module_name FROM learning_modules ORDER BY module_name").fetchall()
    conn.close()

    return jsonify([dict(row) for row in all_modules])

@learning_plan_bp.route('/api/trails/<int:trail_id>', methods=['PUT'])
def update_trail_api(trail_id):
    """API para editar uma trilha: atualiza o nome e a lista de módulos."""
    user_id = session.get('user_id')
    if not user_id: abort(403)

    data = request.get_json()
    new_name = data.get('trail_name')
    module_ids = data.get('modules') # Espera uma lista de IDs [3, 1, 5]

    if not new_name or module_ids is None:
        abort(400, "Dados incompletos: 'trail_name' e 'modules' são obrigatórios.")

    conn = get_db_connection()
    # Verifica se o usuário é o dono da trilha
    trail_owner = conn.execute("SELECT 1 FROM learning_trails WHERE id = ? AND created_by_user_id = ?", (trail_id, user_id)).fetchone()
    if not trail_owner:
        conn.close()
        abort(403, "Você não tem permissão para editar esta trilha.")

    try:
        # Usa uma transação para garantir a integridade dos dados
        conn.execute("BEGIN TRANSACTION")

        # 1. Atualiza o nome da trilha
        conn.execute("UPDATE learning_trails SET trail_name = ? WHERE id = ?", (new_name, trail_id))

        # 2. Remove todos os módulos antigos da trilha
        conn.execute("DELETE FROM trail_modules WHERE trail_id = ?", (trail_id,))

        # 3. Insere os novos módulos com a nova ordem
        for index, module_id in enumerate(module_ids):
            conn.execute(
                "INSERT INTO trail_modules (trail_id, module_id, step_order) VALUES (?, ?, ?)",
                (trail_id, module_id, index) # `step_order` é a posição na lista
            )
        
        conn.commit()
    except sqlite3.Error as e:
        conn.rollback()
        return jsonify({"status": "error", "message": f"Erro no banco de dados: {e}"}), 500
    finally:
        conn.close()

    return jsonify({"status": "success", "message": "Trilha atualizada com sucesso!"})


# --- FIM DO NOVO CÓDIGO ---


# Rota existente...
@learning_plan_bp.route('/api/modules/<int:module_id>/complete', methods=['POST'])
def complete_module_api(module_id):
    """API para marcar um módulo como concluído e aplicar gamificação."""
    user_id = session.get('user_id')
    if not user_id: abort(403)

    conn = get_db_connection()
    # Lógica para dar XP, verificar medalhas, etc.
    # ... (código da gamificação que já desenvolvemos) ...
    conn.close()
    return jsonify({"status": "success", "message": "Módulo concluído!"})
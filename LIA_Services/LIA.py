# /routes/ia.py
import os
import re
import uuid
from flask import Blueprint, jsonify, request, session
from LIA_Services.Services import Context_Service, Feedback_Service
from Utils.auth.auth_utils import login_required
from Config import MODULES_DIR


# --- IMPORTAÇÕES DOS SERVIÇOS DE IA ---
from LIA_Services import LIAResponseGenerator
from LIA_Services.Configs.LLMConfig import are_components_available
from Utils.recommendation_service import log_ai_feedback

ia_bp = Blueprint('ia_bp', __name__)

# --- A LÓGICA DE DESCOBRIR MÓDULOS PERMANECE AQUI ---
def get_available_modules():
    """Verifica o diretório data/modules e retorna uma lista com os nomes dos módulos."""
    try:
        modules_path = str(MODULES_DIR)
        if not os.path.exists(modules_path):
            print("AVISO: Diretório 'data/modules' não encontrado.")
            return []
        available = sorted([d for d in os.listdir(modules_path) if os.path.isdir(os.path.join(modules_path, d))])
        print(f"Módulos descobertos automaticamente: {available}")
        return available
    except Exception as e:
        print(f"ERRO CRÍTICO ao descobrir módulos: {e}")
        return []

AVAILABLE_MODULES = get_available_modules()
# -------------------------------------------------------------

@ia_bp.route('/api/get_modules_list', methods=['GET'])
@login_required
def get_modules_list():
    """Retorna a lista de módulos disponíveis para o frontend."""
    if not AVAILABLE_MODULES:
        return jsonify({"error": "Nenhum módulo disponível."}), 404
    return jsonify({"modules": AVAILABLE_MODULES})

@ia_bp.route('/api/ask_llm', methods=['POST'])
@login_required
def ask_llm_api():
    if not are_components_available():
        return jsonify({"error": "Componentes da IA não estão configurados."}), 500

    data = request.get_json()
    original_user_question = data.get('user_question')
    if not original_user_question:
        return jsonify({"error": "Requisição inválida."}), 400

    selected_model = data.get('selected_model', 'groq-70b')
    user_id = session.get('username', 'anonymous')
    user_perms = session.get('permissions', {})
    response_uuid = str(uuid.uuid4())

    # **LÓGICA CORRIGIDA**: Verifica se é uma busca focada para pular o reranking
    is_focused_search = '@' in original_user_question

    try:
        # ETAPA 1: BUSCA INICIAL DE DOCUMENTOS CANDIDATOS
        initial_docs, initial_metas, was_blocked_by_perm = Context_Service.find_context_for_question(
            user_question=original_user_question,
            available_modules=AVAILABLE_MODULES,
            user_perms=user_perms
        )

        if was_blocked_by_perm:
            no_access_answer = "Não encontrei informações sobre este tópico nos documentos aos quais você tem acesso. Tente perguntar de outra forma ou sobre outro assunto."
            return jsonify({
                "answer": no_access_answer, "context_files": [], "response_id": response_uuid,
                "user_id": user_id, "original_user_question": original_user_question,
                "model_used": selected_model, "context_sources_list": []
            })
        
        if not initial_docs:
            no_context_answer = "Opa! Não encontrei nada sobre isso nos documentos. Pode tentar perguntar de outra forma? 😉"
            return jsonify({
                "answer": no_context_answer, "context_files": [], "response_id": response_uuid,
                "user_id": user_id, "original_user_question": original_user_question,
                "model_used": selected_model, "context_sources_list": []
            })

        final_context = ""
        final_sources = []

        # ETAPA 2: RE-RANKING CONDICIONAL
        if not is_focused_search:
            # Para buscas gerais, usamos o reranker para obter a melhor qualidade.
            final_context, final_sources = LIAResponseGenerator.rerank_and_filter_context(
                question=original_user_question,
                documents=initial_docs,
                metadatas=initial_metas
            )
        else:
            # Para buscas com '@', pulamos o reranker e usamos os resultados diretos.
            print("Busca focada com '@' detectada. Pulando a etapa de re-ranking para maior velocidade.")
            # Apenas pegamos os 4 melhores resultados da busca vetorial inicial.
            top_k = 4
            final_context = "\n---\n".join(initial_docs[:top_k])
            final_sources = sorted(list(set(meta['source'] for meta in initial_metas[:top_k])))

        if not final_context.strip():
            no_context_answer = "Encontrei alguns documentos, mas nenhum parecia responder diretamente à sua pergunta. Poderia tentar ser mais específico? 🤔"
            return jsonify({
                "answer": no_context_answer, "context_files": [], "response_id": response_uuid,
                "user_id": user_id, "original_user_question": original_user_question,
                "model_used": selected_model, "context_sources_list": []
            })

        # ETAPA 3: GERAÇÃO DA RESPOSTA FINAL
        final_answer = LIAResponseGenerator.generate_llm_answer(
            model_name=selected_model,
            context=final_context,
            question=original_user_question
        )

        return jsonify({
            "answer": final_answer,
            "context_files": final_sources,
            "response_id": response_uuid,
            "user_id": user_id,
            "original_user_question": original_user_question,
            "model_used": selected_model,
            "context_sources_list": final_sources
        })

    except Exception as e:
        print(f"ERRO CRÍTICO na API ask_llm: {e}")
        return jsonify({"error": f"Ocorreu um erro inesperado ao processar sua pergunta: {str(e)}"}), 500

@ia_bp.route('/api/submit_feedback', methods=['POST'])
@login_required
def submit_feedback_api():
    data = request.get_json()
    response_id = data.get('response_id')
    user_id = session.get('username', 'anonymous')
    rating = data.get('rating')
    comment = data.get('comment')
    # NOVOS: Recebe os campos adicionais do frontend
    user_question = data.get('user_question')
    model_used = data.get('model_used')
    context_sources = data.get('context_sources') # Será uma lista do frontend

    if not all([response_id, user_id, rating is not None]):
        return jsonify({"error": "Dados de feedback inválidos."}), 400

    try:
        # Passa os novos campos para log_ai_feedback
        log_ai_feedback(
            response_id=response_id,
            user_id=user_id,
            rating=rating,
            comment=comment,
            user_question=user_question,
            model_used=model_used,
            context_sources=context_sources
        )
        return jsonify({"message": "Feedback registrado com sucesso!"}), 200
    except Exception as e:
        print(f"Erro ao registrar feedback: {e}")
        return jsonify({"error": "Erro interno ao registrar feedback."}), 500
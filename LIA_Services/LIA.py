# /routes/ia.py
import os
import re
import uuid
from flask import Blueprint, jsonify, request, session
from LIA_Services.Services import Context_Service, Feedback_Service
from Utils.auth.Autenticacao import LoginObrigatorio
from Config import MODULES_DIR, BASE_PREFIX

# --- IMPORTAÇÕES DOS SERVIÇOS DE IA ---
from LIA_Services import LIAResponseGenerator
from LIA_Services.Configs.LLMConfig import are_components_available
from Utils.ServicoRecomendacao import RegistrarFeedbackIA

ia_bp = Blueprint('ia_bp', __name__)


def _transform_path_to_url(file_path, token):
    """
    Recebe um caminho de arquivo (ex: data/modules/rh/doc.md) e o token,
    retornando a URL clicável correta para a aplicação.
    """
    if not file_path:
        return "#"

    # 1. Normalizar as barras para evitar problemas entre Windows (\) e Linux (/)
    clean_path = file_path.replace('\\', '/')
    
    # URL Base (ex: /luft-docs)
    base_url = BASE_PREFIX

    # --- CASO 1: É UM MÓDULO? ---
    # Estrutura padrão: data/modules/<NOME_DO_MODULO>/...
    if '/modules/' in clean_path:
        try:
            # Quebra o caminho para pegar o nome da pasta logo após 'modules'
            parts = clean_path.split('/modules/')
            if len(parts) > 1:
                sub_parts = parts[1].split('/') # Pega o resto do caminho
                module_name = sub_parts[0]      # O primeiro item é a pasta do módulo
                
                # Retorna link para a rota de Módulo
                return f"{base_url}/modulo/?modulo={module_name}&token={token}"
        except Exception as e:
            print(f"Erro ao gerar link de módulo: {e}")

    # --- CASO 2: É UM SUBMÓDULO OU ARQUIVO GLOBAL? ---
    # Estrutura: data/global/.../NOME_ARQUIVO.md
    # A lógica aqui é pegar o nome do arquivo (sem extensão) e passar como ?nome=
    if clean_path.endswith('.md'):
        try:
            filename = os.path.basename(clean_path) # Ex: TORRE_DE_CONTROLE.md
            name_no_ext = os.path.splitext(filename)[0] # Ex: TORRE_DE_CONTROLE
            
            # Retorna link para a rota de Submódulo
            return f"{base_url}/submodule/?nome={name_no_ext}&token={token}"
        except Exception as e:
            print(f"Erro ao gerar link de submódulo: {e}")

    # Fallback: Se não conseguir identificar, retorna '#' ou o próprio caminho
    return "#"

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
@LoginObrigatorio
def get_modules_list():
    """Retorna a lista de módulos disponíveis para o frontend."""
    if not AVAILABLE_MODULES:
        return jsonify({"error": "Nenhum módulo disponível."}), 404
    return jsonify({"modules": AVAILABLE_MODULES})

@ia_bp.route('/api/ask_llm', methods=['POST'])
@LoginObrigatorio
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

        # --- NOVA LÓGICA DE LINKS ---
        # Pega o token atual da sessão (ou do request se você estiver passando via header)
        # Como o usuário já está logado para chamar essa rota, pegamos o token que veio no request (query param) ou geramos um novo se necessário.
        # Mas para facilitar, vamos pegar o que o frontend mandou ou da sessão.
        
        # Tenta pegar token do parametro, header ou sessão
        current_token = request.args.get('token') 
        if not current_token:
             # Se não veio na query, tentamos pegar da sessão se você salvou lá, 
             # ou assumimos que o frontend vai ter que lidar com isso. 
             # No seu caso, o frontend JS passa o token na URL ao carregar, mas aqui é um POST.
             # Vamos tentar reconstruir ou usar um placeholder se não tiver.
             current_token = session.get('token', '')

        # Processa as fontes para criar objetos com Link
        structured_sources = []
        for source in final_sources:
            link = _transform_path_to_url(source, current_token)
            structured_sources.append({
                "name": source,  # O caminho original (para exibir texto)
                "url": link      # O link clicável
            })

        return jsonify({
            "answer": final_answer,
            "context_files": final_sources, # Mantém compatibilidade legada se precisar
            "response_id": response_uuid,
            "user_id": user_id,
            "original_user_question": original_user_question,
            "model_used": selected_model,
            "context_sources_objects": structured_sources # <--- CAMPO NOVO COM LINKS
        })

    except Exception as e:
        print(f"ERRO CRÍTICO na API ask_llm: {e}")
        return jsonify({"error": f"Ocorreu um erro inesperado: {str(e)}"}), 500
    
@ia_bp.route('/api/submit_feedback', methods=['POST'])
@LoginObrigatorio
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
        RegistrarFeedbackIA(
            identificadorResposta=response_id,
            identificadorUsuario=user_id,
            avaliacao=rating,
            comentario=comment,
            perguntaUsuario=user_question,
            modeloUtilizado=model_used,
            fontesContexto=context_sources,
        )
        return jsonify({"message": "Feedback registrado com sucesso!"}), 200
    except Exception as e:
        print(f"Erro ao registrar feedback: {e}")
        return jsonify({"error": "Erro interno ao registrar feedback."}), 500
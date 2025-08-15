# /routes/search.py
import re
import os
from flask import Blueprint, render_template, request, session, jsonify, current_app, url_for
from Utils.data.search_utils import search_all_documents, extract_media_preview
from Utils.data.module_utils import carregar_modulos, carregar_markdown 
from Utils.text.service_filter import ContentFilterService
from Utils.auth.auth_utils import login_required
from Routes.API.Permissions import get_user_group
from Utils.recommendation_service import (
    log_search_term, 
    get_hybrid_recommendations, 
    get_most_accessed,
    get_popular_searches,
    get_autocomplete_suggestions,
    get_access_counts
)
from Utils.permissions_config import MODULOS_RESTRITOS

search_bp = Blueprint('search', __name__)
filter_service = ContentFilterService()

def get_context_snippet(content, query, length=200):
    content_sem_codigo = re.sub(r'```[\s\S]*?```', '', content)
    content_limpo = re.sub(r'<[^>]+>', '', content_sem_codigo)
    if not query:
        return content_limpo[:length] + '...' if len(content_limpo) > length else content_limpo
    match = re.search(re.escape(query), content_limpo, re.IGNORECASE)
    if not match: return content_limpo[:length] + '...' if len(content_limpo) > length else content_limpo
    start = max(0, match.start() - (length // 2)); end = min(len(content_limpo), match.end() + (length // 2))
    snippet = content_limpo[start:end]
    if start > 0: snippet = '...' + snippet
    if end < len(content_limpo): snippet += '...'
    return snippet

@search_bp.route('/')
@login_required
def perform_search():
    token = request.args.get('token', '').strip()
    query = request.args.get('q', '').strip()
    module_filter = request.args.get('module', '').strip()
    if query: log_search_term(query)
    
    _, user_name = get_user_group()
    user_perms = session.get('permissions', {})
    can_view_tecnico = user_perms.get('can_view_tecnico', False)
    can_see_restricted_module = user_perms.get('can_see_restricted_module', False)
    
    raw_results = search_all_documents(query, token, module_filter, can_view_tecnico)
    
    # Filtra os resultados da busca
    if not can_see_restricted_module:
        filtered_results = [res for res in raw_results if res.get('module_id') not in MODULOS_RESTRITOS]
    else:
        filtered_results = raw_results

    processed_results = []
    for res in filtered_results:
        snippet = get_context_snippet(res['content'], query)
        res['snippet'] = filter_service._highlight_terms(snippet, query)
        processed_results.append(res)
        
    # Carrega todos os módulos para o dropdown
    all_modules, _ = carregar_modulos()
    
    # --- NOVO: Filtra a lista de módulos para o dropdown ---
    if not can_see_restricted_module:
        # Envia para o template apenas os módulos que não são restritos
        modules_for_dropdown = [mod for mod in all_modules if mod.get('id') not in MODULOS_RESTRITOS]
    else:
        # Se tem permissão, envia todos
        modules_for_dropdown = all_modules
    
    # Passa a lista JÁ FILTRADA para o template
    return render_template(
        'Pages/SearchPage.html', 
        query=query, 
        results=processed_results, 
        total_results=len(processed_results), 
        modules=modules_for_dropdown,  # <-- Usa a lista filtrada
        current_filter=module_filter, 
        token=token
    )

# --- ROTA DE API UNIFICADA E CORRIGIDA ---
@search_bp.route('/api/recommendations')
@login_required
def api_recommendations():
    """Retorna um objeto JSON com todas as recomendações necessárias."""
    token = request.args.get('token', '')
    
    # --- NOVO: Obtém a permissão do usuário da sessão ---
    user_perms = session.get('permissions', {})
    can_see_restricted_module = user_perms.get('can_see_restricted_module', False)

    # 1. Tenta obter recomendações híbridas
    recs_raw = get_hybrid_recommendations(limit=10)
    
    # Lógica de fallback
    if not recs_raw:
        current_app.logger.info("Recomendações híbridas vazias. Usando fallback para 'Mais Acedidos'.")
        recs_raw = get_most_accessed(limit=10)

    # --- NOVO: Filtra as recomendações com base na permissão ANTES de processar ---
    if not can_see_restricted_module:
        recs_raw = [rec for rec in recs_raw if rec.get('document_id') not in MODULOS_RESTRITOS]
    
    doc_ids_to_show = [rec['document_id'] for rec in recs_raw]
    
    # 2. Monta os detalhes completos para cada recomendação (já filtrada)
    all_modules, _ = carregar_modulos()
    module_details_map = {mod['id']: mod for mod in all_modules}
    access_counts = get_access_counts(doc_ids_to_show)
    popular_searches = get_popular_searches(limit=10)
    popular_search_terms = [search['query_term'] for search in popular_searches]
    
    recommendation_results = []
    for doc_id in doc_ids_to_show:
        try:
            content = carregar_markdown(doc_id)
            if not content: continue

            details, url, doc_type = {}, "", "Documentação"
            if doc_id in module_details_map:
                details = module_details_map[doc_id]
                url = f"/modulo?modulo={doc_id}"
            else: 
                file_name_part = os.path.basename(doc_id)
                details = {'nome': file_name_part.replace('_', ' ').replace('-', ' ').capitalize(), 'icon': 'fas fa-file-alt'}
                url = f"/modulo?submodulo={doc_id}"
                parent_dir = os.path.basename(os.path.dirname(doc_id))
                doc_type = parent_dir.capitalize() if parent_dir else "Submódulo"
            
            snippet = get_context_snippet(content, query="")
            highlight_query = ""
            for term in popular_search_terms:
                if re.search(r'\b' + re.escape(term) + r'\b', snippet, re.IGNORECASE):
                    highlight_query = term
                    break
            
            if highlight_query:
                snippet = filter_service._highlight_terms(snippet, highlight_query)

            preview_data = extract_media_preview(content)
            if preview_data and not preview_data.get('is_absolute'):
                endpoint = 'index.serve_imagem_dinamica' if preview_data['type'] == 'image' else 'index.serve_video'
                preview_data['path'] = url_for(endpoint, nome_arquivo=preview_data['path'], token=token)

            recommendation_results.append({
                'module_id': doc_id, 'module_nome': details.get('nome', 'Desconhecido'),
                'module_icon': details.get('icon', 'fas fa-question-circle'), 'doc_type': doc_type,
                'url': url, 'snippet': snippet, 'preview': preview_data,
                'access_count': access_counts.get(doc_id, 0)
            })
        except Exception as e:
            current_app.logger.error(f"ERRO ao processar recomendação para '{doc_id}': {e}", exc_info=True)
            continue
    
    final_data_to_send = {
        'hybrid_recommendations': recommendation_results,
        'popular_searches': get_popular_searches(limit=5)
    }
    
    return jsonify(final_data_to_send)

# --- ROTA DE API PARA AUTO-COMPLETE ---
@search_bp.route('/api/autocomplete')
@login_required
def api_autocomplete():
    query = request.args.get('q', '')
    suggestions = get_autocomplete_suggestions(query, limit=5)
    return jsonify(suggestions)
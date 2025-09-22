# /routes/search.py
import re
import os
from urllib.parse import urlencode
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
def _montar_url(base, token):
    # Garante anexar ?token=... respeitando se já há querystring
    sep = '&' if ('?' in base) else '?'
    return f"{base}{sep}{urlencode({'token': token})}" if token else base

def _build_doc_payload(doc_id, token, module_details_map, content, highlight_term="", access_count=0):
    """
    Monta o payload padrão (nome, ícone, url, snippet, preview) para a palette.
    """
    # Descobre se é módulo raiz (está no catálogo)
    if doc_id in module_details_map:
        details = module_details_map[doc_id]
        url = _montar_url(f"/modulo?modulo={doc_id}", token)
        doc_type = "Módulo"
    else:
        file_name_part = os.path.basename(doc_id)
        details = {
            'nome': file_name_part.replace('_', ' ').replace('-', ' ').capitalize(),
            'icon': 'fas fa-file-alt'
        }
        url = _montar_url(f"/modulo?submodulo={doc_id}", token)
        parent_dir = os.path.basename(os.path.dirname(doc_id))
        doc_type = parent_dir.capitalize() if parent_dir else "Submódulo"

    # Snippet e destaque
    snippet = get_context_snippet(content, query=highlight_term or "")
    if highlight_term:
        snippet = filter_service._highlight_terms(snippet, highlight_term)

    # Preview de mídia (imagem/vídeo)
    preview_data = extract_media_preview(content)
    if preview_data and not preview_data.get('is_absolute'):
        endpoint = 'index.serve_imagem_dinamica' if preview_data['type'] == 'image' else 'index.serve_video'
        preview_data['path'] = url_for(endpoint, nome_arquivo=preview_data['path'], token=token)

    return {
        'module_id': doc_id,
        'module_nome': details.get('nome', 'Desconhecido'),
        'module_icon': details.get('icon', 'fas fa-question-circle'),
        'doc_type': doc_type,
        'url': url,
        'snippet': snippet,
        'preview': preview_data,
        'access_count': int(access_count or 0),
    }

# --- NOVA ROTA: resultados de busca em JSON para a palette ---
@search_bp.get('/api/search')
@login_required
def api_search():
    token = request.args.get('token', '').strip()
    query = request.args.get('q', '').strip()
    module_filter = request.args.get('module', '').strip()

    # Loga o termo (como já faz na perform_search)
    if query:
        log_search_term(query)

    # Permissões
    user_perms = session.get('permissions', {})
    can_view_tecnico = user_perms.get('can_view_tecnico', False)
    can_see_restricted_module = user_perms.get('can_see_restricted_module', False)

    # Busca bruta
    raw_results = search_all_documents(query, token, module_filter, can_view_tecnico)

    # Filtra módulos restritos
    if not can_see_restricted_module:
        raw_results = [r for r in raw_results if r.get('module_id') not in MODULOS_RESTRITOS]

    # Mapa de detalhes dos módulos
    all_modules, _ = carregar_modulos()
    module_details_map = {m['id']: m for m in all_modules}

    # Access count
    doc_ids = [r['module_id'] for r in raw_results]
    access_counts = get_access_counts(doc_ids) if doc_ids else {}

    # Monta payload
    items = []
    for r in raw_results[:50]:  # limite de segurança
        try:
            doc_id = r['module_id']
            content = r.get('content') or carregar_markdown(doc_id) or ""
            payload = _build_doc_payload(
                doc_id=doc_id,
                token=token,
                module_details_map=module_details_map,
                content=content,
                highlight_term=query,
                access_count=access_counts.get(doc_id, 0),
            )
            items.append(payload)
        except Exception as e:
            current_app.logger.error(f"Erro ao montar payload de busca '{r}': {e}", exc_info=True)
            continue

    return jsonify({'results': items})

# --- COMPLEMENTO: Recommendations também devolve 'most_accessed' ---
@search_bp.route('/api/recommendations')
@login_required
def api_recommendations():
    token = request.args.get('token', '')

    user_perms = session.get('permissions', {})
    can_see_restricted_module = user_perms.get('can_see_restricted_module', False)

    # 1) Híbrido (com fallback)
    recs_raw = get_hybrid_recommendations(limit=10) or []
    if not recs_raw:
        current_app.logger.info("Recomendações híbridas vazias. Fallback: 'Mais Acessados'.")
        recs_raw = get_most_accessed(limit=10) or []

    # 2) Mais acessados para o bloco dedicado
    most_raw = get_most_accessed(limit=12) or []

    # Filtra restritos
    if not can_see_restricted_module:
        recs_raw = [x for x in recs_raw if x.get('document_id') not in MODULOS_RESTRITOS]
        most_raw = [x for x in most_raw if x.get('document_id') not in MODULOS_RESTRITOS]

    # Mapas auxiliares
    all_modules, _ = carregar_modulos()
    module_details_map = {m['id']: m for m in all_modules}

    # Access counts
    doc_ids_to_show = [x['document_id'] for x in (recs_raw + most_raw)]
    access_counts = get_access_counts(doc_ids_to_show) if doc_ids_to_show else {}

    # Pesquisas populares (chips)
    popular_searches = get_popular_searches(limit=10)
    popular_search_terms = [s['query_term'] for s in popular_searches]

    # Monta blocos
    def _expand_list(raw_list):
        out = []
        for item in raw_list:
            doc_id = item['document_id']
            try:
                content = carregar_markdown(doc_id) or ""
                # destaque: se um termo popular aparece no conteúdo, destaca o primeiro encontrado
                highlight_term = ""
                for term in popular_search_terms:
                    if re.search(r'\b' + re.escape(term) + r'\b', content, re.IGNORECASE):
                        highlight_term = term
                        break
                out.append(_build_doc_payload(
                    doc_id=doc_id,
                    token=token,
                    module_details_map=module_details_map,
                    content=content,
                    highlight_term=highlight_term,
                    access_count=access_counts.get(doc_id, 0),
                ))
            except Exception as e:
                current_app.logger.error(f"Erro em recommendations payload '{doc_id}': {e}", exc_info=True)
                continue
        return out

    recommendation_results = _expand_list(recs_raw)
    most_accessed_results = _expand_list(most_raw)

    return jsonify({
        'hybrid_recommendations': recommendation_results,
        'most_accessed': most_accessed_results,
        'popular_searches': popular_searches[:5],
    })

# --- permanece igual ---
@search_bp.route('/api/autocomplete')
@login_required
def api_autocomplete():
    query = request.args.get('q', '')
    suggestions = get_autocomplete_suggestions(query, limit=5)
    return jsonify(suggestions)
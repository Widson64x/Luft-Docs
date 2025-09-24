# /routes/search.py
import re
import os
from urllib.parse import urlencode
from flask import (
    Blueprint, render_template, request, session, jsonify,
    current_app, url_for
)
from Utils.data.search_utils import search_all_documents, extract_media_preview
from Utils.data.module_utils import carregar_modulos, carregar_markdown
from Utils.text.service_filter import ContentFilterService
from Utils.auth.auth_utils import login_required
from Routes.API.Permissions import get_user_group
from Utils.recommendation_service import (
    log_search_term, get_hybrid_recommendations, get_most_accessed,
    get_popular_searches, get_autocomplete_suggestions, get_access_counts
)
from Utils.permissions_config import MODULOS_RESTRITOS

search_bp = Blueprint('search', __name__)
filter_service = ContentFilterService()

@search_bp.app_context_processor
def inject_base_prefix():
    # Disponibiliza BASE_PREFIX para qualquer template
    base_prefix = current_app.config.get("BASE_PREFIX", "")
    return {"base_prefix": base_prefix}

def _get_base() -> str:
    return (current_app.config.get("BASE_PREFIX") or "").rstrip("/")

def _with_base(path: str) -> str:
    if path.startswith("http://") or path.startswith("https://"):
        return path
    base = _get_base()
    if not path.startswith("/"):
        path = "/" + path
    return (base + path).replace("//", "/")

def get_context_snippet(content, query, length=200):
    content_sem_codigo = re.sub(r'```[\s\S]*?```', '', content)
    content_limpo = re.sub(r'<[^>]+>', '', content_sem_codigo)
    if not query:
        return content_limpo[:length] + '...' if len(content_limpo) > length else content_limpo
    match = re.search(re.escape(query), content_limpo, re.IGNORECASE)
    if not match:
        return content_limpo[:length] + '...' if len(content_limpo) > length else content_limpo
    start = max(0, match.start() - (length // 2))
    end = min(len(content_limpo), match.end() + (length // 2))
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
    if query:
        log_search_term(query)

    _, _user_name = get_user_group()
    user_perms = session.get('permissions', {})
    can_view_tecnico = user_perms.get('can_view_tecnico', False)
    can_see_restricted_module = user_perms.get('can_see_restricted_module', False)

    raw_results = search_all_documents(query, token, module_filter, can_view_tecnico)

    # Filtra restritos
    results_filtered = raw_results if can_see_restricted_module else [
        r for r in raw_results if r.get('module_id') not in MODULOS_RESTRITOS
    ]

    processed_results = []
    for res in results_filtered:
        snippet = get_context_snippet(res['content'], query)
        res['snippet'] = filter_service._highlight_terms(snippet, query)
        processed_results.append(res)

    all_modules, _ = carregar_modulos()
    modules_for_dropdown = all_modules if can_see_restricted_module else [
        m for m in all_modules if m.get('id') not in MODULOS_RESTRITOS
    ]

    return render_template(
        'Pages/SearchPage.html',
        query=query,
        results=_decorate_results(processed_results, token),
        total_results=len(processed_results),
        modules=modules_for_dropdown,
        current_filter=module_filter,
        token=token
    )

def _decorate_results(results, token: str):
    """
    Garante que cada item result já venha com URLs/mídias prefixadas.
    """
    out = []
    base = _get_base()
    for res in results:
        # corrige URL de navegação do cartão (se vier calculada fora)
        url = res.get('url')
        if not url:
            # fallback: tenta inferir
            doc_id = res.get("module_id")
            if doc_id:
                url = _build_doc_url(doc_id, token)
        else:
            url = _with_base(url)

        # corrige preview caso seja relativo
        preview = res.get('preview')
        if preview and not preview.get('is_absolute'):
            endpoint = 'index.serve_imagem_dinamica' if preview['type'] == 'image' else 'index.serve_video'
            preview['path'] = url_for(endpoint, nome_arquivo=preview['path'], token=token)
        out.append({**res, "url": url, "preview": preview})
    return out

# ----------------- helpers de URL usadas nos endpoints JSON -----------------

def _montar_url(base_path, token):
    """Concatena token corretamente."""
    sep = '&' if ('?' in base_path) else '?'
    return f"{base_path}{sep}{urlencode({'token': token})}" if token else base_path

def _build_doc_url(doc_id: str, token: str) -> str:
    """
    Mantém seu padrão /modulo?modulo=... ou /modulo?submodulo=...
    porém sempre com BASE_PREFIX na frente.
    """
    # Heurística simples: IDs com barra indicam arquivo (submódulo)
    if "/" in doc_id and not doc_id.endswith("/"):
        p = _montar_url(f"/modulo?submodulo={doc_id}", token)
    else:
        p = _montar_url(f"/modulo?modulo={doc_id}", token)
    return _with_base(p)

def _build_doc_payload(doc_id, token, module_details_map, content, highlight_term: str = "", access_count: int = 0):
    """
    Monta o payload padrão (nome, ícone, url, snippet, preview) para os resultados de busca e recomendações.
    - Se doc_id começar com "tech_": módulo técnico (?modulo_tecnico=)
    - Se doc_id existir no mapa de módulos: módulo normal (?modulo=)
    - Caso contrário: submódulo (?submodulo=)
    """

    # --- Detecta se é módulo técnico ---
    if str(doc_id).startswith("tech_"):
        clean_id = str(doc_id).replace("tech_", "", 1)
        details = module_details_map.get(doc_id, {
            'nome': clean_id.capitalize(),
            'icon': 'fas fa-tools'
        })
        url = _montar_url(f"/modulo?modulo_tecnico={clean_id}", token)
        doc_type = "Módulo Técnico"

    # --- Detecta se é módulo normal ---
    elif doc_id in module_details_map:
        details = module_details_map[doc_id]
        url = _montar_url(f"/modulo?modulo={doc_id}", token)
        doc_type = "Módulo"

    # --- Caso contrário: submódulo ---
    else:
        file_name_part = os.path.basename(doc_id)
        details = {
            'nome': file_name_part.replace('_', ' ').replace('-', ' ').capitalize(),
            'icon': 'fas fa-file-alt'
        }
        url = _montar_url(f"/modulo?submodulo={doc_id}", token)
        parent_dir = os.path.basename(os.path.dirname(doc_id))
        doc_type = parent_dir.capitalize() if parent_dir else "Submódulo"

    # --- Snippet e destaque ---
    snippet = get_context_snippet(content, query=highlight_term or "")
    if highlight_term:
        snippet = filter_service._highlight_terms(snippet, highlight_term)

    # --- Preview de mídia (imagem/vídeo) ---
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

# --------- API JSON (palette / integrações) ----------

@search_bp.get('/api/search')
@login_required
def api_search():
    token = request.args.get('token', '').strip()
    query = request.args.get('q', '').strip()
    module_filter = request.args.get('module', '').strip()

    if query:
        log_search_term(query)

    user_perms = session.get('permissions', {})
    can_view_tecnico = user_perms.get('can_view_tecnico', False)
    can_see_restricted_module = user_perms.get('can_see_restricted_module', False)

    raw_results = search_all_documents(query, token, module_filter, can_view_tecnico)

    if not can_see_restricted_module:
        raw_results = [r for r in raw_results if r.get('module_id') not in MODULOS_RESTRITOS]

    all_modules, _ = carregar_modulos()
    module_details_map = {m['id']: m for m in all_modules}

    doc_ids = [r['module_id'] for r in raw_results]
    access_counts = get_access_counts(doc_ids) if doc_ids else {}

    items = []
    for r in raw_results[:50]:
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

@search_bp.route('/api/recommendations')
@login_required
def api_recommendations():
    token = request.args.get('token', '')

    user_perms = session.get('permissions', {})
    can_see_restricted_module = user_perms.get('can_see_restricted_module', False)

    recs_raw = get_hybrid_recommendations(limit=10) or []
    if not recs_raw:
        current_app.logger.info("Recomendações híbridas vazias. Fallback: 'Mais Acessados'.")
        recs_raw = get_most_accessed(limit=10) or []

    most_raw = get_most_accessed(limit=12) or []

    if not can_see_restricted_module:
        recs_raw = [x for x in recs_raw if x.get('document_id') not in MODULOS_RESTRITOS]
        most_raw = [x for x in most_raw if x.get('document_id') not in MODULOS_RESTRITOS]

    all_modules, _ = carregar_modulos()
    module_details_map = {m['id']: m for m in all_modules}

    doc_ids_to_show = [x['document_id'] for x in (recs_raw + most_raw)]
    access_counts = get_access_counts(doc_ids_to_show) if doc_ids_to_show else {}

    popular_searches = get_popular_searches(limit=10)
    popular_terms = [s['query_term'] for s in popular_searches]

    def _expand_list(raw_list):
        out = []
        for item in raw_list:
            doc_id = item['document_id']
            try:
                content = carregar_markdown(doc_id) or ""
                highlight_term = ""
                for term in popular_terms:
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

    return jsonify({
        'hybrid_recommendations': _expand_list(recs_raw),
        'most_accessed': _expand_list(most_raw),
        'popular_searches': popular_searches[:5],
    })

@search_bp.route('/api/autocomplete')
@login_required
def api_autocomplete():
    query = request.args.get('q', '')
    suggestions = get_autocomplete_suggestions(query, limit=5)
    return jsonify(suggestions)

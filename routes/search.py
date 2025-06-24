from flask import Blueprint, render_template, request, session
from utils.data.module_utils import carregar_modulos, carregar_markdown
from utils.data.search_history import add_search_term, get_recent_searches
from utils.data.module_access import get_most_accessed_with_trend
from utils.auth.auth_utils import login_required
from utils.text.advanced_filter import FiltroAvancado
from markupsafe import Markup
import re

busca_bp = Blueprint('busca', __name__)

@busca_bp.route('/', methods=["GET", "POST"])
@login_required
def busca_pela_raiz():
    """
    Disponível em:
      GET /?token=<TOKEN>&busca=1&q=termo
    Se não vier 'busca' nem 'q', retorna None e index toma a vez.
    """
    acao_busca = request.args.get('busca', '').strip()
    if not acao_busca:
        return None

    nivel = session.get('permission')  # nível de permissão do usuário
    query = request.values.get("q", "").strip()

    modulos, palavras_globais = carregar_modulos()
    filtro = FiltroAvancado(palavras_globais)

    resultados = []
    if query:
        add_search_term(query)
        # busca avançada por módulo e seções
        for m in modulos:
            md_content = carregar_markdown(m["id"])
            if not md_content:
                continue
            # obtém trechos mais relevantes usando TF-IDF + heurísticas
            secoes = filtro.busca_avancada(md_content, query)
            for sec in secoes:
                # sec é um markdown com título e conteúdo já destacado
                # converte quebras de linha em <br> e marca como seguro
                html = Markup(sec.replace('\n', '<br>'))
                resultados.append({
                    "modulo_id": m["id"],
                    "modulo_nome": m["nome"],
                    "trecho": html
                })
    else:
        # mostra módulos mais acessados com tendência
        acessados = get_most_accessed_with_trend(modulos)
        for m, count, tendencia in acessados:
            if count > 0:
                resultados.append({
                    "modulo_id": m["id"],
                    "modulo_nome": m["nome"],
                    "trecho": m.get("descricao", ""),
                    "tendencia": tendencia,
                    "total": count
                })

    recentes = get_recent_searches()
    return render_template(
        'search.html',
        resultados=resultados,
        query=query,
        modulos=modulos,
        modulo_atual=None,
        recentes=recentes
    )

from flask import (
    Blueprint, render_template, session, redirect,
    url_for, request, abort, send_from_directory, current_app
)
import os
import re
from markupsafe import Markup, escape

from utils.data.module_utils import (
    carregar_modulos_aprovados,
    get_modulo_by_id,
    carregar_markdown,
    carregar_markdown_submodulo,
    carregar_markdown_tecnico
)
from utils.text.markdown_utils import parser_wikilinks
from utils.data.module_access import register_access, get_most_accessed_with_trend
from utils.data.search_history import add_search_term, get_recent_searches
from utils.text.advanced_filter import FiltroAvancado
from utils.auth.auth_utils import authenticate_initial_request, logout_user, login_required
from routes.permissions import load_permissions, get_user_group

index_bp = Blueprint('index', __name__)
filtro_global = None  # Global para filtro avançado, inicializado apenas uma vez


def destacar_termo(texto, termo):
    """
    Destaca todas as ocorrências de `termo` dentro de `texto`.
    """
    if not termo or not termo.strip():
        return escape(texto)

    pattern = re.compile(re.escape(termo), re.IGNORECASE)

    def _repl(match):
        return Markup(
            f"<mark style='background:#ffe066;color:#222;border-radius:6px;"
            f"font-weight:600;'>{escape(match.group(0))}</mark>"
        )

    return Markup(pattern.sub(_repl, escape(texto)))


@index_bp.route('/data/img/<path:nome_arquivo>')
def serve_imagem_dinamica(nome_arquivo):
    caminho_base = os.path.join(current_app.root_path, 'data', 'img')
    return send_from_directory(caminho_base, nome_arquivo)


@index_bp.route('/data/videos/<path:nome_arquivo>')
def serve_video(nome_arquivo):
    caminho_base = os.path.join(current_app.root_path, 'data', 'videos')
    return send_from_directory(caminho_base, nome_arquivo)


@index_bp.route('/', methods=['GET'])
def index():
    """
    Roteador único para toda a aplicação:
      1) Autenticação (login por token ou user_name)
      2) Despacho para:
         - Download (se vier ?download=...)
         - Busca    (se vier ?busca=1& q=...)
         - Submódulo(se vier ?submodulo=...)
         - Módulo   (se vier ?modulo=...)
         - Módulo Técnico (se vier ?modulo_tecnico=...)
      3) Página inicial (lista de módulos), se nenhum parâmetro de ação vier.
    """
    global filtro_global

    # 1. Autenticação centralizada
    resultado = authenticate_initial_request()
    if resultado is not True:
        return resultado

    # 2. Permissões da sessão
    grupo, user_name = get_user_group()
    user_perms = session.get('permissions', {})
    can_access_editor           = user_perms.get('can_access_editor', False)
    can_view_tecnico            = user_perms.get('can_view_tecnico', False)
    can_access_permissions_menu = user_perms.get('can_access_permissions_menu', False)

    # Captura parâmetros
    action_download       = request.args.get('download', '').strip()
    action_busca          = request.args.get('busca', '').strip()
    action_submodulo      = request.args.get('submodulo', '').strip()
    action_modulo         = request.args.get('modulo', '').strip()
    action_modulo_tecnico = request.args.get('modulo_tecnico', '').strip()

    # Download
    if action_download:
        pasta = os.path.join(current_app.root_path, 'downloads', 'docs')
        caminho = os.path.join(pasta, action_download)
        if not os.path.isfile(caminho):
            abort(404)
        return send_from_directory(pasta, action_download, as_attachment=True)

    # Busca
    if action_busca:
        query = request.values.get('q', '').strip()
        modulos, palavras_globais = carregar_modulos_aprovados()
        mais_acessados = get_most_accessed_with_trend(modulos)
        resultados = []

        if query:
            add_search_term(query)
            for m in modulos:
                md = carregar_markdown(m['id'])
                if not md:
                    continue
                text_lower = md.lower()
                if query.lower() in text_lower or query.lower() in m['nome'].lower():
                    idx = text_lower.find(query.lower())
                    trecho = md[max(0, idx-60): idx+len(query)+60] if idx>=0 else md[:160]
                    destaque = destacar_termo(trecho.replace('\n',' '), query)
                    resultados.append({
                        'modulo_id': m['id'],
                        'modulo_nome': m['nome'],
                        'trecho': destaque
                    })
        else:
            for m, count, tendencia in mais_acessados:
                if count>0:
                    resultados.append({
                        'modulo_id': m['id'],
                        'modulo_nome': m['nome'],
                        'trecho': m.get('descricao',''),
                        'tendencia': tendencia,
                        'total': count
                    })

        recentes = get_recent_searches()
        return render_template(
            'busca.html', resultados=resultados, query=query,
            modulos=modulos, recentes=recentes,
            mais_acessados=mais_acessados, menus=[]
        )

    # Submódulo
    if action_submodulo:
        nome = action_submodulo
        modulos, palavras_globais = carregar_modulos_aprovados()
        md = carregar_markdown_submodulo(nome)
        if not md:
            return '<h2>Submódulo não encontrado.</h2>', 404
        register_access(nome)
        html = parser_wikilinks(md, modulos, palavras_globais)
        return render_template('submodulo.html', nome=nome, conteudo=html, modulos=modulos, menus=[])

    # Módulo técnico
    if action_modulo_tecnico:
        perms = load_permissions().get('can_view_tecnico', {})
        allowed = (grupo in perms.get('groups', []) or user_name in perms.get('users', []))
        if not allowed:
            return render_template('acesso_negado.html'), 403

        modulos, palavras_globais = carregar_modulos_aprovados()
        if filtro_global is None:
            filtro_global = FiltroAvancado(palavras_globais)

        modulo_id = action_modulo_tecnico
        modulo = get_modulo_by_id(modulos, modulo_id)
        if not modulo:
            abort(404)

        register_access(modulo_id)
        md = carregar_markdown_tecnico(modulo_id)
        if not md:
            return render_template('conteudo_nao_encontrado.html'), 404

        query = request.args.get('q', '').strip()
        if query:
            resultados = filtro_global.busca_avancada(md, query)
            if resultados:
                md_filtrado = '\n\n---\n\n'.join(resultados)
                conteudo_html = parser_wikilinks(md_filtrado, modulos, palavras_globais)
                resultado_highlight = True
            else:
                conteudo_html = "<p class='text-danger'>Nenhum resultado encontrado.</p>"
                resultado_highlight = True
        else:
            conteudo_html = parser_wikilinks(md, modulos, palavras_globais)
            resultado_highlight = False

        relacionados = [m for m in modulos if m['id'] in modulo.get('relacionados', [])]
        return render_template(
            'modulo.html', modulo=modulo, conteudo=conteudo_html,
            relacionados=relacionados, modulos=modulos,
            modulo_atual=modulo, query=query,
            resultado_highlight=resultado_highlight, menus=[]
        )

    # Módulo comum
    if action_modulo:
        mod_id = action_modulo
        modulos, palavras_globais = carregar_modulos_aprovados()
        if filtro_global is None:
            filtro_global = FiltroAvancado(palavras_globais)

        modulo = get_modulo_by_id(modulos, mod_id)
        if not modulo:
            abort(404)

        register_access(mod_id)
        md = carregar_markdown(mod_id)
        if not md:
            return render_template('conteudo_nao_encontrado.html'), 404

        query = request.args.get('q', '').strip()
        if query:
            resultados = filtro_global.busca_avancada(md, query)
            if resultados:
                md_filtrado = '\n\n---\n\n'.join(resultados)
                conteudo_html = parser_wikilinks(md_filtrado, modulos, palavras_globais)
                resultado_highlight = True
            else:
                conteudo_html = "<p class='text-danger'>Nenhum resultado encontrado.</p>"
                resultado_highlight = True
        else:
            conteudo_html = parser_wikilinks(md, modulos, palavras_globais)
            resultado_highlight = False

        relacionados = [m for m in modulos if m['id'] in modulo.get('relacionados', [])]
        return render_template(
            'modulo.html', modulo=modulo, conteudo=conteudo_html,
            relacionados=relacionados, modulos=modulos,
            modulo_atual=modulo, query=query,
            resultado_highlight=resultado_highlight, menus=[]
        )

    # Página inicial
    modulos, _ = carregar_modulos_aprovados()
    return render_template(
        'index.html', modulos=modulos,
        can_access_editor=can_access_editor,
        can_view_tecnico=can_view_tecnico,
        can_access_permissions_menu=can_access_permissions_menu,
        menus=[]
    )


@index_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return render_template('logout.html')

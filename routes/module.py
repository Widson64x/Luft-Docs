from flask import Blueprint, render_template, request, abort, redirect, url_for
from utils.data.module_utils import (
    carregar_modulos,
    get_modulo_by_id,
    carregar_markdown,
    carregar_markdown_tecnico,
    carregar_markdown_submodulo
)
from utils.text.markdown_utils import parser_wikilinks
from utils.data.module_access import register_access
from utils.auth.auth_utils import login_required

# Blueprint para as rotas de módulo, registrado com o prefixo /modulo em app.py
modulo_bp = Blueprint('modulo', __name__)

@modulo_bp.route('/', methods=['GET'])
@login_required
def ver_modulo_pela_raiz():
    """
    Renderiza o conteúdo de um módulo (normal ou técnico) ou de um submódulo.
    Graças ao url_prefix em app.py, esta rota responde em /modulo/
    e espera parâmetros como:
      - /modulo?modulo=ID_DO_MODULO
      - /modulo?modulo_tecnico=ID_DO_MODULO
      - /modulo?submodulo=NOME_DO_SUBMODULO
    """
    # Parâmetros da URL
    param_mod = request.args.get('modulo', '').strip()
    param_tech = request.args.get('modulo_tecnico', '').strip()
    param_sub = request.args.get('submodulo', '').strip()

    modulos, palavras_globais = carregar_modulos()

    # 1) Prioridade para Submódulo
    if param_sub:
        md_content = carregar_markdown_submodulo(param_sub)
        if not md_content:
            abort(404, "Submódulo não encontrado.")
        
        register_access(param_sub)
        conteudo_html = parser_wikilinks(md_content, modulos, palavras_globais)
        
        return render_template(
            'submodule.html',
            nome=param_sub,
            conteudo=conteudo_html,
            modulos=modulos
        )

    # 2) Módulo normal ou técnico
    if not param_mod and not param_tech:
        # Se nenhum ID de módulo for fornecido, redireciona para a página inicial
        # O token é pego da sessão, não precisa passar na URL aqui.
        return redirect(url_for('index.index'))

    is_tech = bool(param_tech)
    modulo_id = param_tech if is_tech else param_mod

    # Busca o módulo pelo ID
    modulo = get_modulo_by_id(modulos, modulo_id)
    if not modulo:
        abort(404, "Módulo não encontrado.")

    # Carrega o conteúdo Markdown
    if is_tech:
        md_content = carregar_markdown_tecnico(modulo_id)
    else:
        md_content = carregar_markdown(modulo_id)

    if not md_content:
        # Se o arquivo do módulo não for encontrado ou estiver vazio
        return render_template('conteudo_nao_encontrado.html'), 404
    
    # Registra o acesso ao módulo
    register_access(modulo_id)
    
    # Processa o conteúdo para HTML
    conteudo_html = parser_wikilinks(md_content, modulos, palavras_globais)

    # Encontra módulos relacionados
    relacionados_ids = modulo.get('relacionados', [])
    relacionados = [m for m in modulos if m['id'] in relacionados_ids]

    # Renderiza o template do módulo
    return render_template(
        'module.html',
        modulo=modulo,
        conteudo=conteudo_html,
        relacionados=relacionados,
        modulos=modulos,
        modulo_atual=modulo,
        query=None,
        resultado_highlight=False
    )
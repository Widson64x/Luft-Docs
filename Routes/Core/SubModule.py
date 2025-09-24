# routes/submodule.py

from flask import Blueprint, render_template, request, abort, redirect, url_for
from Utils.data.module_utils import carregar_modulos, carregar_markdown_submodulo
from Utils.text.markdown_utils import parser_wikilinks
from Utils.auth.auth_utils import login_required

from Utils.recommendation_service import log_document_access

# Blueprint registrado com o prefixo /submodule em app.py
submodulo_bp = Blueprint('submodulo', __name__, url_prefix="/luft-docs/submodule")

@submodulo_bp.route('/', methods=['GET'])
@login_required
def ver_submodulo():
    """
    Renderiza o conteúdo de um submódulo e regista o seu acesso.
    """
    nome_submodulo = request.args.get('nome', '').strip()

    if not nome_submodulo:
        return redirect(url_for('index.index'))

    modulos, palavras_globais = carregar_modulos()
    md_content = carregar_markdown_submodulo(nome_submodulo)

    if not md_content:
        abort(404, "Submódulo não encontrado.")

    # --- CORREÇÃO: Regista o acesso usando o novo sistema ---
    log_document_access(nome_submodulo)
    
    conteudo_html = parser_wikilinks(md_content, modulos, palavras_globais)

    return render_template(
        'Modules/SubModule.html',
        nome=nome_submodulo,
        conteudo=conteudo_html,
        modulos=modulos
    )
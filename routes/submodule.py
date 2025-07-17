# routes/submodule.py

from flask import Blueprint, render_template, request, abort, redirect, url_for
from utils.data.module_utils import carregar_modulos, carregar_markdown_submodulo
from utils.text.markdown_utils import parser_wikilinks
from utils.data.module_access import register_access
from utils.auth.auth_utils import login_required

# Blueprint registrado com o prefixo /submodule em app.py
submodulo_bp = Blueprint('submodulo', __name__)

@submodulo_bp.route('/', methods=['GET'])
@login_required
def ver_submodulo():
    """
    Renderiza o conteúdo de um submódulo.
    Graças ao url_prefix em app.py, esta rota responde em /submodule/
    e espera o parâmetro 'nome':
      - /submodule?nome=NOME_DO_SUBMODULO
    """
    # Busca o nome do submódulo pelo parâmetro 'nome' na URL.
    nome_submodulo = request.args.get('nome', '').strip()

    # Se nenhum nome for fornecido, redireciona para a página inicial.
    if not nome_submodulo:
        return redirect(url_for('index.index'))

    # Carrega os dados necessários.
    modulos, palavras_globais = carregar_modulos()
    md_content = carregar_markdown_submodulo(nome_submodulo)

    # Se o conteúdo do submódulo não for encontrado, retorna um erro 404.
    if not md_content:
        abort(404, "Submódulo não encontrado.")

    # Registra o acesso e processa o conteúdo para HTML.
    register_access(nome_submodulo)
    conteudo_html = parser_wikilinks(md_content, modulos, palavras_globais)

    # Renderiza o template do submódulo.
    return render_template(
        'submodule.html',
        nome=nome_submodulo,
        conteudo=conteudo_html,
        modulos=modulos
    )


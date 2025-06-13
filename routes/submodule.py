# routes/submodule.py

from flask import Blueprint, render_template, request, session
from utils.data.module_utils import carregar_modulos, carregar_markdown_submodulo
from utils.text.markdown_utils import parser_wikilinks
from utils.data.module_access import register_access
from utils.auth.auth_utils import login_required

submodulo_bp = Blueprint('submodulo', __name__)

@submodulo_bp.route('/', methods=['GET'])
@login_required
def ver_submodulo_pela_raiz():
    """
    Acessível em:
      GET /?token=<TOKEN>&modulo/submodulo=<NOME_DO_SUBMODULO>
    - Se não vier 'modulo/submodulo' na query, retorna None para deixar outro handler tratar.
    """

    # Método para pegar o Nível de Permissão
    nivel = session.get('permission')
    print(nivel)

    nome = request.args.get('modulo/submodulo', '').strip()
    if not nome:
        return None

    modulos, palavras_globais = carregar_modulos()
    md_content = carregar_markdown_submodulo(nome)
    if not md_content:
        return "<h2>Submódulo não encontrado.</h2>", 404

    register_access(nome)
    conteudo_html = parser_wikilinks(md_content, modulos, palavras_globais)

    return render_template(
        'submodulo.html',
        nome=nome,
        conteudo=conteudo_html,
        modulos=modulos
    )

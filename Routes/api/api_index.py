# routes/api.py

import math
from flask import Blueprint, request, jsonify, session, current_app
from Utils.auth.auth_utils import login_required
from Utils.data.module_utils import carregar_modulos_aprovados, carregar_markdown
from Utils.permissions_config import MODULOS_RESTRITOS, MODULOS_TECNICOS_VISIVEIS
import time

# Blueprint para a API
api_bp = Blueprint('api', __name__, url_prefix='/api')

CARDS_PER_PAGE = 9

@api_bp.route('/modules', methods=['GET'])
@login_required
def get_modules():
    """
    Endpoint da API para buscar e paginar módulos.
    Aceita os parâmetros de query: ?search=... & page=...
    """
    # 1. Obter parâmetros da requisição
    search_query = request.args.get('search', '').lower().strip()
    page = request.args.get('page', 1, type=int)

    # 2. Obter permissões do usuário da sessão
    user_perms = session.get('permissions', {})
    can_see_restricted_module = user_perms.get('can_see_restricted_module', False)
    can_view_tecnico = user_perms.get('can_view_tecnico', False)
    can_create_modules = user_perms.get('can_create_modules', False)

    # 3. Carregar e filtrar módulos baseados na permissão de visualização
    modulos_aprovados, _ = carregar_modulos_aprovados()
    modulos_visiveis = []
    for m in modulos_aprovados:
        if m.get('id') in MODULOS_RESTRITOS:
            if can_see_restricted_module:
                modulos_visiveis.append(m)
        else:
            modulos_visiveis.append(m)
    
    # 4. Aplicar filtro de busca, se houver
    if search_query:
        lista_de_cards_filtrada = [
            m for m in modulos_visiveis 
            if search_query in m.get('nome', '').lower() or search_query in m.get('descricao', '').lower()
        ]
    else:
        lista_de_cards_filtrada = modulos_visiveis

    # 5. Adicionar dados extras aos cards filtrados
    # E adicionar o card "Criar Módulo" se não houver busca
    lista_final_de_cards = []
    for m in lista_de_cards_filtrada:
        md_content = carregar_markdown(m['id'])
        m['has_content'] = bool(md_content and md_content.strip())
        m['show_tecnico_button'] = m['id'] in MODULOS_TECNICOS_VISIVEIS or can_view_tecnico
        lista_final_de_cards.append(m)
    
    # Adiciona o card de criação APENAS se não houver termo de busca
    if not search_query and can_create_modules:
        card_criar = {'type': 'create_card'}
        lista_final_de_cards.append(card_criar)

    # 6. Paginar os resultados FINAIS
    total_items = len(lista_final_de_cards)
    total_pages = math.ceil(total_items / CARDS_PER_PAGE)
    start = (page - 1) * CARDS_PER_PAGE
    end = start + CARDS_PER_PAGE
    cards_na_pagina = lista_final_de_cards[start:end]

    time.sleep(0.5)
    # 7. Retornar dados em formato JSON
    return jsonify({
        'cards': cards_na_pagina,
        'current_page': page,
        'total_pages': total_pages,
        'token': request.args.get('token') # Passa o token para o frontend
    })
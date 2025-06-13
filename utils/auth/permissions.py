# utils/auth/permissions.py

"""
Módulo central de permissões da aplicação.
Permissões baseadas na lista de menus que vem da API (já mapeados para nomes internos!).
Exemplo: se o usuário tem 'seguranca' nos menus, ele pode acessar rotas e recursos protegidos por esse menu.
"""

def get_user_menu_list():
    """
    Retorna a lista de menus internos do usuário atual, conforme salvo na sessão.
    Útil para checagens no backend.
    """
    from flask import session
    return session.get('menus', [])

def can(menus, nome_menu):
    """
    Verifica se o usuário tem acesso ao menu específico.
    - menus: lista de nomes de menus do usuário (ex: ['seguranca', 'parametros'])
    - nome_menu: nome do menu (case-insensitive, nome interno)
    Retorna True se o menu estiver na lista do usuário.
    """
    if not menus or not nome_menu:
        return False
    nome_menu = nome_menu.strip().lower()
    # menus pode vir da sessão (lista), do template ou backend
    return any(str(menu).strip().lower() == nome_menu for menu in menus)

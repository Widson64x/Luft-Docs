"""Utilitarios de estruturacao de menus."""

from typing import Any, Dict, List


def organizarMenus(listaMenus: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Organiza a lista plana de menus em uma arvore hierarquica.

    Args:
        listaMenus: Colecao plana de menus contendo a chave Codigo_Menu.

    Returns:
        List[Dict[str, Any]]: Estrutura de menus agrupada por nivel hierarquico.
    """
    menusPorCodigo = {
        menu["Codigo_Menu"]: {**menu, "submenus": []}
        for menu in listaMenus
    }
    estruturaMenus: Dict[int, Dict[str, Any]] = {}

    for codigoMenu in sorted(menusPorCodigo.keys()):
        if codigoMenu < 100:
            estruturaMenus[codigoMenu] = menusPorCodigo[codigoMenu]
            continue

        if codigoMenu < 10000:
            codigoPai = int(str(codigoMenu)[:2])
            if codigoPai in estruturaMenus:
                estruturaMenus[codigoPai]["submenus"].append(menusPorCodigo[codigoMenu])
            continue

        codigoPai = int(str(codigoMenu)[:4])
        for menuPrincipal in estruturaMenus.values():
            submenuPai = next(
                (
                    submenuAtual
                    for submenuAtual in menuPrincipal["submenus"]
                    if submenuAtual["Codigo_Menu"] == codigoPai
                ),
                None,
            )
            if submenuPai is not None:
                submenuPai["submenus"].append(menusPorCodigo[codigoMenu])
                break

    return list(estruturaMenus.values())

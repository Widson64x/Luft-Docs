from __future__ import annotations

import math
import time

from flask import session

from Utils.ConfiguracaoPermissoes import MODULOS_RESTRITOS, MODULOS_TECNICOS_VISIVEIS
from Utils.data.UtilitariosModulo import CarregarMarkdown, CarregarModulosAprovados


class ServicoApiModulos:
    """Centraliza a regra de negocio da listagem paginada de modulos."""

    CARDS_POR_PAGINA = 9

    def obterRespostaListaModulos(
        self, consulta: str, pagina: int, token: str | None
    ) -> dict[str, object]:
        """Retorna o payload JSON da API de modulos da pagina inicial."""
        permissao_usuario = session.get("permissions", {})
        pode_ver_restritos = permissao_usuario.get(
            "can_see_restricted_module",
            False,
        )
        pode_ver_tecnico = permissao_usuario.get("can_view_tecnico", False)
        pode_criar_modulos = permissao_usuario.get("can_create_modules", False)

        modulos_aprovados, _ = CarregarModulosAprovados()
        modulos_visiveis = []
        for modulo in modulos_aprovados:
            if modulo.get("id") in MODULOS_RESTRITOS and not pode_ver_restritos:
                continue
            modulos_visiveis.append(modulo)

        if consulta:
            cards_filtrados = [
                modulo
                for modulo in modulos_visiveis
                if consulta in modulo.get("nome", "").lower()
                or consulta in modulo.get("descricao", "").lower()
            ]
        else:
            cards_filtrados = modulos_visiveis

        cards = []
        for modulo in cards_filtrados:
            conteudo_markdown = CarregarMarkdown(modulo["id"])
            modulo["has_content"] = bool(conteudo_markdown and conteudo_markdown.strip())
            modulo["show_tecnico_button"] = (
                modulo["id"] in MODULOS_TECNICOS_VISIVEIS or pode_ver_tecnico
            )
            cards.append(modulo)

        if not consulta and pode_criar_modulos:
            cards.append({"type": "create_card"})

        total_itens = len(cards)
        total_paginas = math.ceil(total_itens / self.CARDS_POR_PAGINA) if total_itens else 0
        inicio = (pagina - 1) * self.CARDS_POR_PAGINA
        fim = inicio + self.CARDS_POR_PAGINA

        time.sleep(0.5)
        return {
            "cards": cards[inicio:fim],
            "current_page": pagina,
            "total_pages": total_paginas,
            "token": token,
        }
from __future__ import annotations

import math
import time

from Services.PermissaoService import ChavesPermissao, PermissaoService
from Utils.data.UtilitariosModulo import (
    CarregarMarkdown,
    CarregarModulosAprovados,
    FiltrarModulosRestritos,
    ModuloPossuiDocumentacaoTecnica,
)


class ServicoApiModulos:
    """Centraliza a regra de negocio da listagem paginada de modulos."""

    CARDS_POR_PAGINA = 12

    def obterRespostaListaModulos(
        self, consulta: str, pagina: int, token: str | None
    ) -> dict[str, object]:
        """Retorna o payload JSON da API de modulos da pagina inicial."""
        pode_ver_restritos = PermissaoService.usuarioPossuiPermissao(
            ChavesPermissao.VISUALIZAR_MODULOS_RESTRITOS
        )
        pode_ver_tecnico = PermissaoService.usuarioPossuiPermissao(
            ChavesPermissao.VISUALIZAR_MODULOS_TECNICOS
        )
        pode_criar_modulos = PermissaoService.usuarioPossuiPermissao(
            ChavesPermissao.CRIAR_MODULOS
        )

        modulos_aprovados, _ = CarregarModulosAprovados()
        modulos_visiveis = FiltrarModulosRestritos(
            modulos_aprovados,
            pode_ver_restritos,
        )

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
                pode_ver_tecnico
                and ModuloPossuiDocumentacaoTecnica(modulo["id"])
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

    def obterRespostaArvoreModulos(self) -> dict[str, object]:
        """Retorna uma lista enxuta de modulos visiveis para a sidebar."""
        pode_ver_restritos = PermissaoService.usuarioPossuiPermissao(
            ChavesPermissao.VISUALIZAR_MODULOS_RESTRITOS
        )

        modulos_aprovados, _ = CarregarModulosAprovados()
        modulos_visiveis = []
        for modulo in FiltrarModulosRestritos(modulos_aprovados, pode_ver_restritos):
            modulos_visiveis.append(
                {
                    "id": modulo["id"],
                    "nome": modulo.get("nome") or modulo["id"],
                    "icone": modulo.get("icone") or "ph-bold ph-cube",
                    "descricao": modulo.get("descricao") or "",
                }
            )

        modulos_visiveis.sort(
            key=lambda item: (
                item["nome"].lower(),
                item["id"].lower(),
            )
        )
        return {
            "modules": modulos_visiveis,
            "total": len(modulos_visiveis),
        }
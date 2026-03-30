from __future__ import annotations

from typing import Any

from Utils.ServicoRecomendacao import RegistrarAcessoDocumento
from Utils.data.UtilitariosModulo import CarregarMarkdownSubmodulo, CarregarModulos
from Utils.text.UtilitariosMarkdown import ConverterWikiLinks


class ServicoSubModulo:
    """Centraliza a regra de negocio da rota dedicada de submodulos."""

    def obterRespostaSubmodulo(self, nomeSubmodulo: str) -> dict[str, Any]:
        """Resolve a resposta apropriada para a exibicao de um submodulo."""
        if not nomeSubmodulo:
            return {
                "tipo": "redirecionar",
                "endpoint": "index.exibirInicio",
                "parametros": {},
            }

        modulos, palavras_globais = CarregarModulos()
        conteudo_markdown = CarregarMarkdownSubmodulo(nomeSubmodulo)
        if not conteudo_markdown:
            return {
                "tipo": "erro",
                "codigo": 404,
                "mensagem": "Submodulo nao encontrado.",
            }

        RegistrarAcessoDocumento(nomeSubmodulo)
        conteudo_html = ConverterWikiLinks(conteudo_markdown, modulos, palavras_globais)
        return {
            "tipo": "template",
            "template": "Modules/SubModule.html",
            "contexto": {
                "nome": nomeSubmodulo,
                "conteudo": conteudo_html,
                "modulos": modulos,
                "luft_app_name": nomeSubmodulo,
            },
            "codigo": 200,
        }
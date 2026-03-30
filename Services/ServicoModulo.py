from __future__ import annotations

from datetime import datetime
from typing import Any

from flask import session
from sqlalchemy.orm import joinedload

from Models import Modulo
from Utils.ConfiguracaoPermissoes import MODULOS_TECNICOS_VISIVEIS
from Utils.ServicoRecomendacao import RegistrarAcessoDocumento
from Utils.data.UtilitariosModulo import (
    CarregarMarkdown,
    CarregarMarkdownSubmodulo,
    CarregarMarkdownTecnico,
    CarregarModulos,
)
from Utils.text.ServicoFiltroConteudo import ServicoFiltroConteudo
from Utils.text.UtilitariosMarkdown import ConverterWikiLinks


class ServicoModulo:
    """Centraliza a regra de negocio de visualizacao de modulos e submodulos."""

    def __init__(self) -> None:
        self.servicoFiltroConteudo = ServicoFiltroConteudo()

    def obterRespostaConteudo(
        self,
        idModulo: str,
        idModuloTecnico: str,
        idSubmodulo: str,
        consulta: str,
        token: str,
    ) -> dict[str, Any]:
        """Resolve a resposta apropriada para a rota principal de modulos."""
        modulos, palavras_globais = CarregarModulos()

        if idSubmodulo:
            return self._obterRespostaSubmodulo(idSubmodulo, consulta, modulos, palavras_globais)

        if not idModulo and not idModuloTecnico:
            return {
                "tipo": "redirecionar",
                "endpoint": "index.exibirInicio",
                "parametros": {},
            }

        documentacao_tecnica = bool(idModuloTecnico)
        identificador_modulo = idModuloTecnico if documentacao_tecnica else idModulo

        if documentacao_tecnica and not self._usuarioPodeVerModuloTecnico(identificador_modulo):
            return {
                "tipo": "template",
                "template": "Auth/AccessDenied.html",
                "contexto": {},
                "codigo": 403,
            }

        modulo = (
            Modulo.query.options(
                joinedload(Modulo.roteiros),
                joinedload(Modulo.relacionados),
                joinedload(Modulo.edit_history),
            )
            .filter_by(id=identificador_modulo)
            .first()
        )

        if not modulo:
            return {
                "tipo": "erro",
                "codigo": 404,
                "mensagem": "Modulo nao encontrado.",
            }

        conteudo_markdown = self._obterConteudoModulo(
            identificador_modulo, documentacao_tecnica, consulta
        )
        if not conteudo_markdown:
            return {
                "tipo": "template",
                "template": "Auth/Dev.html",
                "contexto": {},
                "codigo": 404,
            }

        RegistrarAcessoDocumento(
            f"tech_{identificador_modulo}" if documentacao_tecnica else identificador_modulo
        )

        conteudo_html = ConverterWikiLinks(conteudo_markdown, modulos, palavras_globais)
        permissoes_usuario = session.get("permissions", {})

        return {
            "tipo": "template",
            "template": "Modules/Modulos.html",
            "contexto": {
                "modulo": modulo,
                "conteudo": conteudo_html,
                "relacionados": modulo.relacionados,
                "modulos": modulos,
                "query": consulta,
                "resultado_highlight": bool(consulta),
                "versao_info": self._obterInformacoesVersao(modulo),
                "id_do_modulo": identificador_modulo,
                "token": token,
                "modulo_icone": modulo.icone or "bi-box",
                "modulo_atual": modulo,
                "proactive_module_name": modulo.nome,
                "proactive_module_id": modulo.id,
                "roteiros_data": [roteiro.to_dict() for roteiro in modulo.roteiros],
                "can_edit_scripts": permissoes_usuario.get("can_edit_scripts", False),
            },
            "codigo": 200,
        }

    def _obterRespostaSubmodulo(
        self,
        idSubmodulo: str,
        consulta: str,
        modulos: list[dict[str, Any]],
        palavrasGlobais: dict[str, str],
    ) -> dict[str, Any]:
        """Monta a resposta de renderizacao para um submodulo acessado pela rota de modulo."""
        conteudo_markdown = CarregarMarkdownSubmodulo(idSubmodulo)
        if not conteudo_markdown:
            return {
                "tipo": "erro",
                "codigo": 404,
                "mensagem": "Submodulo nao encontrado.",
            }

        RegistrarAcessoDocumento(idSubmodulo)
        if consulta:
            conteudo_markdown = self.servicoFiltroConteudo.filtrarConteudoSubmodulo(
                conteudo_markdown, consulta
            )

        conteudo_html = ConverterWikiLinks(conteudo_markdown, modulos, palavrasGlobais)
        return {
            "tipo": "template",
            "template": "Modules/SubModule.html",
            "contexto": {
                "nome": idSubmodulo,
                "conteudo": conteudo_html,
                "modulos": modulos,
                "query": consulta,
            },
            "codigo": 200,
        }

    def _usuarioPodeVerModuloTecnico(self, identificadorModulo: str) -> bool:
        """Valida a permissao de acesso a documentacao tecnica."""
        permissoes_usuario = session.get("permissions", {})
        return permissoes_usuario.get("can_view_tecnico", False) or (
            identificadorModulo in MODULOS_TECNICOS_VISIVEIS
        )

    def _obterConteudoModulo(
        self, identificadorModulo: str, documentacaoTecnica: bool, consulta: str
    ) -> str | None:
        """Carrega e aplica os filtros de conteudo do modulo solicitado."""
        conteudo = (
            CarregarMarkdownTecnico(identificadorModulo)
            if documentacaoTecnica
            else CarregarMarkdown(identificadorModulo)
        )
        if not conteudo or not consulta:
            return conteudo

        if documentacaoTecnica:
            return self.servicoFiltroConteudo.filtrarDocumentacaoTecnica(conteudo, consulta)
        return self.servicoFiltroConteudo.filtrarDocumentacao(conteudo, consulta)

    def _obterInformacoesVersao(self, modulo: Modulo) -> dict[str, str]:
        """Monta as informacoes de versao utilizadas na tela do modulo."""
        informacoes_versao = {
            "versao_atual": "N/A",
            "data_aprovacao": "N/A",
            "editor": "N/A",
        }

        versao_atual = modulo.current_version
        data_aprovacao = modulo.last_approved_on
        if not versao_atual or not data_aprovacao:
            return informacoes_versao

        data_aprovacao_formatada = "Data indisponivel"
        try:
            data_objeto = datetime.fromisoformat(data_aprovacao)
            data_aprovacao_formatada = data_objeto.strftime("%d/%m/%Y as %H:%M")
        except (TypeError, ValueError):
            pass

        editor_responsavel = "Nao encontrado"
        for entrada_historico in modulo.edit_history:
            if entrada_historico.version == versao_atual:
                editor_responsavel = entrada_historico.editor or "Nao encontrado"
                break

        informacoes_versao.update(
            {
                "versao_atual": versao_atual,
                "data_aprovacao": data_aprovacao_formatada,
                "editor": editor_responsavel,
            }
        )
        return informacoes_versao
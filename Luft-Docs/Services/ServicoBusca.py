from __future__ import annotations

import os
import re
from urllib.parse import urlencode

from flask import current_app, request, url_for

from Services.PermissaoService import ChavesPermissao, PermissaoService
from Utils.ServicoRecomendacao import (
    ObterBuscasPopulares,
    ObterContagensAcesso,
    ObterMaisAcessados,
    ObterRecomendacoesHibridas,
    ObterSugestoesAutocomplete,
    RegistrarTermoBusca,
)
from Utils.data.UtilitariosBusca import BuscarTodosDocumentos, ExtrairPreviaMidia
from Utils.data.UtilitariosModulo import (
    CarregarMarkdown,
    CarregarModulos,
    CriarMapaRestricaoModulos,
    DocumentoEhRestrito,
    DocumentoEhTecnico,
    FiltrarModulosRestritos,
)
from Utils.text.ServicoFiltroConteudo import ServicoFiltroConteudo


class ServicoBusca:
    """Centraliza a regra de negocio das rotas de busca e recomendacao."""

    def __init__(self) -> None:
        self._servico_filtro_conteudo = ServicoFiltroConteudo()

    def obterContextoBusca(
        self, consulta: str, filtro_modulo: str, token: str
    ) -> dict[str, object]:
        """Monta o contexto da pagina de busca com resultados e filtros."""
        if consulta:
            RegistrarTermoBusca(consulta)

        pode_ver_tecnico = PermissaoService.usuarioPossuiPermissao(
            ChavesPermissao.VISUALIZAR_MODULOS_TECNICOS
        )
        pode_ver_restritos = PermissaoService.usuarioPossuiPermissao(
            ChavesPermissao.VISUALIZAR_MODULOS_RESTRITOS
        )
        todos_modulos, _ = CarregarModulos()
        mapa_restricoes = CriarMapaRestricaoModulos(todos_modulos)

        resultados_brutos = BuscarTodosDocumentos(
            consulta,
            token,
            filtro_modulo,
            pode_ver_tecnico,
        )
        resultados_filtrados = self._filtrarRestritos(
            resultados_brutos,
            pode_ver_restritos,
            mapa_restricoes,
        )

        resultados_processados = []
        for resultado in resultados_filtrados:
            trecho = self._obterTrechoContextual(resultado["content"], consulta)
            resultado["snippet"] = self._servico_filtro_conteudo.destacarTermos(
                trecho,
                consulta,
            )
            resultados_processados.append(resultado)

        modulos_dropdown = FiltrarModulosRestritos(todos_modulos, pode_ver_restritos)

        return {
            "query": consulta,
            "results": self._decorarResultados(resultados_processados, token),
            "total_results": len(resultados_processados),
            "modules": modulos_dropdown,
            "current_filter": filtro_modulo,
            "token": token,
        }

    def obterResultadosBuscaApi(
        self, consulta: str, filtro_modulo: str, token: str
    ) -> dict[str, object]:
        """Retorna o payload JSON da busca para integrações do frontend."""
        if consulta:
            RegistrarTermoBusca(consulta)

        pode_ver_tecnico = PermissaoService.usuarioPossuiPermissao(
            ChavesPermissao.VISUALIZAR_MODULOS_TECNICOS
        )
        pode_ver_restritos = PermissaoService.usuarioPossuiPermissao(
            ChavesPermissao.VISUALIZAR_MODULOS_RESTRITOS
        )
        todos_modulos, _ = CarregarModulos()
        mapa_restricoes = CriarMapaRestricaoModulos(todos_modulos)

        resultados_brutos = BuscarTodosDocumentos(
            consulta,
            token,
            filtro_modulo,
            pode_ver_tecnico,
        )
        resultados_filtrados = self._filtrarRestritos(
            resultados_brutos,
            pode_ver_restritos,
            mapa_restricoes,
        )

        mapa_modulos = {modulo["id"]: modulo for modulo in todos_modulos}
        ids_documentos = [resultado["module_id"] for resultado in resultados_filtrados]
        contagens_acesso = ObterContagensAcesso(ids_documentos) if ids_documentos else {}

        itens = []
        for resultado in resultados_filtrados[:50]:
            try:
                identificador = resultado["module_id"]
                conteudo = resultado.get("content") or CarregarMarkdown(identificador) or ""
                itens.append(
                    self._montarPayloadDocumento(
                        doc_id=identificador,
                        token=token,
                        mapa_modulos=mapa_modulos,
                        conteudo=conteudo,
                        termo_destaque=consulta,
                        contagem_acesso=contagens_acesso.get(identificador, 0),
                    )
                )
            except Exception as erro:
                current_app.logger.error(
                    "Erro ao montar payload de busca '%s': %s",
                    resultado,
                    erro,
                    exc_info=True,
                )

        return {"results": itens}

    def obterRecomendacoes(self, token: str) -> dict[str, object]:
        """Retorna recomendacoes hibridas, mais acessados e buscas populares."""
        pode_ver_tecnico = PermissaoService.usuarioPossuiPermissao(
            ChavesPermissao.VISUALIZAR_MODULOS_TECNICOS
        )
        pode_ver_restritos = PermissaoService.usuarioPossuiPermissao(
            ChavesPermissao.VISUALIZAR_MODULOS_RESTRITOS
        )
        todos_modulos, _ = CarregarModulos()
        mapa_restricoes = CriarMapaRestricaoModulos(todos_modulos)

        recomendacoes = ObterRecomendacoesHibridas(limite=10) or []
        if not recomendacoes:
            current_app.logger.info(
                "Recomendacoes hibridas vazias. Fallback: 'Mais Acessados'."
            )
            recomendacoes = ObterMaisAcessados(limite=10) or []

        mais_acessados = ObterMaisAcessados(limite=12) or []
        if not pode_ver_tecnico:
            recomendacoes = [
                item
                for item in recomendacoes
                if not DocumentoEhTecnico(item.get("document_id"))
            ]
            mais_acessados = [
                item
                for item in mais_acessados
                if not DocumentoEhTecnico(item.get("document_id"))
            ]
        if not pode_ver_restritos:
            recomendacoes = [
                item
                for item in recomendacoes
                if not DocumentoEhRestrito(item.get("document_id"), mapa_restricoes)
            ]
            mais_acessados = [
                item
                for item in mais_acessados
                if not DocumentoEhRestrito(item.get("document_id"), mapa_restricoes)
            ]

        mapa_modulos = {modulo["id"]: modulo for modulo in todos_modulos}
        ids_documentos = [
            item["document_id"] for item in (recomendacoes + mais_acessados)
        ]
        contagens_acesso = (
            ObterContagensAcesso(ids_documentos) if ids_documentos else {}
        )

        buscas_populares = ObterBuscasPopulares(limite=10)
        termos_populares = [item["query_term"] for item in buscas_populares]

        def expandir(lista_bruta: list[dict[str, object]]) -> list[dict[str, object]]:
            itens = []
            for item in lista_bruta:
                identificador = item["document_id"]
                try:
                    conteudo = CarregarMarkdown(identificador) or ""
                    termo_destaque = ""
                    for termo in termos_populares:
                        if re.search(
                            r"\b" + re.escape(termo) + r"\b",
                            conteudo,
                            re.IGNORECASE,
                        ):
                            termo_destaque = termo
                            break
                    itens.append(
                        self._montarPayloadDocumento(
                            doc_id=identificador,
                            token=token,
                            mapa_modulos=mapa_modulos,
                            conteudo=conteudo,
                            termo_destaque=termo_destaque,
                            contagem_acesso=contagens_acesso.get(identificador, 0),
                        )
                    )
                except Exception as erro:
                    current_app.logger.error(
                        "Erro em recommendations payload '%s': %s",
                        identificador,
                        erro,
                        exc_info=True,
                    )
            return itens

        return {
            "hybrid_recommendations": expandir(recomendacoes),
            "most_accessed": expandir(mais_acessados),
            "popular_searches": buscas_populares[:5],
        }

    def obterAutocomplete(self, consulta: str) -> list[str]:
        """Retorna sugestoes de autocomplete para a caixa de busca."""
        return ObterSugestoesAutocomplete(consulta, limite=5)

    def _decorarResultados(
        self, resultados: list[dict[str, object]], token: str
    ) -> list[dict[str, object]]:
        decorados = []
        for resultado in resultados:
            url_navegacao = resultado.get("url")
            if not url_navegacao:
                identificador = resultado.get("module_id")
                if identificador:
                    url_navegacao = self._montarUrlDocumento(identificador, token)
            else:
                url_navegacao = self._normalizarUrlRelativa(str(url_navegacao))

            previa = self._normalizarPrevia(resultado.get("preview"), token)
            decorados.append({**resultado, "url": url_navegacao, "preview": previa})
        return decorados

    def _montarPayloadDocumento(
        self,
        doc_id: str,
        token: str,
        mapa_modulos: dict[str, dict[str, object]],
        conteudo: str,
        termo_destaque: str = "",
        contagem_acesso: int = 0,
    ) -> dict[str, object]:
        if str(doc_id).startswith("tech_"):
            identificador_limpo = str(doc_id).replace("tech_", "", 1)
            detalhes = mapa_modulos.get(
                doc_id,
                {"nome": identificador_limpo.capitalize(), "icon": "fas fa-tools"},
            )
            url = self._montarUrlComToken(
                f"/modulo?modulo_tecnico={identificador_limpo}",
                token,
            )
            tipo_documento = "Modulo Tecnico"
        elif doc_id in mapa_modulos:
            detalhes = mapa_modulos[doc_id]
            url = self._montarUrlComToken(f"/modulo?modulo={doc_id}", token)
            tipo_documento = "Modulo"
        else:
            nome_arquivo = os.path.basename(doc_id)
            detalhes = {
                "nome": nome_arquivo.replace("_", " ").replace("-", " ").capitalize(),
                "icon": "fas fa-file-alt",
            }
            url = self._montarUrlComToken(f"/modulo?submodulo={doc_id}", token)
            diretorio_pai = os.path.basename(os.path.dirname(doc_id))
            tipo_documento = diretorio_pai.capitalize() if diretorio_pai else "Submodulo"

        trecho = self._obterTrechoContextual(conteudo, termo_destaque)
        if termo_destaque:
            trecho = self._servico_filtro_conteudo.destacarTermos(trecho, termo_destaque)

        previa = self._normalizarPrevia(ExtrairPreviaMidia(conteudo), token)
        return {
            "module_id": doc_id,
            "module_nome": detalhes.get("nome", "Desconhecido"),
            "module_icon": detalhes.get("icon", "fas fa-question-circle"),
            "doc_type": tipo_documento,
            "url": url,
            "snippet": trecho,
            "preview": previa,
            "access_count": int(contagem_acesso or 0),
        }

    @staticmethod
    def _obterTrechoContextual(conteudo: str, consulta: str, tamanho: int = 200) -> str:
        conteudo_sem_codigo = re.sub(r"```[\s\S]*?```", "", conteudo)
        conteudo_limpo = re.sub(r"<[^>]+>", "", conteudo_sem_codigo)
        if not consulta:
            return (
                conteudo_limpo[:tamanho] + "..."
                if len(conteudo_limpo) > tamanho
                else conteudo_limpo
            )

        correspondencia = re.search(re.escape(consulta), conteudo_limpo, re.IGNORECASE)
        if not correspondencia:
            return (
                conteudo_limpo[:tamanho] + "..."
                if len(conteudo_limpo) > tamanho
                else conteudo_limpo
            )

        inicio = max(0, correspondencia.start() - (tamanho // 2))
        fim = min(len(conteudo_limpo), correspondencia.end() + (tamanho // 2))
        trecho = conteudo_limpo[inicio:fim]
        if inicio > 0:
            trecho = "..." + trecho
        if fim < len(conteudo_limpo):
            trecho += "..."
        return trecho

    @staticmethod
    def _filtrarRestritos(
        itens: list[dict[str, object]],
        pode_ver_restritos: bool,
        mapa_restricoes: dict[str, bool],
        chave_id: str = "module_id",
    ) -> list[dict[str, object]]:
        if pode_ver_restritos:
            return itens
        return [
            item
            for item in itens
            if not DocumentoEhRestrito(item.get(chave_id), mapa_restricoes)
        ]

    @staticmethod
    def _montarUrlComToken(caminho_base: str, token: str) -> str:
        separador = "&" if "?" in caminho_base else "?"
        return (
            f"{caminho_base}{separador}{urlencode({'token': token})}"
            if token
            else caminho_base
        )

    def _montarUrlDocumento(self, doc_id: str, token: str) -> str:
        if "/" in doc_id and not doc_id.endswith("/"):
            return self._montarUrlComToken(f"/modulo?submodulo={doc_id}", token)
        return self._montarUrlComToken(f"/modulo?modulo={doc_id}", token)

    def _normalizarPrevia(
        self, previa: dict[str, object] | None, token: str
    ) -> dict[str, object] | None:
        if not previa:
            return previa
        if previa.get("is_absolute"):
            return previa

        endpoint = (
            "Inicio.servirImagemDinamica"
            if previa.get("type") == "image"
            else "Inicio.servirVideo"
        )
        return {
            **previa,
            "path": url_for(endpoint, nome_arquivo=previa["path"], token=token),
            "is_absolute": True,
        }

    @staticmethod
    def _normalizarUrlRelativa(url: str) -> str:
        if url.startswith("http://") or url.startswith("https://"):
            return url
        base_prefix = (current_app.config.get("BASE_PREFIX") or "").rstrip("/")
        if base_prefix and url.startswith(base_prefix):
            url = url[len(base_prefix) :]
        return url if url.startswith("/") else f"/{url}"
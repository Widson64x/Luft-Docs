from __future__ import annotations

import os
import re

import google.generativeai as genai

from Services.PermissaoService import ChavesPermissao

from .ConfiguracaoLLM import ConfiguracaoLLM


class ServicoContextoLIA:
    """Centraliza a descoberta e a filtragem do contexto usado pela LIA."""

    CAMINHOS_RESTRITOS = ["data/global/EDIs", "data/global/Integradores"]
    ARQUIVO_RESTRITO = "technical_documentation.md"

    def transformarConsulta(self, pergunta_usuario: str) -> list[str]:
        """Expande perguntas gerais para melhorar a busca vetorial."""
        print(
            f"Transformando a pergunta original para busca geral: '{pergunta_usuario}'"
        )
        prompt_expansao = f"""Sua tarefa e agir como um especialista em reformulacao de perguntas para um sistema de busca interno.
Dada a pergunta de um usuario, gere 3 variacoes que mantenham a intencao original, mas use sinonimos e diferentes estruturas de frase.
Isso ajudara o sistema de busca a encontrar documentos mais relevantes.

PERGUNTA ORIGINAL: \"{pergunta_usuario}\"

Retorne apenas as 3 variacoes, uma por linha. Nao adicione cabecalhos ou texto extra.
"""

        try:
            modelo_gemini = ConfiguracaoLLM.obterCliente("gemini_model")
            if not modelo_gemini:
                raise ConnectionError(
                    "Modelo Gemini nao esta disponivel para transformacao da query."
                )

            resposta = modelo_gemini.generate_content(prompt_expansao)
            variacoes = [linha.strip() for linha in resposta.text.strip().split("\n") if linha.strip()]
            if not variacoes:
                print(
                    "AVISO: Transformacao da query nao retornou variacoes. Usando apenas a original."
                )
                return [pergunta_usuario]

            print(f"Variacoes geradas: {variacoes}")
            return [pergunta_usuario] + variacoes
        except Exception as erro:
            print(f"ERRO ao transformar a query: {erro}. Usando apenas a pergunta original.")
            return [pergunta_usuario]

    def encontrarContextoParaPergunta(
        self,
        pergunta_usuario: str,
        modulos_disponiveis: list[str],
        permissoes_usuario: dict[str, bool],
    ) -> tuple[list[str], list[dict[str, object]], bool]:
        """Orquestra a busca vetorial e a filtragem por permissao da LIA."""
        if not ConfiguracaoLLM.componentesDisponiveis():
            raise ConnectionError(
                "Componentes da IA (DB vetorial ou embedding) nao estao disponiveis."
            )

        colecao = ConfiguracaoLLM.obterCliente("db_collection")
        modelo_embedding = ConfiguracaoLLM.obterCliente("embedding_model")

        pergunta_limpa, filtro_consulta = self._construirFiltroConsulta(
            pergunta_usuario,
            modulos_disponiveis,
        )
        if filtro_consulta:
            print("Busca focada com '@' detectada. Pulando a etapa de transformacao da pergunta.")
            consultas_embedding = [pergunta_limpa]
        else:
            consultas_embedding = self.transformarConsulta(pergunta_limpa)

        print(f"Gerando embeddings para: {consultas_embedding}")
        embeddings = genai.embed_content(
            model=modelo_embedding,
            content=consultas_embedding,
            task_type="RETRIEVAL_QUERY",
        )["embedding"]

        resultados_relevantes = colecao.query(
            query_embeddings=embeddings,
            n_results=10,
            where=filtro_consulta if filtro_consulta else None,
            include=["metadatas", "documents"],
        )

        if not resultados_relevantes["documents"][0] and filtro_consulta:
            print(
                f"Busca filtrada por {filtro_consulta} nao retornou resultados. Tentando busca geral como fallback."
            )
            resultados_relevantes = colecao.query(
                query_embeddings=embeddings,
                n_results=10,
                include=["metadatas", "documents"],
            )

        documentos_iniciais = resultados_relevantes["documents"][0]
        metadados_iniciais = resultados_relevantes["metadatas"][0]

        documentos_finais, metadados_finais = self._filtrarContextoPorPermissao(
            documentos_iniciais,
            metadados_iniciais,
            permissoes_usuario.get(ChavesPermissao.VISUALIZAR_MODULOS_TECNICOS, False),
        )
        foi_bloqueado_por_permissao = bool(
            documentos_iniciais
            and not documentos_finais
            and not permissoes_usuario.get(
                ChavesPermissao.VISUALIZAR_MODULOS_TECNICOS,
                False,
            )
        )
        return documentos_finais, metadados_finais, foi_bloqueado_por_permissao

    def _construirFiltroConsulta(
        self,
        pergunta_usuario: str,
        modulos_disponiveis: list[str],
    ) -> tuple[str, dict[str, object]]:
        pergunta_limpa = pergunta_usuario
        filtro_consulta: dict[str, object] = {}
        modulos_encontrados: list[str] = []

        padrao_modulo = re.compile(r"@([\w-]+)")
        modulos_mencionados = padrao_modulo.findall(pergunta_usuario)
        if modulos_mencionados:
            print(f"Deteccao explicita com '@' encontrada: {modulos_mencionados}")
            modulos_validos = [
                modulo
                for modulo in modulos_mencionados
                if modulo in modulos_disponiveis
            ]
            if modulos_validos:
                modulos_encontrados = modulos_validos
                pergunta_limpa = padrao_modulo.sub("", pergunta_usuario).strip()
                print(
                    f"Modulos validos encontrados: {modulos_validos}. Pergunta limpa: '{pergunta_limpa}'"
                )

        if not modulos_encontrados:
            print("Nenhuma mencao explicita valida. Tentando deteccao implicita...")
            pergunta_minuscula = pergunta_limpa.lower()
            modulos_encontrados = [
                modulo
                for modulo in modulos_disponiveis
                if modulo.replace("-", " ") in pergunta_minuscula
            ]

        if modulos_encontrados:
            filtro_consulta = (
                {"$or": [{"module": nome} for nome in modulos_encontrados]}
                if len(modulos_encontrados) > 1
                else {"module": modulos_encontrados[0]}
            )
            print(f"Busca FOCADA ativada. Filtro: {filtro_consulta}")
        else:
            print("Nenhum modulo especifico mencionado. Realizando busca GERAL.")

        return pergunta_limpa, filtro_consulta

    def _filtrarContextoPorPermissao(
        self,
        documentos: list[str],
        metadados: list[dict[str, object]],
        pode_ver_tecnico: bool,
    ) -> tuple[list[str], list[dict[str, object]]]:
        if pode_ver_tecnico:
            return documentos, metadados

        print("Verificando permissoes no contexto retornado...")
        documentos_seguros: list[str] = []
        metadados_seguros: list[dict[str, object]] = []
        for documento, metadado in zip(documentos, metadados):
            origem = str(metadado.get("source", ""))
            arquivo_restrito = os.path.basename(origem) == self.ARQUIVO_RESTRITO
            caminho_restrito = any(
                origem.replace("\\", "/").startswith(caminho)
                for caminho in self.CAMINHOS_RESTRITOS
            )
            if arquivo_restrito or caminho_restrito:
                print(
                    f"Filtrando documento restrito para usuario sem permissao: {origem}"
                )
                continue
            documentos_seguros.append(documento)
            metadados_seguros.append(metadado)

        print(
            f"Contexto filtrado. Documentos permitidos: {len(documentos_seguros)} de {len(documentos)}"
        )
        return documentos_seguros, metadados_seguros

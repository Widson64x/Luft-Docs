from __future__ import annotations

import os
import uuid
from typing import Any

from flask import current_app, request, session

from Config import BASE_PREFIX, MODULES_DIR

from .ConfiguracaoLLM import ConfiguracaoLLM
from .GeradorRespostaLIA import GeradorRespostaLIA
from .ServicoContextoLIA import ServicoContextoLIA
from .ServicoFeedbackLIA import ServicoFeedbackLIA


class ServicoLIA:
    """Orquestra o fluxo completo das rotas backend da LIA."""

    def __init__(self) -> None:
        self._servico_contexto = ServicoContextoLIA()
        self._gerador_resposta = GeradorRespostaLIA()
        self._servico_feedback = ServicoFeedbackLIA()
        self._modulos_disponiveis = self._descobrirModulosDisponiveis()

    def obterRespostaListaModulos(self) -> dict[str, Any]:
        """Retorna a lista de modulos disponiveis para o frontend da LIA."""
        if not self._modulos_disponiveis:
            return self._respostaJson({"error": "Nenhum modulo disponivel."}, 404)
        return self._respostaJson({"modules": self._modulos_disponiveis}, 200)

    def obterRespostaPergunta(self, dados_requisicao: dict[str, Any] | None) -> dict[str, Any]:
        """Processa a pergunta do usuario e gera a resposta final da LIA."""
        if not ConfiguracaoLLM.componentesDisponiveis():
            return self._respostaJson(
                {"error": "Componentes da IA nao estao configurados."},
                500,
            )

        dados_requisicao = dados_requisicao or {}
        pergunta_original = dados_requisicao.get("user_question")
        if not pergunta_original:
            return self._respostaJson({"error": "Requisicao invalida."}, 400)

        modelo_selecionado = dados_requisicao.get("selected_model", "groq-70b")
        identificador_resposta = str(uuid.uuid4())
        identificador_usuario = session.get("user_name", "anonymous")
        permissoes_usuario = session.get("permissions", {})
        busca_focada = "@" in pergunta_original

        try:
            documentos_iniciais, metadados_iniciais, bloqueado_por_permissao = (
                self._servico_contexto.encontrarContextoParaPergunta(
                    pergunta_usuario=pergunta_original,
                    modulos_disponiveis=self._modulos_disponiveis,
                    permissoes_usuario=permissoes_usuario,
                )
            )

            if bloqueado_por_permissao:
                return self._respostaJson(
                    {
                        "answer": "Nao encontrei informacoes sobre este topico nos documentos aos quais voce tem acesso. Tente perguntar de outra forma ou sobre outro assunto.",
                        "context_files": [],
                        "response_id": identificador_resposta,
                        "user_id": identificador_usuario,
                        "original_user_question": pergunta_original,
                        "model_used": modelo_selecionado,
                        "context_sources_list": [],
                    },
                    200,
                )

            if not documentos_iniciais:
                return self._respostaJson(
                    {
                        "answer": "Opa! Nao encontrei nada sobre isso nos documentos. Pode tentar perguntar de outra forma?",
                        "context_files": [],
                        "response_id": identificador_resposta,
                        "user_id": identificador_usuario,
                        "original_user_question": pergunta_original,
                        "model_used": modelo_selecionado,
                        "context_sources_list": [],
                    },
                    200,
                )

            if busca_focada:
                print(
                    "Busca focada com '@' detectada. Pulando a etapa de re-ranking para maior velocidade."
                )
                contexto_final = "\n---\n".join(documentos_iniciais[:4])
                fontes_finais = sorted(
                    list(
                        {
                            str(metadado["source"])
                            for metadado in metadados_iniciais[:4]
                            if "source" in metadado
                        }
                    )
                )
            else:
                contexto_final, fontes_finais = (
                    self._gerador_resposta.reranquearEFiltrarContexto(
                        pergunta=pergunta_original,
                        documentos=documentos_iniciais,
                        metadados=metadados_iniciais,
                    )
                )

            if not contexto_final.strip():
                return self._respostaJson(
                    {
                        "answer": "Encontrei alguns documentos, mas nenhum parecia responder diretamente a sua pergunta. Poderia tentar ser mais especifico?",
                        "context_files": [],
                        "response_id": identificador_resposta,
                        "user_id": identificador_usuario,
                        "original_user_question": pergunta_original,
                        "model_used": modelo_selecionado,
                        "context_sources_list": [],
                    },
                    200,
                )

            resposta_final = self._gerador_resposta.gerarRespostaLlm(
                nome_modelo=modelo_selecionado,
                contexto=contexto_final,
                pergunta=pergunta_original,
            )
            token_atual = request.args.get("token") or session.get("token", "")
            fontes_estruturadas = [
                {
                    "name": fonte,
                    "url": self._transformarCaminhoEmUrl(fonte, token_atual),
                }
                for fonte in fontes_finais
            ]

            return self._respostaJson(
                {
                    "answer": resposta_final,
                    "context_files": fontes_finais,
                    "response_id": identificador_resposta,
                    "user_id": identificador_usuario,
                    "original_user_question": pergunta_original,
                    "model_used": modelo_selecionado,
                    "context_sources_objects": fontes_estruturadas,
                },
                200,
            )
        except Exception as erro:
            current_app.logger.error("ERRO CRITICO na API da LIA: %s", erro, exc_info=True)
            return self._respostaJson(
                {"error": f"Ocorreu um erro inesperado: {str(erro)}"},
                500,
            )

    def obterRespostaRegistroFeedback(
        self, dados_requisicao: dict[str, Any] | None
    ) -> dict[str, Any]:
        """Registra o feedback enviado pelo frontend da LIA."""
        dados_requisicao = dados_requisicao or {}
        identificador_resposta = dados_requisicao.get("response_id")
        identificador_usuario = session.get("user_name", "anonymous")
        avaliacao = dados_requisicao.get("rating")

        if not all([identificador_resposta, identificador_usuario, avaliacao is not None]):
            return self._respostaJson(
                {"error": "Dados de feedback invalidos."},
                400,
            )

        try:
            self._servico_feedback.salvarFeedback(
                identificador_resposta=identificador_resposta,
                identificador_usuario=identificador_usuario,
                avaliacao=avaliacao,
                comentario=dados_requisicao.get("comment"),
                pergunta_usuario=dados_requisicao.get("user_question"),
                modelo_utilizado=dados_requisicao.get("model_used"),
                fontes_contexto=dados_requisicao.get("context_sources"),
            )
            return self._respostaJson(
                {"message": "Feedback registrado com sucesso!"},
                200,
            )
        except Exception:
            return self._respostaJson(
                {"error": "Erro interno ao registrar feedback."},
                500,
            )

    def _descobrirModulosDisponiveis(self) -> list[str]:
        try:
            caminho_modulos = str(MODULES_DIR)
            if not os.path.exists(caminho_modulos):
                print("AVISO: Diretorio de modulos nao encontrado.")
                return []

            modulos = sorted(
                [
                    item
                    for item in os.listdir(caminho_modulos)
                    if os.path.isdir(os.path.join(caminho_modulos, item))
                ]
            )
            print(f"Modulos descobertos automaticamente: {modulos}")
            return modulos
        except Exception as erro:
            print(f"ERRO CRITICO ao descobrir modulos: {erro}")
            return []

    def _transformarCaminhoEmUrl(self, caminho_arquivo: str, token: str) -> str:
        if not caminho_arquivo:
            return "#"

        caminho_limpo = caminho_arquivo.replace("\\", "/")
        if "/modules/" in caminho_limpo:
            try:
                partes = caminho_limpo.split("/modules/")
                if len(partes) > 1:
                    sub_partes = partes[1].split("/")
                    nome_modulo = sub_partes[0]
                    return f"{BASE_PREFIX}/modulo/?modulo={nome_modulo}&token={token}"
            except Exception as erro:
                print(f"Erro ao gerar link de modulo: {erro}")

        if caminho_limpo.endswith(".md"):
            try:
                nome_arquivo = os.path.basename(caminho_limpo)
                nome_sem_extensao = os.path.splitext(nome_arquivo)[0]
                return f"{BASE_PREFIX}/submodulo/?nome={nome_sem_extensao}&token={token}"
            except Exception as erro:
                print(f"Erro ao gerar link de submodulo: {erro}")

        return "#"

    @staticmethod
    def _respostaJson(dados: dict[str, Any], codigo: int) -> dict[str, Any]:
        return {"tipo": "json", "dados": dados, "codigo": codigo}

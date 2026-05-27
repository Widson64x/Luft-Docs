from __future__ import annotations

import os

from flask import current_app, request

from Config import DOCS_DOWNLOAD_DIR


class ServicoDownload:
    """Centraliza a validacao de downloads de arquivos da aplicacao."""

    def obterRespostaDownload(self) -> dict[str, object]:
        """Valida a solicitacao e retorna os dados necessarios para envio do arquivo."""
        nome_arquivo = request.args.get("download", "").strip()
        if not nome_arquivo:
            return {
                "tipo": "erro",
                "codigo": 400,
                "mensagem": "Parametro 'download' vazio",
            }

        if ".." in nome_arquivo or nome_arquivo.startswith(("/", "\\")):
            return {
                "tipo": "erro",
                "codigo": 400,
                "mensagem": "Nome de arquivo invalido",
            }

        pasta_download = DOCS_DOWNLOAD_DIR
        if not os.path.isdir(pasta_download):
            current_app.logger.error(
                "Pasta de downloads nao existe: %s", pasta_download
            )
            return {
                "tipo": "erro",
                "codigo": 500,
                "mensagem": "Erro de configuracao do servidor",
            }

        caminho_arquivo = os.path.join(pasta_download, nome_arquivo)
        if not os.path.isfile(caminho_arquivo):
            current_app.logger.warning("Arquivo nao encontrado: %s", caminho_arquivo)
            return {"tipo": "erro", "codigo": 404, "mensagem": "Arquivo nao encontrado"}

        return {
            "tipo": "download",
            "pasta": pasta_download,
            "nome_arquivo": nome_arquivo,
        }
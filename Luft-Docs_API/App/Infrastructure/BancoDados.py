"""Gerenciamento de engine e sessoes SQLAlchemy da aplicacao."""

import logging
from typing import Optional

from sqlalchemy import create_engine
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import NullPool

from App.Config.ConfiguracoesApi import ConfiguracoesApi, carregarConfiguracoesApi
from App.Shared.ExcecoesAplicacao import InfraestruturaAplicacaoErro


logger = logging.getLogger(__name__)


class GerenciadorBancoDados:
    """Controla a inicializacao e o ciclo de vida das sessoes do banco."""

    def __init__(self, configuracoes: ConfiguracoesApi):
        """Inicializa o gerenciador com as configuracoes de banco da aplicacao.

        Args:
            configuracoes: Configuracoes centralizadas da aplicacao.
        """
        self.configuracoes = configuracoes
        self.engine = None
        self.fabricaSessoes = None
        self.extensaoBanco = None

    def _garantirInfraestrutura(self) -> None:
        """Inicializa engine e fabrica de sessoes sob demanda."""
        if self.extensaoBanco is not None or self.fabricaSessoes is not None:
            return

        try:
            descricaoBanco = self.configuracoes.obterDescricaoBancoDados()
            self.extensaoBanco = self.configuracoes.obterExtensaoBancoDados()
            if self.extensaoBanco is not None:
                self.engine = self.extensaoBanco.obter_engine()
                self.engine.echo = self.configuracoes.exibirLogsBanco
                logger.info(
                    "Conectando ao banco de dados %s no host %s:%s com o usuario %s via LuftCore.",
                    descricaoBanco["nome_banco"],
                    descricaoBanco["host"],
                    descricaoBanco["porta"] or "N/D",
                    descricaoBanco["usuario"],
                )
                logger.info("Engine SQLAlchemy configurada com sucesso.")
                return

            urlBancoDados = self.configuracoes.obterUrlBancoDados()
            logger.info(
                "Conectando ao banco de dados %s no host %s:%s com o usuario %s.",
                descricaoBanco["nome_banco"],
                descricaoBanco["host"],
                descricaoBanco["porta"] or "N/D",
                descricaoBanco["usuario"],
            )
            self.engine = create_engine(urlBancoDados, poolclass=NullPool)
            self.engine.echo = self.configuracoes.exibirLogsBanco
            self.fabricaSessoes = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine,
            )
            logger.info("Engine SQLAlchemy configurada com sucesso.")
        except Exception as erro:
            raise InfraestruturaAplicacaoErro("Nao foi possivel inicializar a infraestrutura de banco de dados.") from erro

    def criarSessao(self) -> Session:
        """Cria uma nova sessao SQLAlchemy para a requisicao atual.

        Returns:
            Session: Sessao pronta para uso na operacao atual.
        """
        self._garantirInfraestrutura()
        try:
            if self.extensaoBanco is not None:
                sessaoBanco = self.extensaoBanco.obter_sessao_simples()
                logger.debug("Sessao do banco de dados aberta via LuftCore.")
                return sessaoBanco

            sessaoBanco = self.fabricaSessoes()
            logger.debug("Sessao do banco de dados aberta.")
            return sessaoBanco
        except SQLAlchemyError as erro:
            raise InfraestruturaAplicacaoErro("Erro ao abrir uma sessao com o banco de dados.") from erro

    def finalizarSessao(self, sessaoBanco: Optional[Session], houveErro: bool = False) -> None:
        """Finaliza a sessao SQLAlchemy e aplica rollback quando necessario.

        Args:
            sessaoBanco: Sessao ativa que deve ser finalizada.
            houveErro: Flag indicando se a operacao terminou com erro.

        Returns:
            None: Sessao encerrada e recursos liberados.
        """
        if sessaoBanco is None:
            return

        try:
            if houveErro:
                sessaoBanco.rollback()
        finally:
            sessaoBanco.close()
            logger.debug("Sessao do banco de dados fechada.")


gerenciadorBancoDados = GerenciadorBancoDados(carregarConfiguracoesApi())
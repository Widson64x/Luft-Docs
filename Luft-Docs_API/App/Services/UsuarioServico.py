"""Servicos de aplicacao relacionados a autenticacao e consulta de usuarios."""

from datetime import datetime
import logging
from typing import Any, Dict, Optional, Tuple

from sqlalchemy.orm import Session

from App.Config.ConfiguracoesApi import ConfiguracoesApi
from App.Repositories.UsuarioRepositorio import UsuarioFalsoRepositorio, UsuarioRepositorio
from App.Services.AutenticacaoServico import AutenticacaoServico
from App.Shared.ExcecoesAplicacao import InfraestruturaAplicacaoErro, RecursoNaoEncontradoErro
from App.Utils.HashLoginUtil import ResolvedorHashLogin


logger = logging.getLogger(__name__)


class UsuarioServico:
    """Coordena os casos de uso de usuario e token da API."""

    def __init__(
        self,
        configuracoes: ConfiguracoesApi,
        repositorioUsuario: UsuarioRepositorio,
        repositorioUsuarioFalso: UsuarioFalsoRepositorio,
        autenticacaoServico: AutenticacaoServico,
        resolvedorHashLogin: ResolvedorHashLogin,
    ):
        """Inicializa as dependencias do fluxo de usuarios.

        Args:
            configuracoes: Configuracoes centralizadas da aplicacao.
            repositorioUsuario: Repositorio de acesso ao banco de dados.
            repositorioUsuarioFalso: Repositorio de dados simulados.
            autenticacaoServico: Servico de emissao e validacao de JWT.
            resolvedorHashLogin: Componente responsavel por resolver o hash MD5 do login.
        """
        self.configuracoes = configuracoes
        self.repositorioUsuario = repositorioUsuario
        self.repositorioUsuarioFalso = repositorioUsuarioFalso
        self.autenticacaoServico = autenticacaoServico
        self.resolvedorHashLogin = resolvedorHashLogin

    def autenticarUsuarioPorHashLogin(
        self,
        sessaoBanco: Optional[Session],
        hashLogin: str,
    ) -> Dict[str, Any]:
        """Resolve o hash informado, busca o usuario e emite um token JWT.

        Args:
            sessaoBanco: Sessao SQLAlchemy opcional para acesso ao banco.
            hashLogin: Hash MD5 do login do usuario.

        Returns:
            Dict[str, Any]: Estrutura de resposta da autenticacao do usuario.
        """
        if self.configuracoes.modoApiFalso:
            registroUsuario = self.repositorioUsuarioFalso.buscarRegistroPorHashLogin(hashLogin)
            if registroUsuario is None:
                raise RecursoNaoEncontradoErro("Usuario nao encontrado (hash invalido).")

            tokenAcesso, instanteExpiracao = self.autenticacaoServico.gerarTokenAcesso(
                registroUsuario["usuario"]["Login_Usuario"]
            )
            return self._montarRespostaAutenticacao(
                registroUsuario["usuario"],
                registroUsuario["grupo"],
                tokenAcesso,
                instanteExpiracao,
            )

        if sessaoBanco is None:
            raise InfraestruturaAplicacaoErro("Sessao de banco nao disponivel para a operacao solicitada.")

        loginUsuario = self.resolvedorHashLogin.obterLoginPorHash(sessaoBanco, hashLogin)
        if loginUsuario is None:
            raise RecursoNaoEncontradoErro("Usuario nao encontrado (hash invalido).")

        dadosUsuario, dadosGrupo = self._obterDadosUsuarioEGrupoPorLogin(sessaoBanco, loginUsuario)
        tokenAcesso, instanteExpiracao = self.autenticacaoServico.gerarTokenAcesso(loginUsuario)
        return self._montarRespostaAutenticacao(dadosUsuario, dadosGrupo, tokenAcesso, instanteExpiracao)

    def validarTokenAcesso(
        self,
        sessaoBanco: Optional[Session],
        tokenAcesso: str,
    ) -> Dict[str, Any]:
        """Valida um token JWT e reconstrui a resposta padrao do usuario.

        Args:
            sessaoBanco: Sessao SQLAlchemy opcional para acesso ao banco.
            tokenAcesso: Token JWT previamente emitido pela API.

        Returns:
            Dict[str, Any]: Estrutura de resposta contendo usuario, grupo e token.
        """
        loginUsuario, instanteExpiracao = self.autenticacaoServico.decodificarToken(tokenAcesso)

        if self.configuracoes.modoApiFalso:
            registroUsuario = self.repositorioUsuarioFalso.buscarRegistroPorLogin(loginUsuario)
            if registroUsuario is None:
                raise RecursoNaoEncontradoErro("Usuario do token nao encontrado no modo falso.")

            return self._montarRespostaAutenticacao(
                registroUsuario["usuario"],
                registroUsuario["grupo"],
                tokenAcesso,
                instanteExpiracao,
            )

        if sessaoBanco is None:
            raise InfraestruturaAplicacaoErro("Sessao de banco nao disponivel para a operacao solicitada.")

        dadosUsuario, dadosGrupo = self._obterDadosUsuarioEGrupoPorLogin(sessaoBanco, loginUsuario)
        return self._montarRespostaAutenticacao(dadosUsuario, dadosGrupo, tokenAcesso, instanteExpiracao)

    def _obterDadosUsuarioEGrupoPorLogin(
        self,
        sessaoBanco: Session,
        loginUsuario: str,
    ) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """Recupera os dados externos de usuario e grupo a partir do login.

        Args:
            sessaoBanco: Sessao SQLAlchemy ativa.
            loginUsuario: Login do usuario que deve ser localizado.

        Returns:
            Tuple[Dict[str, Any], Dict[str, Any]]: Dados serializados de usuario e grupo.
        """
        usuarioEncontrado = self.repositorioUsuario.buscarUsuarioPorLogin(sessaoBanco, loginUsuario)
        if usuarioEncontrado is None:
            raise RecursoNaoEncontradoErro("Usuario nao encontrado.")

        grupoUsuario = self.repositorioUsuario.buscarGrupoPorCodigo(
            sessaoBanco,
            usuarioEncontrado.codigoUsuarioGrupo,
        )
        if grupoUsuario is None:
            raise RecursoNaoEncontradoErro("Grupo de usuario nao encontrado.")

        logger.info("Usuario '%s' e grupo associados recuperados com sucesso.", loginUsuario)
        return usuarioEncontrado.paraRespostaExterna(), grupoUsuario.paraRespostaExterna()

    def _montarRespostaAutenticacao(
        self,
        dadosUsuario: Dict[str, Any],
        dadosGrupo: Dict[str, Any],
        tokenAcesso: str,
        instanteExpiracao: datetime,
    ) -> Dict[str, Any]:
        """Monta o contrato padrao retornado pelos endpoints de autenticacao.

        Args:
            dadosUsuario: Dados do usuario no formato externo da API.
            dadosGrupo: Dados do grupo no formato externo da API.
            tokenAcesso: Token JWT emitido ou validado.
            instanteExpiracao: Instante de expiracao do token em UTC.

        Returns:
            Dict[str, Any]: Estrutura final de resposta da API.
        """
        return {
            "usuario": dadosUsuario,
            "grupo": dadosGrupo,
            "token": tokenAcesso,
            "token_expira_em": self._formatarInstanteUtc(instanteExpiracao),
        }

    def _formatarInstanteUtc(self, instanteExpiracao: datetime) -> str:
        """Formata um instante UTC no padrao ISO utilizado pela API.

        Args:
            instanteExpiracao: Instante UTC que deve ser serializado.

        Returns:
            str: Texto ISO 8601 terminando em Z.
        """
        return instanteExpiracao.isoformat().replace("+00:00", "Z")
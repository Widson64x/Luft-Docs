"""Servicos relacionados a emissao, validacao e revogacao de tokens."""

from datetime import datetime, timedelta, timezone
import logging
from typing import Set, Tuple

from jose import JWTError, jwt

from App.Config.ConfiguracoesApi import ConfiguracoesApi
from App.Shared.ExcecoesAplicacao import AutenticacaoErro


logger = logging.getLogger(__name__)


class AutenticacaoServico:
    """Orquestra a criacao e a validacao dos tokens JWT da API."""

    def __init__(self, configuracoes: ConfiguracoesApi):
        """Inicializa o servico com as configuracoes de seguranca da API.

        Args:
            configuracoes: Configuracoes centralizadas da aplicacao.
        """
        self.configuracoes = configuracoes
        self.tokensRevogados: Set[str] = set()

    def gerarTokenAcesso(self, loginUsuario: str) -> Tuple[str, datetime]:
        """Gera um token JWT de acesso para o usuario informado.

        Args:
            loginUsuario: Login do usuario autenticado.

        Returns:
            Tuple[str, datetime]: Token gerado e seu instante de expiracao em UTC.
        """
        instanteExpiracao = datetime.now(timezone.utc) + timedelta(hours=self.configuracoes.horasExpiracaoToken)
        payloadToken = {
            self.configuracoes.claimSubjectToken: loginUsuario,
            self.configuracoes.claimExpiracaoToken: int(instanteExpiracao.timestamp()),
        }
        tokenAcesso = jwt.encode(
            payloadToken,
            self.configuracoes.chaveSecreta,
            algorithm=self.configuracoes.algoritmoToken,
            headers=self.configuracoes.obterCabecalhoJwt(),
        )
        logger.info("Token JWT gerado com sucesso para o usuario '%s'.", loginUsuario)
        return tokenAcesso, instanteExpiracao

    def revogarToken(self, tokenAcesso: str) -> None:
        """Adiciona um token a lista de revogacao em memoria.

        Args:
            tokenAcesso: Token JWT que deve ser invalidado.

        Returns:
            None: Operacao concluida sem retorno.
        """
        tokenNormalizado = (tokenAcesso or "").strip()
        if not tokenNormalizado:
            raise AutenticacaoErro("Token nao fornecido.")

        self.tokensRevogados.add(tokenNormalizado)
        logger.info("Token JWT revogado com sucesso.")

    def decodificarToken(self, tokenAcesso: str) -> Tuple[str, datetime]:
        """Decodifica e valida um token JWT ja emitido pela API.

        Args:
            tokenAcesso: Token JWT a ser analisado.

        Returns:
            Tuple[str, datetime]: Login do usuario e instante de expiracao do token.
        """
        tokenNormalizado = (tokenAcesso or "").strip()
        if not tokenNormalizado:
            raise AutenticacaoErro("Token nao fornecido.")
        if tokenNormalizado in self.tokensRevogados:
            raise AutenticacaoErro("Token invalido ou expirado.")

        try:
            payloadToken = jwt.decode(
                tokenNormalizado,
                self.configuracoes.chaveSecreta,
                algorithms=[self.configuracoes.algoritmoToken],
            )
        except JWTError as erro:
            raise AutenticacaoErro("Token invalido ou malformado.") from erro

        loginUsuario = payloadToken.get(self.configuracoes.claimSubjectToken)
        instanteExpiracaoUnix = payloadToken.get(self.configuracoes.claimExpiracaoToken)
        if not loginUsuario or not instanteExpiracaoUnix:
            raise AutenticacaoErro("Estrutura do token invalida.")

        instanteExpiracao = datetime.fromtimestamp(int(instanteExpiracaoUnix), tz=timezone.utc)
        if instanteExpiracao < datetime.now(timezone.utc):
            raise AutenticacaoErro("Token expirado.")

        logger.info("Token JWT validado com sucesso para o usuario '%s'.", loginUsuario)
        return loginUsuario, instanteExpiracao
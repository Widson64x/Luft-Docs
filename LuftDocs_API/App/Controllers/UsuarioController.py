"""Controller responsavel pelos endpoints de usuario e token."""

import logging
from secrets import compare_digest
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Security, status
from fastapi.security import APIKeyHeader
from sqlalchemy.orm import Session

from App.Config.ConfiguracoesApi import carregarConfiguracoesApi
from App.Infrastructure.BancoDados import gerenciadorBancoDados
from App.Repositories.UsuarioRepositorio import UsuarioFalsoRepositorio, UsuarioRepositorio
from App.Schemas.AutenticacaoSchema import RequisicaoRevogacaoToken
from App.Services.AutenticacaoServico import AutenticacaoServico
from App.Services.UsuarioServico import UsuarioServico
from App.Shared.ExcecoesAplicacao import (
    AutenticacaoErro,
    ConfiguracaoAplicacaoErro,
    InfraestruturaAplicacaoErro,
    RecursoNaoEncontradoErro,
)
from App.Utils.HashLoginUtil import ResolvedorHashLogin


logger = logging.getLogger(__name__)

configuracoesApi = carregarConfiguracoesApi()
cabecalhoChaveApi = APIKeyHeader(
    name=configuracoesApi.nomeCabecalhoChaveApi,
    scheme_name="ApiKeyAuth",
    description="Informe a chave de acesso da aplicacao consumidora.",
    auto_error=False,
)
usuarioRepositorio = UsuarioRepositorio()
usuarioFalsoRepositorio = UsuarioFalsoRepositorio()
resolvedorHashLogin = ResolvedorHashLogin(usuarioRepositorio)
autenticacaoServico = AutenticacaoServico(configuracoesApi)
usuarioServico = UsuarioServico(
    configuracoesApi,
    usuarioRepositorio,
    usuarioFalsoRepositorio,
    autenticacaoServico,
    resolvedorHashLogin,
)


def validarChaveAcessoApi(
    chaveAcessoRecebida: Optional[str] = Security(cabecalhoChaveApi),
) -> None:
    """Valida a chave de acesso obrigatoria das rotas protegidas da API.

    Args:
        chaveAcessoRecebida: Valor lido do cabecalho configurado para a API.

    Returns:
        None: Fluxo liberado somente quando a chave recebida for valida.
    """
    chaveInformada = (chaveAcessoRecebida or "").strip()
    if not chaveInformada:
        logger.warning("Requisicao bloqueada por ausencia da chave de acesso da API.")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=(
                f"Cabecalho obrigatorio ausente. Informe a chave da API em "
                f"'{configuracoesApi.nomeCabecalhoChaveApi}'."
            ),
        )

    if not compare_digest(chaveInformada, configuracoesApi.chaveAcessoApi):
        logger.warning("Requisicao bloqueada por chave de acesso invalida.")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Chave de acesso da API invalida.",
        )


roteadorUsuario = APIRouter(
    prefix="/api",
    tags=["Usuario"],
    dependencies=[Depends(validarChaveAcessoApi)],
)


def abrirSessaoBancoSeNecessario() -> Optional[Session]:
    """Abre uma sessao SQLAlchemy apenas quando a API nao esta em modo falso.

    Returns:
        Optional[Session]: Sessao ativa para o banco ou None em modo falso.
    """
    if configuracoesApi.modoApiFalso:
        return None

    return gerenciadorBancoDados.criarSessao()


def fecharSessaoBanco(sessaoBanco: Optional[Session], houveErro: bool) -> None:
    """Finaliza a sessao aberta pelo controller atual.

    Args:
        sessaoBanco: Sessao SQLAlchemy aberta durante a requisicao.
        houveErro: Flag indicando se a operacao terminou com excecao.

    Returns:
        None: Recursos associados a sessao liberados ao final da operacao.
    """
    gerenciadorBancoDados.finalizarSessao(sessaoBanco, houveErro)


@roteadorUsuario.get("/user")
def obterUsuario(
    hashLogin: str = Query(..., alias="login_hash", description="Hash MD5 do login do usuario"),
) -> Dict[str, Any]:
    """Recupera usuario e grupo a partir do hash do login e emite um token JWT.

    Args:
        hashLogin: Hash MD5 do login recebido pela requisicao.

    Returns:
        Dict[str, Any]: Contrato de autenticacao contendo usuario, grupo e token.
    """
    sessaoBanco = None
    houveErro = False

    try:
        logger.info("Recebida requisicao para autenticacao por hash de login.")
        sessaoBanco = abrirSessaoBancoSeNecessario()
        return usuarioServico.autenticarUsuarioPorHashLogin(sessaoBanco, hashLogin)
    except RecursoNaoEncontradoErro as erro:
        houveErro = True
        logger.warning(str(erro))
        raise HTTPException(status_code=404, detail=str(erro)) from erro
    except AutenticacaoErro as erro:
        houveErro = True
        logger.warning(str(erro))
        raise HTTPException(status_code=401, detail=str(erro)) from erro
    except (ConfiguracaoAplicacaoErro, InfraestruturaAplicacaoErro) as erro:
        houveErro = True
        logger.exception("Falha de infraestrutura ao obter usuario.")
        raise HTTPException(status_code=500, detail=str(erro)) from erro
    except Exception as erro:
        houveErro = True
        logger.exception("Erro inesperado ao obter usuario.")
        raise HTTPException(status_code=500, detail="Ocorreu um erro inesperado no servidor.") from erro
    finally:
        fecharSessaoBanco(sessaoBanco, houveErro)


@roteadorUsuario.post("/logout_token")
def revogarToken(requisicaoRevogacao: RequisicaoRevogacaoToken) -> Dict[str, str]:
    """Revoga um token JWT previamente emitido pela API.

    Args:
        requisicaoRevogacao: Corpo contendo o token que deve ser invalidado.

    Returns:
        Dict[str, str]: Mensagem simples confirmando a revogacao do token.
    """
    try:
        autenticacaoServico.revogarToken(requisicaoRevogacao.token)
        return {"msg": "Token revogado com sucesso"}
    except AutenticacaoErro as erro:
        logger.warning(str(erro))
        raise HTTPException(status_code=400, detail=str(erro)) from erro
    except Exception as erro:
        logger.exception("Erro inesperado ao revogar token.")
        raise HTTPException(status_code=500, detail="Ocorreu um erro inesperado no servidor.") from erro


@roteadorUsuario.get("/token")
def validarToken(
    tokenAcesso: str = Query(..., alias="token", description="Token JWT emitido pela API"),
) -> Dict[str, Any]:
    """Valida um token JWT e retorna novamente o contexto do usuario autenticado.

    Args:
        tokenAcesso: Token JWT enviado pelo cliente para validacao.

    Returns:
        Dict[str, Any]: Contrato de autenticacao contendo usuario, grupo e token.
    """
    sessaoBanco = None
    houveErro = False

    try:
        logger.info("Recebida requisicao para validacao de token JWT.")
        sessaoBanco = abrirSessaoBancoSeNecessario()
        return usuarioServico.validarTokenAcesso(sessaoBanco, tokenAcesso)
    except RecursoNaoEncontradoErro as erro:
        houveErro = True
        logger.warning(str(erro))
        raise HTTPException(status_code=404, detail=str(erro)) from erro
    except AutenticacaoErro as erro:
        houveErro = True
        logger.warning(str(erro))
        raise HTTPException(status_code=401, detail=str(erro)) from erro
    except (ConfiguracaoAplicacaoErro, InfraestruturaAplicacaoErro) as erro:
        houveErro = True
        logger.exception("Falha de infraestrutura ao validar token.")
        raise HTTPException(status_code=500, detail=str(erro)) from erro
    except Exception as erro:
        houveErro = True
        logger.exception("Erro inesperado ao validar token.")
        raise HTTPException(status_code=500, detail="Ocorreu um erro inesperado no servidor.") from erro
    finally:
        fecharSessaoBanco(sessaoBanco, houveErro)
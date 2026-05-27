"""Repositorios responsaveis pelo acesso a dados de usuarios e grupos."""

import hashlib
import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from App.Models.UsuarioModel import UsuarioGrupoModel, UsuarioModel
from App.Shared.ExcecoesAplicacao import InfraestruturaAplicacaoErro


logger = logging.getLogger(__name__)


class UsuarioRepositorio:
    """Centraliza consultas de usuarios e grupos persistidos no banco."""

    def buscarUsuarioPorLogin(self, sessaoBanco: Session, loginUsuario: str) -> Optional[UsuarioModel]:
        """Recupera um usuario pelo login informado.

        Args:
            sessaoBanco: Sessao SQLAlchemy ativa.
            loginUsuario: Login unico do usuario a ser pesquisado.

        Returns:
            Optional[UsuarioModel]: Usuario encontrado ou None.
        """
        try:
            return sessaoBanco.query(UsuarioModel).filter_by(loginUsuario=loginUsuario).first()
        except SQLAlchemyError as erro:
            raise InfraestruturaAplicacaoErro("Erro ao consultar o usuario no banco de dados.") from erro

    def buscarGrupoPorCodigo(
        self,
        sessaoBanco: Session,
        codigoUsuarioGrupo: Optional[int],
    ) -> Optional[UsuarioGrupoModel]:
        """Recupera o grupo associado ao codigo informado.

        Args:
            sessaoBanco: Sessao SQLAlchemy ativa.
            codigoUsuarioGrupo: Identificador do grupo do usuario.

        Returns:
            Optional[UsuarioGrupoModel]: Grupo encontrado ou None.
        """
        if codigoUsuarioGrupo is None:
            return None

        try:
            return (
                sessaoBanco.query(UsuarioGrupoModel)
                .filter_by(codigoUsuarioGrupo=codigoUsuarioGrupo)
                .first()
            )
        except SQLAlchemyError as erro:
            raise InfraestruturaAplicacaoErro("Erro ao consultar o grupo do usuario no banco de dados.") from erro

    def listarLoginsUsuarios(self, sessaoBanco: Session) -> List[str]:
        """Lista todos os logins de usuarios ativos para composicao do cache de hash.

        Args:
            sessaoBanco: Sessao SQLAlchemy ativa.

        Returns:
            List[str]: Colecao de logins encontrados no banco.
        """
        try:
            registros = sessaoBanco.query(UsuarioModel.loginUsuario).all()
        except SQLAlchemyError as erro:
            raise InfraestruturaAplicacaoErro("Erro ao listar logins de usuarios no banco de dados.") from erro

        return [loginUsuario for (loginUsuario,) in registros if loginUsuario]


class UsuarioFalsoRepositorio:
    """Fornece acesso aos registros simulados utilizados em modo falso."""

    def __init__(self, caminhoArquivo: Optional[Path] = None):
        """Inicializa o repositorio local de usuarios simulados.

        Args:
            caminhoArquivo: Caminho opcional para o arquivo JSON de usuarios simulados.
        """
        self.caminhoArquivo = caminhoArquivo or Path(__file__).resolve().parents[1] / "Resources" / "UsuariosFalsos.json"
        self.dadosUsuarios: Optional[List[Dict[str, Any]]] = None

    def carregarUsuarios(self) -> List[Dict[str, Any]]:
        """Carrega os usuarios simulados em memoria.

        Returns:
            List[Dict[str, Any]]: Lista de registros simulados.
        """
        if self.dadosUsuarios is not None:
            return self.dadosUsuarios

        try:
            with self.caminhoArquivo.open("r", encoding="utf-8") as arquivoUsuarios:
                self.dadosUsuarios = json.load(arquivoUsuarios)
                logger.info("Arquivo de usuarios simulados carregado com sucesso.")
                return self.dadosUsuarios
        except FileNotFoundError as erro:
            raise InfraestruturaAplicacaoErro("Arquivo de usuarios simulados nao encontrado.") from erro
        except json.JSONDecodeError as erro:
            raise InfraestruturaAplicacaoErro("Arquivo de usuarios simulados possui JSON invalido.") from erro

    def buscarRegistroPorLogin(self, loginUsuario: str) -> Optional[Dict[str, Any]]:
        """Busca um registro simulado a partir do login do usuario.

        Args:
            loginUsuario: Login que deve ser encontrado no arquivo local.

        Returns:
            Optional[Dict[str, Any]]: Registro encontrado ou None.
        """
        return next(
            (
                registro
                for registro in self.carregarUsuarios()
                if registro.get("usuario", {}).get("Login_Usuario") == loginUsuario
            ),
            None,
        )

    def buscarRegistroPorHashLogin(self, hashLogin: str) -> Optional[Dict[str, Any]]:
        """Busca um registro simulado a partir do hash MD5 do login.

        Args:
            hashLogin: Hash MD5 do login do usuario.

        Returns:
            Optional[Dict[str, Any]]: Registro encontrado ou None.
        """
        hashNormalizado = (hashLogin or "").strip().lower()
        if len(hashNormalizado) != 32:
            return None

        for registro in self.carregarUsuarios():
            loginUsuario = registro.get("usuario", {}).get("Login_Usuario", "")
            if not loginUsuario:
                continue

            hashCalculado = hashlib.md5(loginUsuario.encode("utf-8")).hexdigest()
            if hashCalculado == hashNormalizado:
                return registro

        return None
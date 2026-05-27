"""Utilitarios relacionados a resolucao de hashes de login."""

import hashlib
import logging
import time
from typing import Dict, Optional

from sqlalchemy.orm import Session

from App.Repositories.UsuarioRepositorio import UsuarioRepositorio


logger = logging.getLogger(__name__)


class ResolvedorHashLogin:
    """Mantem um cache temporario para resolver hashes MD5 de login."""

    def __init__(self, repositorioUsuario: UsuarioRepositorio, ttlSegundos: int = 300):
        """Inicializa o componente de resolucao de hash de login.

        Args:
            repositorioUsuario: Repositorio utilizado para listar logins existentes.
            ttlSegundos: Tempo de vida do cache em segundos.
        """
        self.repositorioUsuario = repositorioUsuario
        self.ttlSegundos = ttlSegundos
        self.instanteExpiracaoCache = 0.0
        self.mapaHashesLogins: Dict[str, str] = {}

    def reconstruirCache(self, sessaoBanco: Session) -> None:
        """Reconstrui o cache em memoria a partir dos logins persistidos.

        Args:
            sessaoBanco: Sessao SQLAlchemy ativa para consulta ao banco.

        Returns:
            None: Cache renovado em memoria.
        """
        logger.info("Reconstruindo cache de hashes de login.")
        loginsUsuarios = self.repositorioUsuario.listarLoginsUsuarios(sessaoBanco)
        self.mapaHashesLogins = {
            hashlib.md5(loginUsuario.encode("utf-8")).hexdigest(): loginUsuario
            for loginUsuario in loginsUsuarios
        }
        self.instanteExpiracaoCache = time.time() + self.ttlSegundos
        logger.info("Cache de hash reconstruido com %d logins.", len(self.mapaHashesLogins))

    def garantirCacheValido(self, sessaoBanco: Session) -> None:
        """Assegura que o cache em memoria ainda esteja dentro do TTL.

        Args:
            sessaoBanco: Sessao SQLAlchemy ativa para eventual recarga do cache.

        Returns:
            None: Cache valido para uso apos a chamada.
        """
        if time.time() >= self.instanteExpiracaoCache:
            self.reconstruirCache(sessaoBanco)

    def obterLoginPorHash(self, sessaoBanco: Session, hashLogin: str) -> Optional[str]:
        """Obtém o login correspondente a um hash MD5 informado.

        Args:
            sessaoBanco: Sessao SQLAlchemy ativa para eventual consulta ao banco.
            hashLogin: Hash MD5 do login do usuario.

        Returns:
            Optional[str]: Login encontrado ou None quando o hash e invalido.
        """
        hashNormalizado = (hashLogin or "").strip().lower()
        if len(hashNormalizado) != 32:
            logger.warning("Hash MD5 invalido recebido: '%s'.", hashLogin)
            return None

        self.garantirCacheValido(sessaoBanco)
        loginUsuario = self.mapaHashesLogins.get(hashNormalizado)
        if loginUsuario is not None:
            logger.info("Hash resolvido via cache para o usuario '%s'.", loginUsuario)
            return loginUsuario

        self.reconstruirCache(sessaoBanco)
        return self.mapaHashesLogins.get(hashNormalizado)

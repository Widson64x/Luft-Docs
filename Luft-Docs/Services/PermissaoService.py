"""
Serviço central de autorização do LuftDocs.

Lógica:
  1. Cada permissão vive na tabela Tb_Permissao (SISTEMA_ID=5).
  2. Acesso pode ser concedido por grupo (Tb_PermissaoGrupo) ou por usuário
     individual com override (Tb_PermissaoUsuario.Conceder True/False).
  3. O usuário autenticado vive na sessão Flask (chave `user_id`, `user_group`).
  4. A rota de administração usa o blueprint Routes/Permissoes.py.
  5. Suporte a Bearer token no header Authorization para chamadas de API.
"""
from __future__ import annotations

import json
import logging
import re
import unicodedata
from functools import wraps
from typing import Any

from flask import g, has_request_context, redirect, render_template, request, session, url_for
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError, OperationalError
from luftcore.extensions.flask_extension import api_error, render_no_permission

import Config as cfg
from Db.Connections import obterEngineSqlServer, obterSessaoSqlServer
from Models import Tb_LogAcesso, Tb_Permissao, Tb_PermissaoGrupo, Tb_PermissaoUsuario

_logger = logging.getLogger(__name__)

SISTEMA_ID: int = cfg.SISTEMA_ID
_SQL_IDENTIFIER_RE = re.compile(r"^[A-Za-z0-9_]+$")


def _debug_permissoes_ativo() -> bool:
    ativo = bool(getattr(cfg, "DEBUG_PERMISSIONS", False))
    if ativo:
        #print("[DEBUG PERMISSAO] AVISO: DEBUG_PERMISSIONS está ATIVO (True). Bypass total habilitado.")
        pass
    return ativo


class ChavesPermissao:
    """Catálogo central das chaves de permissão usadas pela aplicação."""

    VISUALIZAR_SISTEMA = "SISTEMA.VISUALIZAR"
    # Permissões de segurança (administração de permissões, acesso a logs, etc.)
    VISUALIZAR_SEGURANCA = "SISTEMA.SEGURANCA.VISUALIZAR"
    EDITAR_SEGURANCA = "SISTEMA.SEGURANCA.EDITAR"
    CRIAR_SEGURANCA = "SISTEMA.SEGURANCA.CRIAR"
    # Permissões de visualização geral (acesso a telas, módulos, etc.)
    VISUALIZAR_MODULOS = "DOCS.MODULOS.VISUALIZAR"
    VISUALIZAR_MODULOS_TECNICOS = "DOCS.MODULOS_TECNICOS.VISUALIZAR"
    VISUALIZAR_MODULOS_RESTRITOS = "DOCS.MODULOS_RESTRITOS.VISUALIZAR"
    # Permissão para acessar ferramentas de desenvolvimento (ex: editor de módulos, logs, etc.)
    VISUALIZAR_FERRAMENTAS_DESENVOLVIMENTO = "DOCS.FERRAMENTAS_DESENVOLVIMENTO.VISUALIZAR"
    # Assistente virtual LIA
    VISUALIZAR_LIA = "DOCS.LIA.VISUALIZAR"
    # Permissões de editor de módulos
    VISUALIZAR_EDITOR = "DOCS.EDITOR_MODULOS.VISUALIZAR"
    CRIAR_MODULOS = "DOCS.EDITOR_MODULOS.CRIAR"
    EDITAR_MODULOS = "DOCS.EDITOR_MODULOS.EDITAR"
    EXCLUIR_MODULOS = "DOCS.EDITOR_MODULOS.EXCLUIR"
    APROVAR_MODULOS = "DOCS.EDITOR_MODULOS.APROVAR"
    REJEITAR_MODULOS = "DOCS.EDITOR_MODULOS.APROVAR"
    VERSIONAR_MODULOS = "DOCS.EDITOR_MODULOS.SINCRONIZAR"
    # Roteiros
    CRIAR_ROTEIROS = "DOCS.ROTEIROS.CRIAR"
    EDITAR_ROTEIROS = "DOCS.ROTEIROS.EDITAR"

    CACHE_SESSAO = (
        VISUALIZAR_SISTEMA,
        VISUALIZAR_MODULOS,
        VISUALIZAR_MODULOS_TECNICOS,
        VISUALIZAR_MODULOS_RESTRITOS,
        VISUALIZAR_FERRAMENTAS_DESENVOLVIMENTO,
        VISUALIZAR_LIA,
        VISUALIZAR_SEGURANCA,
        EDITAR_SEGURANCA,
        CRIAR_SEGURANCA,
        VISUALIZAR_EDITOR,
        CRIAR_MODULOS,
        EDITAR_MODULOS,
        EXCLUIR_MODULOS,
        APROVAR_MODULOS,
        REJEITAR_MODULOS,
        VERSIONAR_MODULOS,
        CRIAR_ROTEIROS,
        EDITAR_ROTEIROS,
    )

# ---------------------------------------------------------------------------
# Utilitários internos
# ---------------------------------------------------------------------------

def _normalizar(texto: str) -> str:
    """Remove acentos e normaliza maiúsculas para comparação de chaves."""
    if not texto:
        return ""
    return "".join(
        c for c in unicodedata.normalize("NFD", texto.upper().strip())
        if unicodedata.category(c) != "Mn"
    )


def _usuario_da_sessao() -> tuple[int | None, int | None]:
    """Retorna (id_usuario, id_grupo) a partir da sessão atual."""
    id_usuario = session.get("user_id")
    id_grupo = session.get("user_group", {}).get("group_code")
    #print(f"[DEBUG PERMISSAO] Sessão -> user_id: {id_usuario}, user_group: {id_grupo}")
    return id_usuario, id_grupo


def _ip_da_requisicao() -> str:
    x_forwarded_for = request.headers.get('X-Forwarded-For')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.headers.get('X-Real-IP', request.remote_addr)

def _eh_requisicao_api() -> bool:
    return (
        request.is_json
        or request.headers.get("X-Requested-With") == "XMLHttpRequest"
        or request.headers.get("Accept", "").startswith("application/json")
    )


def _normalizar_permissoes_em_cache(permissoes: dict[str, bool] | None) -> dict[str, bool]:
    if not permissoes:
        return {}
    return {
        _normalizar(chave): bool(valor)
        for chave, valor in permissoes.items()
    }


def _obter_banco_diretorio_sqlserver() -> str:
    nome_banco = (getattr(cfg, "SQLSERVER_DIRECTORY_DB", "") or "").strip()
    if _SQL_IDENTIFIER_RE.fullmatch(nome_banco):
        return nome_banco
    return "LuftInforma"


def _obterSessaoSqlServerObrigatoria():
    sessao = obterSessaoSqlServer()
    if sessao is None:
        raise RuntimeError("SQL Server nao configurado para esta operacao.")
    return sessao


def _consultar_diretorio_sqlserver(
    consulta: str,
    parametros: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    if not cfg.SQLSERVER_URL:
        #print("[DEBUG PERMISSAO] _consultar_diretorio_sqlserver: Sem SQLSERVER_URL.")
        return []

    engine = obterEngineSqlServer()
    if engine is None:
        #print("[DEBUG PERMISSAO] _consultar_diretorio_sqlserver: engine == None.")
        return []

    banco_diretorio = _obter_banco_diretorio_sqlserver()
    consulta_renderizada = consulta.format(directory_db=f"[{banco_diretorio}]")

    try:
        with engine.connect() as conexao:
            resultado = conexao.execute(text(consulta_renderizada), parametros or {})
            return [dict(linha) for linha in resultado.mappings().all()]
    except Exception as exc:
        #print(f"[DEBUG PERMISSAO] Erro ao consultar diretorio sql server: {exc}")
        pass
    return []


# ---------------------------------------------------------------------------
# Classe principal
# ---------------------------------------------------------------------------

class PermissaoService:

    # --- verificação ---

    @staticmethod
    def verificarPermissao(
        chave: str,
        id_usuario: int | None = None,
        id_grupo: int | None = None,
    ) -> bool:
        print(f"\n[DEBUG PERMISSAO] Banco Direto -> Validando '{chave}' | param_user_id: {id_usuario} | param_group_id: {id_grupo}")
        
        if _debug_permissoes_ativo():
            return True

        if id_usuario is None or id_grupo is None:
            _uid, _gid = _usuario_da_sessao()
            id_usuario = id_usuario or _uid
            id_grupo = id_grupo or _gid

        #print(f"[DEBUG PERMISSAO] Banco Direto -> Resolvido user_id: {id_usuario} | group_id: {id_grupo}")

        if not id_usuario:
            #print("[DEBUG PERMISSAO] Banco Direto -> Falha: id_usuario é vazio/None.")
            return False

        chave_norm = _normalizar(chave)

        sessao = obterSessaoSqlServer()
        if sessao is None:
            #print("[DEBUG PERMISSAO] Banco Direto -> Falha: Sessao SQL Server é None.")
            return False

        try:
            permissao = next(
                (
                    p
                    for p in sessao.query(Tb_Permissao).filter_by(Id_Sistema=SISTEMA_ID).all()
                    if _normalizar(p.Chave_Permissao) == chave_norm
                ),
                None,
            )
            
            if permissao is None:
                #print(f"[DEBUG PERMISSAO] Banco Direto -> Falha: Permissão '{chave_norm}' NÃO EXISTE na Tb_Permissao para Sistema_ID {SISTEMA_ID}.")
                return False
                
            #print(f"[DEBUG PERMISSAO] Banco Direto -> Permissão encontrada na Tb_Permissao (ID: {permissao.Id_Permissao})")

            # Override de usuário tem prioridade absoluta
            override = sessao.query(Tb_PermissaoUsuario).filter_by(
                Id_Permissao=permissao.Id_Permissao,
                Codigo_Usuario=id_usuario,
            ).first()
            
            if override is not None:
                #print(f"[DEBUG PERMISSAO] Banco Direto -> Encontrado OVERRIDE de usuário na Tb_PermissaoUsuario: Conceder = {override.Conceder}")
                return bool(override.Conceder)

            #print("[DEBUG PERMISSAO] Banco Direto -> Sem override de usuário. Verificando por grupo...")

            # Verificação via grupo
            if id_grupo:
                vinculo = sessao.query(Tb_PermissaoGrupo).filter_by(
                    Id_Permissao=permissao.Id_Permissao,
                    Codigo_UsuarioGrupo=id_grupo,
                ).first()
                if vinculo is not None:
                    #print(f"[DEBUG PERMISSAO] Banco Direto -> SUCESSO: Encontrado vínculo para o grupo {id_grupo} na Tb_PermissaoGrupo.")
                    return True
                else:
                    #print(f"[DEBUG PERMISSAO] Banco Direto -> Falha: Nenhum vínculo encontrado para o grupo {id_grupo}.")
                    pass
            else:
                #print("[DEBUG PERMISSAO] Banco Direto -> Falha: id_grupo é vazio, não é possível verificar vínculo de grupo.")
                pass
        except (ProgrammingError, OperationalError) as exc:
            #print(f"[DEBUG PERMISSAO] Banco Direto -> Erro de banco de dados: {exc}")
            return False
        finally:
            sessao.close()

        #print("[DEBUG PERMISSAO] Banco Direto -> Falha: Usuário não tem permissão concedida por nenhuma via.")
        return False

    @staticmethod
    def usuarioPossuiPermissao(
        chave: str,
        id_usuario: int | None = None,
        id_grupo: int | None = None,
        consultar_cache: bool = True,
    ) -> bool:
        print(f"\n[DEBUG PERMISSAO] usuarioPossuiPermissao -> Solicitada a chave: '{chave}'")
        
        if _debug_permissoes_ativo():
            return True

        chave_norm = _normalizar(chave)
        
        if consultar_cache and has_request_context():
            PermissaoService.sincronizarPermissoesSessao()
            permissoes_sessao = _normalizar_permissoes_em_cache(session.get("permissions"))
            
            if chave_norm in permissoes_sessao:
                resultado_cache = permissoes_sessao[chave_norm]
                #print(f"[DEBUG PERMISSAO] usuarioPossuiPermissao -> Lendo CACHE: {chave_norm} = {resultado_cache}")
                return resultado_cache
            else:
                #print(f"[DEBUG PERMISSAO] usuarioPossuiPermissao -> Chave '{chave_norm}' não está no CACHE. Indo ao banco...")
                pass
        return PermissaoService.verificarPermissao(
            chave,
            id_usuario=id_usuario,
            id_grupo=id_grupo,
        )

    @staticmethod
    def listarPermissoesSessao() -> dict[str, bool]:
        if not has_request_context():
            return {}
        PermissaoService.sincronizarPermissoesSessao()
        return dict(session.get("permissions", {}))

    @staticmethod
    def sincronizarPermissoesSessao(force: bool = False) -> dict[str, bool]:
        if not has_request_context():
            return {}

        if not force and getattr(g, "_permissoes_sincronizadas", False):
            return dict(session.get("permissions", {}))

        print("\n[DEBUG PERMISSAO] sincronizarPermissoesSessao -> Sincronizando cache de permissões da requisição atual.")

        if _debug_permissoes_ativo():
            permissoes = {chave: True for chave in ChavesPermissao.CACHE_SESSAO}
            session["permissions"] = permissoes
            g._permissoes_sincronizadas = True
            return permissoes

        id_usuario = session.get("user_id")
        if not id_usuario:
            #print("[DEBUG PERMISSAO] sincronizarPermissoesSessao -> Sem user_id na sessão. Limpando cache.")
            session.pop("permissions", None)
            g._permissoes_sincronizadas = True
            return {}

        id_grupo = session.get("user_group", {}).get("group_code")
        id_grupo_atual = PermissaoService.obterCodigoGrupoUsuario(id_usuario)
        
        #print(f"[DEBUG PERMISSAO] sincronizarPermissoesSessao -> Grupo Sessao: {id_grupo} | Grupo Atual BD: {id_grupo_atual}")
        
        if id_grupo_atual is not None and id_grupo_atual != id_grupo:
            #print("[DEBUG PERMISSAO] sincronizarPermissoesSessao -> Atualizando grupo na sessão com dados do BD.")
            dados_grupo = dict(session.get("user_group") or {})
            dados_grupo["group_code"] = id_grupo_atual
            session["user_group"] = dados_grupo
            id_grupo = id_grupo_atual

        permissoes = PermissaoService.computarPermissoesSessao(id_usuario, id_grupo)
        session["permissions"] = permissoes
        g._permissoes_sincronizadas = True
        return permissoes

    # --- log ---

    @staticmethod
    def registrarLogAcesso(
        rota: str,
        metodo: str,
        ip: str,
        chave: str,
        permitido: bool,
        parametros: str | None = None,
    ) -> None:
        sessao = obterSessaoSqlServer()
        if sessao is None:
            return
        try:
            id_usuario, _ = _usuario_da_sessao()
            nome_usuario = session.get("user_name", "Anonimo")
            log = Tb_LogAcesso(
                Id_Sistema=SISTEMA_ID,
                Id_Usuario=id_usuario,
                Nome_Usuario=nome_usuario,
                Rota_Acessada=rota,
                Metodo_Http=metodo,
                Ip_Origem=ip,
                Permissao_Exigida=chave.upper(),
                Acesso_Permitido=permitido,
                Parametros_Requisicao=parametros,
            )
            sessao.add(log)
            sessao.commit()
        except Exception as exc:
            sessao.rollback()
            #print(f"[DEBUG PERMISSAO] Erro ao gravar log: {exc}")
        finally:
            sessao.close()

    # --- consultas para a tela de admin ---

    @staticmethod
    def listarGruposDiretorio() -> list[dict[str, Any]]:
        # Omitido prints aqui pois sao chamados pela tela de admin
        registros = _consultar_diretorio_sqlserver(
            """
            SELECT
                codigo_usuariogrupo,
                Sigla_UsuarioGrupo,
                Descricao_UsuarioGrupo
            FROM {directory_db}.dbo.usuariogrupo
            ORDER BY Sigla_UsuarioGrupo, codigo_usuariogrupo
            """
        )
        return [
            {
                "codigo_usuariogrupo": registro["codigo_usuariogrupo"],
                "Sigla_UsuarioGrupo": (
                    registro["Sigla_UsuarioGrupo"]
                    or str(registro["codigo_usuariogrupo"])
                ),
                "Nome_UsuarioGrupo": (
                    registro["Descricao_UsuarioGrupo"]
                    or registro["Sigla_UsuarioGrupo"]
                    or str(registro["codigo_usuariogrupo"])
                ),
            }
            for registro in registros
        ]

    @staticmethod
    def listarUsuariosDiretorio() -> list[dict[str, Any]]:
        registros = _consultar_diretorio_sqlserver(
            """
            SELECT
                u.Codigo_Usuario,
                u.Nome_Usuario,
                u.Login_Usuario,
                u.codigo_usuariogrupo,
                g.Sigla_UsuarioGrupo AS Nome_UsuarioGrupo
            FROM {directory_db}.dbo.usuario AS u
            LEFT JOIN {directory_db}.dbo.usuariogrupo AS g
                ON g.codigo_usuariogrupo = u.codigo_usuariogrupo
            WHERE
                NULLIF(LTRIM(RTRIM(COALESCE(u.Nome_Usuario, ''))), '') IS NOT NULL
                OR NULLIF(LTRIM(RTRIM(COALESCE(u.Login_Usuario, ''))), '') IS NOT NULL
            ORDER BY COALESCE(u.Nome_Usuario, u.Login_Usuario), u.Codigo_Usuario
            """
        )
        return [
            {
                "Codigo_Usuario": registro["Codigo_Usuario"],
                "Nome_Usuario": registro["Nome_Usuario"] or registro["Login_Usuario"],
                "Login_Usuario": registro["Login_Usuario"] or "",
                "Nome_UsuarioGrupo": registro["Nome_UsuarioGrupo"],
                "codigo_usuariogrupo": registro["codigo_usuariogrupo"],
            }
            for registro in registros
        ]

    @staticmethod
    def obterCodigoGrupoUsuario(id_usuario: int) -> int | None:
        registros = _consultar_diretorio_sqlserver(
            """
            SELECT TOP 1 codigo_usuariogrupo
            FROM {directory_db}.dbo.usuario
            WHERE Codigo_Usuario = :id_usuario
            """,
            {"id_usuario": id_usuario},
        )
        if not registros:
            return None
        codigo_grupo = registros[0].get("codigo_usuariogrupo")
        return int(codigo_grupo) if codigo_grupo is not None else None

    @staticmethod
    def listarTodasPermissoes() -> list[Tb_Permissao]:
        sessao = obterSessaoSqlServer()
        if sessao is None:
            return []
        try:
            return (
                sessao.query(Tb_Permissao)
                .filter_by(Id_Sistema=SISTEMA_ID)
                .order_by(Tb_Permissao.Categoria_Permissao, Tb_Permissao.Descricao_Permissao)
                .all()
            )
        finally:
            sessao.close()

    @staticmethod
    def idsPermitidosPorGrupo(id_grupo: int) -> list[int]:
        sessao = obterSessaoSqlServer()
        if sessao is None:
            return []
        try:
            vinculos = sessao.query(Tb_PermissaoGrupo).filter_by(Codigo_UsuarioGrupo=id_grupo).all()
            return [v.Id_Permissao for v in vinculos]
        finally:
            sessao.close()

    @staticmethod
    def acessosUsuario(id_usuario: int) -> dict[str, Any]:
        id_grupo = PermissaoService.obterCodigoGrupoUsuario(id_usuario)
        if id_grupo is None:
            _, id_grupo_sessao = _usuario_da_sessao()
            id_grupo = id_grupo_sessao

        heranca: list[int] = []
        if id_grupo:
            heranca = PermissaoService.idsPermitidosPorGrupo(id_grupo)

        sessao = obterSessaoSqlServer()
        if sessao is None:
            return {"ids_heranca": heranca, "overrides": {}}
        try:
            overrides = sessao.query(Tb_PermissaoUsuario).filter_by(Codigo_Usuario=id_usuario).all()
            override_map = {ov.Id_Permissao: ov.Conceder for ov in overrides}
        finally:
            sessao.close()
        return {"ids_heranca": heranca, "overrides": override_map}

    @staticmethod
    def salvarVinculoGrupo(id_grupo: int, id_permissao: int, conceder: bool) -> None:
        sessao = _obterSessaoSqlServerObrigatoria()
        try:
            vinculo = sessao.query(Tb_PermissaoGrupo).filter_by(
                Codigo_UsuarioGrupo=id_grupo,
                Id_Permissao=id_permissao,
            ).first()
            if conceder and vinculo is None:
                sessao.add(Tb_PermissaoGrupo(
                    Codigo_UsuarioGrupo=id_grupo,
                    Id_Permissao=id_permissao,
                ))
            elif not conceder and vinculo is not None:
                sessao.delete(vinculo)
            sessao.commit()
        except Exception:
            sessao.rollback()
            raise
        finally:
            sessao.close()

    @staticmethod
    def salvarVinculoUsuario(id_usuario: int, id_permissao: int, conceder: bool | None) -> None:
        sessao = _obterSessaoSqlServerObrigatoria()
        try:
            override = sessao.query(Tb_PermissaoUsuario).filter_by(
                Codigo_Usuario=id_usuario,
                Id_Permissao=id_permissao,
            ).first()
            if conceder is None:
                if override:
                    sessao.delete(override)
            elif override:
                override.Conceder = conceder
            else:
                sessao.add(Tb_PermissaoUsuario(
                    Codigo_Usuario=id_usuario,
                    Id_Permissao=id_permissao,
                    Conceder=conceder,
                ))
            sessao.commit()
        except Exception:
            sessao.rollback()
            raise
        finally:
            sessao.close()

    @staticmethod
    def criarPermissao(chave: str, descricao: str, categoria: str) -> Tb_Permissao:
        sessao = _obterSessaoSqlServerObrigatoria()
        try:
            existente = sessao.query(Tb_Permissao).filter_by(
                Id_Sistema=SISTEMA_ID,
                Chave_Permissao=chave,
            ).first()
            if existente:
                raise ValueError(f"Permissão '{chave}' já existe.")
            nova = Tb_Permissao(
                Id_Sistema=SISTEMA_ID,
                Chave_Permissao=chave,
                Descricao_Permissao=descricao,
                Categoria_Permissao=categoria,
            )
            sessao.add(nova)
            sessao.commit()
            return nova
        except Exception:
            sessao.rollback()
            raise
        finally:
            sessao.close()

    @staticmethod
    def computarPermissoesSessao(id_usuario: int | None, id_grupo: int | None) -> dict[str, bool]:
        print("\n[DEBUG CACHE SESSAO] ===============================================")
        print(f"[DEBUG CACHE SESSAO] Computando cache para user_id={id_usuario}, group_id={id_grupo}")

        if _debug_permissoes_ativo():
            return {chave: True for chave in ChavesPermissao.CACHE_SESSAO}

        if not id_usuario:
            print("[DEBUG CACHE SESSAO] Abortando: id_usuario vazio.")
            return {chave: False for chave in ChavesPermissao.CACHE_SESSAO}

        try:
            sessao = obterSessaoSqlServer()
            if sessao is None:
                print("[DEBUG CACHE SESSAO] Erro: Falha ao obter sessao SQL Server.")
                return {chave: False for chave in ChavesPermissao.CACHE_SESSAO}

            # 1. Pegar todas as chaves do sistema
            permissoes_sistema = sessao.query(Tb_Permissao).filter_by(Id_Sistema=SISTEMA_ID).all()
            ids_por_chave = {
                _normalizar(permissao.Chave_Permissao): permissao.Id_Permissao
                for permissao in permissoes_sistema
            }
            print(f"[DEBUG CACHE SESSAO] Chaves encontradas no DB (Sistema {SISTEMA_ID}): {ids_por_chave}")

            # 2. Pegar os overrides do usuario
            overrides_usuario = {
                override.Id_Permissao: bool(override.Conceder)
                for override in sessao.query(Tb_PermissaoUsuario).filter_by(Codigo_Usuario=id_usuario).all()
            }
            print(f"[DEBUG CACHE SESSAO] Overrides do usuario {id_usuario}: {overrides_usuario}")

            # 3. Pegar chaves vinculadas ao grupo
            ids_permitidos_grupo = set()
            if id_grupo:
                ids_permitidos_grupo = {
                    vinculo.Id_Permissao
                    for vinculo in sessao.query(Tb_PermissaoGrupo).filter_by(Codigo_UsuarioGrupo=id_grupo).all()
                }
            print(f"[DEBUG CACHE SESSAO] Permissões do grupo {id_grupo}: {ids_permitidos_grupo}")

            # 4. Montar o cache cruzando os dados
            permissoes = {}
            for chave in ChavesPermissao.CACHE_SESSAO:
                chave_norm = _normalizar(chave)
                id_permissao = ids_por_chave.get(chave_norm)
                
                if id_permissao is None:
                    permissoes[chave] = False
                elif id_permissao in overrides_usuario:
                    permissoes[chave] = overrides_usuario[id_permissao]
                else:
                    permissoes[chave] = id_permissao in ids_permitidos_grupo

            print(f"[DEBUG CACHE SESSAO] Mapa Final Computado: {permissoes}")
            print("[DEBUG CACHE SESSAO] ===============================================\n")
            return permissoes

        except (ProgrammingError, OperationalError) as exc:
            print(f"[DEBUG CACHE SESSAO] Erro Crítico (Banco Indisponível): {exc}")
            return {chave: False for chave in ChavesPermissao.CACHE_SESSAO}
        finally:
            if 'sessao' in locals() and sessao is not None:
                sessao.close()


# ---------------------------------------------------------------------------
# Decorator de proteção de rotas
# ---------------------------------------------------------------------------

def RequerPermissao(chave: str):
    def decorador(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            print(f"\n[DEBUG DECORATOR] Rota interceptada: '{request.path}' | Exigindo permissão: '{chave}'")
            
            if _debug_permissoes_ativo():
                return f(*args, **kwargs)

            # Garante que o usuário esteja autenticado
            if "user_name" not in session:
                print(f"[DEBUG DECORATOR] Usuário sem 'user_name' na sessão atual. Verificando tokens...")
                
                auth_header = request.headers.get("Authorization", "")
                if auth_header.startswith("Bearer "):
                    token = auth_header[7:]
                    from Utils.auth.ProvedorUsuario import ObterUsuarioPorToken
                    from Utils.auth.Autenticacao import PopularSessaoUsuario
                    dados = ObterUsuarioPorToken(token)
                    if not (dados and PopularSessaoUsuario(dados)):
                        print(f"[DEBUG DECORATOR] Bearer Token inválido/expirado.")
                        return api_error("Token inválido ou expirado.", status=401)
                else:
                    from Utils.auth.Autenticacao import (
                        ValidarUsuarioPorCredenciais,
                        ValidarUsuarioPorToken,
                    )
                    autenticado = ValidarUsuarioPorToken()
                    if not autenticado and request.args.get("login_hash"):
                        autenticado = ValidarUsuarioPorCredenciais()

                    if not autenticado:
                        print(f"[DEBUG DECORATOR] Falha na autenticação via token/hash de URL. Negando acesso 401/403.")
                        if _eh_requisicao_api():
                            return api_error("Autenticação necessária.", status=401)
                        return render_template("Auth/InfoLogin.html"), 403

            print(f"[DEBUG DECORATOR] Usuário validado na sessão. Chamando usuarioPossuiPermissao()...")
            permitido = PermissaoService.usuarioPossuiPermissao(chave)
            
            ip = _ip_da_requisicao()
            params: dict = {}
            if request.args:
                params["query"] = dict(request.args)
            if request.form:
                params["form"] = dict(request.form)
            if request.is_json:
                try:
                    params["json"] = request.get_json(silent=True) or {}
                except Exception:
                    pass
            params_str = json.dumps(params, ensure_ascii=False)[:1000] if params else None

            print(f"[DEBUG DECORATOR] Resultado final de '{chave}' -> PERMITIDO: {permitido}")

            PermissaoService.registrarLogAcesso(
                request.path, request.method, ip, chave, permitido, params_str
            )

            if not permitido:
                if _eh_requisicao_api():
                    return api_error("Acesso negado.", details={"chave": chave}, status=403)
                return render_no_permission(f"Permissão requerida: {chave}")

            return f(*args, **kwargs)

        return wrapper
    return decorador
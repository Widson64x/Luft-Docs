from __future__ import annotations

import os
import string
from typing import Any

import markdown

from Config import DATA_DIR, GLOBAL_DATA_DIR
from Db.Connections import obterSessaoPostgres
from Models import Modulo, PalavraGlobal


def FormatarModuloParaDicionario(modulo: Modulo | None) -> dict | None:
    """Converte um objeto Modulo do ORM para o formato esperado pela aplicacao."""
    if not modulo:
        return None

    return {
        "id": modulo.id,
        "nome": modulo.nome,
        "descricao": modulo.descricao,
        "icone": modulo.icone,
        "is_restrito": modulo.is_restrito,
        "status": modulo.status,
        "palavras_chave": [palavra.palavra for palavra in modulo.palavras_chave],
        "relacionados": [relacionado.id for relacionado in modulo.relacionados],
        "edit_history": [
        {
            "event": historico.event,
            "version": historico.version,
            "editor": historico.editor,
            "approver": historico.approver,
            "timestamp": historico.timestamp,
            "backup_file_doc": historico.backup_file_doc,
            "backup_file_tech": historico.backup_file_tech,
        }
        for historico in modulo.edit_history
        ],
        "ultima_edicao": {
            "user": modulo.ultima_edicao_user,
            "data": modulo.ultima_edicao_data,
        },
        "pending_edit_info": {
            "user": modulo.pending_edit_user,
            "data": modulo.pending_edit_data,
        },
        "version_info": {
            "current_version": modulo.current_version,
            "last_approved_by": modulo.last_approved_by,
            "last_approved_on": modulo.last_approved_on,
        },
        "current_version": modulo.current_version,
        "last_approved_by": modulo.last_approved_by,
        "last_approved_on": modulo.last_approved_on,
    }


def CarregarModulos() -> tuple[list[dict], dict[str, str]]:
    """Carrega todos os modulos e palavras globais registrados no banco."""
    sessao = obterSessaoPostgres()
    try:
        modulos = []
        for modulo in sessao.query(Modulo).all():
            modulos.append(
                {
                    "id": modulo.id,
                    "nome": modulo.nome,
                    "descricao": modulo.descricao,
                    "icone": modulo.icone,
                    "is_restrito": modulo.is_restrito,
                    "status": modulo.status,
                    "current_version": modulo.current_version,
                    "edit_history": modulo.edit_history,
                    "pending_edit_info": modulo.pending_edit_info,
                }
            )
        palavras_globais = {
            palavra.palavra: palavra.descricao
            for palavra in sessao.query(PalavraGlobal).all()
        }
        return modulos, palavras_globais
    finally:
        sessao.close()


def CarregarModulosAprovados() -> tuple[list[dict], dict[str, str]]:
    """Carrega apenas os modulos aprovados e suas palavras globais associadas."""
    sessao = obterSessaoPostgres()
    try:
        modulos_aprovados = [
            FormatarModuloParaDicionario(modulo)
            for modulo in sessao.query(Modulo).filter_by(Status="aprovado").all()
        ]
        palavras_globais = {
            palavra.palavra: palavra.descricao
            for palavra in sessao.query(PalavraGlobal).all()
        }
        return modulos_aprovados, palavras_globais
    finally:
        sessao.close()


def ObterModuloPorId(identificadorModulo: str) -> dict | None:
    """Busca um modulo por identificador primario."""
    sessao = obterSessaoPostgres()
    try:
        return FormatarModuloParaDicionario(sessao.get(Modulo, identificadorModulo))
    finally:
        sessao.close()


def ModuloEhRestrito(modulo: Modulo | dict[str, Any] | None) -> bool:
    """Determina se um modulo usa a flag de restricao do banco."""
    if modulo is None:
        return False
    if isinstance(modulo, dict):
        return bool(modulo.get("is_restrito") or modulo.get("Is_Restrito"))
    return bool(getattr(modulo, "is_restrito", False))


def FiltrarModulosRestritos(
    modulos: list[dict[str, Any]], podeVerRestritos: bool
) -> list[dict[str, Any]]:
    """Remove da colecao os modulos marcados como restritos quando necessario."""
    if podeVerRestritos:
        return modulos
    return [modulo for modulo in modulos if not ModuloEhRestrito(modulo)]


def CriarMapaRestricaoModulos(modulos: list[dict[str, Any]]) -> dict[str, bool]:
    """Cria um mapa rapido de id -> modulo restrito para filtros secundarios."""
    return {
        str(modulo["id"]): ModuloEhRestrito(modulo)
        for modulo in modulos
        if modulo.get("id")
    }


def DocumentoEhRestrito(
    identificadorDocumento: str | None, mapaRestricoes: dict[str, bool]
) -> bool:
    """Resolve se um documento pertence a um modulo restrito."""
    if not identificadorDocumento:
        return False

    identificador_base = str(identificadorDocumento)
    if identificador_base.startswith("tech_"):
        identificador_base = identificador_base[5:]

    return bool(mapaRestricoes.get(identificador_base, False))


def DocumentoEhTecnico(identificadorDocumento: str | None) -> bool:
    """Resolve se um documento representa a documentacao tecnica de um modulo."""
    return bool(identificadorDocumento and str(identificadorDocumento).startswith("tech_"))


def ModuloPossuiDocumentacaoTecnica(identificadorModulo: str) -> bool:
    """Indica se o modulo possui um arquivo de documentacao tecnica disponivel."""
    caminho = os.path.join(DATA_DIR, identificadorModulo, "technical_documentation.md")
    return os.path.exists(caminho)


def CarregarMarkdown(identificadorModulo: str) -> str | None:
    """Carrega e converte a documentacao principal de um modulo para HTML."""
    caminho = os.path.join(DATA_DIR, identificadorModulo, "documentation.md")
    if not os.path.exists(caminho):
        return None
    with open(caminho, encoding="utf-8") as arquivo_markdown:
        texto_markdown = arquivo_markdown.read()
        return markdown.markdown(texto_markdown, extensions=["fenced_code", "tables"])


def CarregarMarkdownTecnico(identificadorModulo: str) -> str | None:
    """Carrega a documentacao tecnica bruta de um modulo."""
    caminho = os.path.join(DATA_DIR, identificadorModulo, "technical_documentation.md")
    if not os.path.exists(caminho):
        return None
    with open(caminho, encoding="utf-8") as arquivo_markdown:
        return arquivo_markdown.read()


def CarregarMarkdownSubmodulo(nomeSubmodulo: str) -> str | None:
    """Carrega o markdown de um submodulo pesquisando pelo nome do arquivo."""
    nome_arquivo = nomeSubmodulo.replace(" ", "_") + ".md"
    caminho_arquivo = next(iter(GLOBAL_DATA_DIR.rglob(nome_arquivo)), None)
    if caminho_arquivo:
        return caminho_arquivo.read_text(encoding="utf-8")
    return None


def LimparTexto(texto: str) -> str:
    """Normaliza um texto para comparacoes simples baseadas em tokens."""
    return texto.lower().translate(str.maketrans("", "", string.punctuation))


def CalcularScore(paragrafo: str, termosConsulta: list[str]) -> int:
    """Calcula um score simples com base na intersecao de termos."""
    palavras = set(LimparTexto(paragrafo).split())
    return sum(1 for termo in termosConsulta if termo in palavras)
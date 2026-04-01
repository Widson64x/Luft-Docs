from Models.Analytics import (
    AcessoDocumento,
    AvaliacaoDocumento,
    FeedbackIA,
    LogBusca,
    ReporteBug,
)
from Models.Base import BasePostgres, BaseSqlServer
from Models.Conteudo import (
    HistoricoEdicao,
    Modulo,
    ModuloRelacionado,
    PalavraChave,
    PalavraGlobal,
    roteirosModulos,
)
from Models.Metadados import CategoriaTagMeta, RelacaoObjetoTagMeta, TagMeta
from Models.Permissoes import (
    Tb_LogAcesso,
    Tb_Permissao,
    Tb_PermissaoGrupo,
    Tb_PermissaoUsuario,
    UsuarioBanco,
    UsuarioGrupoBanco,
)
from Models.Roteiros import LogAuditoriaRoteiro, Roteiro


BugReport = ReporteBug
IAFeedback = FeedbackIA
DocumentAccess = AcessoDocumento
SearchLog = LogBusca
MetaTagCategoria = CategoriaTagMeta
MetaTag = TagMeta
MetaObjetoRelTag = RelacaoObjetoTagMeta
Evaluation = AvaliacaoDocumento
RoteiroAuditLog = LogAuditoriaRoteiro

__all__ = [
    "AcessoDocumento",
    "AvaliacaoDocumento",
    "BasePostgres",
    "BaseSqlServer",
    "BugReport",
    "CategoriaTagMeta",
    "DocumentAccess",
    "Evaluation",
    "FeedbackIA",
    "HistoricoEdicao",
    "IAFeedback",
    "LogAuditoriaRoteiro",
    "LogBusca",
    "MetaObjetoRelTag",
    "MetaTag",
    "MetaTagCategoria",
    "Modulo",
    "ModuloRelacionado",
    "PalavraChave",
    "PalavraGlobal",
    "ReporteBug",
    "RelacaoObjetoTagMeta",
    "Roteiro",
    "RoteiroAuditLog",
    "SearchLog",
    "TagMeta",
    "Tb_LogAcesso",
    "Tb_Permissao",
    "Tb_PermissaoGrupo",
    "Tb_PermissaoUsuario",
    "UsuarioBanco",
    "UsuarioGrupoBanco",
    "roteirosModulos",
]
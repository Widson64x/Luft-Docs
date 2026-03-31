# models.py
from datetime import datetime

from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import synonym
from sqlalchemy.sql import func

db = SQLAlchemy()

permissoes_grupos = db.Table(
    "Tb_Docs_RelacaoPermissoesGrupos",
    db.Column("PermissaoId", db.Integer, db.ForeignKey("Tb_Docs_Permissoes.Id"), primary_key=True),
    db.Column("GrupoId", db.Integer, db.ForeignKey("Tb_Docs_GruposPermissao.Id"), primary_key=True),
)

permissoes_usuarios = db.Table(
    "Tb_Docs_RelacaoPermissoesUsuarios",
    db.Column("PermissaoId", db.Integer, db.ForeignKey("Tb_Docs_Permissoes.Id"), primary_key=True),
    db.Column("UsuarioId", db.Integer, db.ForeignKey("Tb_Docs_UsuariosPermissao.Id"), primary_key=True),
)

roteiros_modulos = db.Table(
    "Tb_Docs_RelacaoRoteirosModulos",
    db.Column("RoteiroId", db.Integer, db.ForeignKey("Tb_Docs_Roteiros.Id"), primary_key=True),
    db.Column("ModuloId", db.String(100), db.ForeignKey("Tb_Docs_Modulos.Id"), primary_key=True),
)


class Permissao(db.Model):
    __tablename__ = "Tb_Docs_Permissoes"

    Id = db.Column("Id", db.Integer, primary_key=True)
    NomePermissao = db.Column("NomePermissao", db.String(100), unique=True, nullable=False)
    Descricao = db.Column("Descricao", db.String(255), nullable=True)

    Grupos = db.relationship(
        "Grupo",
        secondary=permissoes_grupos,
        lazy="subquery",
        back_populates="Permissoes",
    )
    Usuarios = db.relationship(
        "Usuario",
        secondary=permissoes_usuarios,
        lazy="subquery",
        back_populates="Permissoes",
    )

    id = synonym("Id")
    nome = synonym("NomePermissao")
    descricao = synonym("Descricao")
    grupos = synonym("Grupos")
    usuarios = synonym("Usuarios")

    def __repr__(self):
        return f"<Permissao {self.NomePermissao}>"


class Grupo(db.Model):
    __tablename__ = "Tb_Docs_GruposPermissao"

    Id = db.Column("Id", db.Integer, primary_key=True)
    NomeGrupo = db.Column("NomeGrupo", db.String(100), unique=True, nullable=False)

    Permissoes = db.relationship(
        "Permissao",
        secondary=permissoes_grupos,
        lazy="subquery",
        back_populates="Grupos",
    )

    id = synonym("Id")
    nome = synonym("NomeGrupo")
    permissoes = synonym("Permissoes")

    def __repr__(self):
        return f"<Grupo {self.NomeGrupo}>"


class Usuario(db.Model):
    __tablename__ = "Tb_Docs_UsuariosPermissao"

    Id = db.Column("Id", db.Integer, primary_key=True)
    NomeUsuario = db.Column("NomeUsuario", db.String(100), unique=True, nullable=False)

    Permissoes = db.relationship(
        "Permissao",
        secondary=permissoes_usuarios,
        lazy="subquery",
        back_populates="Usuarios",
    )

    id = synonym("Id")
    nome = synonym("NomeUsuario")
    permissoes = synonym("Permissoes")

    def __repr__(self):
        return f"<Usuario {self.NomeUsuario}>"


class ReporteBug(db.Model):
    __tablename__ = "Tb_Docs_ReportesBug"

    Id = db.Column("Id", db.Integer, primary_key=True, autoincrement=True)
    UsuarioId = db.Column("UsuarioId", db.Integer, nullable=False)
    TipoReporte = db.Column("TipoReporte", db.String(50), nullable=False)
    EntidadeAlvo = db.Column("EntidadeAlvo", db.String(100), nullable=True)
    CategoriaErro = db.Column("CategoriaErro", db.String(100), nullable=True)
    Descricao = db.Column("Descricao", db.Text, nullable=False)
    Status = db.Column("Status", db.String(50), nullable=False, default="aberto")
    CriadoEm = db.Column("CriadoEm", db.TIMESTAMP, server_default=func.now(), nullable=False)

    id = synonym("Id")
    user_id = synonym("UsuarioId")
    report_type = synonym("TipoReporte")
    target_entity = synonym("EntidadeAlvo")
    error_category = synonym("CategoriaErro")
    description = synonym("Descricao")
    status = synonym("Status")
    created_at = synonym("CriadoEm")

    def __repr__(self):
        return f"<ReporteBug {self.Id} por {self.UsuarioId}>"


class FeedbackIA(db.Model):
    __tablename__ = "Tb_Docs_FeedbackIA"

    Id = db.Column("Id", db.Integer, primary_key=True, autoincrement=True)
    RespostaId = db.Column("RespostaId", db.String, nullable=False)
    UsuarioId = db.Column("UsuarioId", db.String, nullable=False)
    PerguntaUsuario = db.Column("PerguntaUsuario", db.Text, nullable=True)
    ModeloUtilizado = db.Column("ModeloUtilizado", db.String(100), nullable=True)
    FontesContexto = db.Column("FontesContexto", db.Text, nullable=True)
    Avaliacao = db.Column("Avaliacao", db.Integer, nullable=True)
    Comentario = db.Column("Comentario", db.Text, nullable=True)
    RegistradoEm = db.Column("RegistradoEm", db.TIMESTAMP, nullable=False, default=datetime.utcnow)

    feedback_id = synonym("Id")
    response_id = synonym("RespostaId")
    user_id = synonym("UsuarioId")
    user_question = synonym("PerguntaUsuario")
    model_used = synonym("ModeloUtilizado")
    context_sources = synonym("FontesContexto")
    rating = synonym("Avaliacao")
    comment = synonym("Comentario")
    timestamp = synonym("RegistradoEm")

    def __repr__(self):
        return f"<FeedbackIA {self.Id} for response {self.RespostaId}>"


class AcessoDocumento(db.Model):
    __tablename__ = "Tb_Docs_LogAcessosDocumentos"

    DocumentoId = db.Column("DocumentoId", db.String(255), primary_key=True)
    QuantidadeAcessos = db.Column("QuantidadeAcessos", db.Integer, nullable=False, default=1)
    UltimoAcessoEm = db.Column(
        "UltimoAcessoEm",
        db.TIMESTAMP,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    document_id = synonym("DocumentoId")
    access_count = synonym("QuantidadeAcessos")
    last_access = synonym("UltimoAcessoEm")


class LogBusca(db.Model):
    __tablename__ = "Tb_Docs_LogBuscas"

    TermoBusca = db.Column("TermoBusca", db.String(255), primary_key=True)
    QuantidadeBuscas = db.Column("QuantidadeBuscas", db.Integer, nullable=False, default=1)
    UltimaBuscaEm = db.Column(
        "UltimaBuscaEm",
        db.TIMESTAMP,
        nullable=False,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    query_term = synonym("TermoBusca")
    search_count = synonym("QuantidadeBuscas")
    last_searched = synonym("UltimaBuscaEm")


class Modulo(db.Model):
    __tablename__ = "Tb_Docs_Modulos"

    Id = db.Column("Id", db.String(100), primary_key=True)
    Nome = db.Column("Nome", db.String(255), nullable=False)
    Descricao = db.Column("Descricao", db.Text, nullable=True)
    Icone = db.Column("Icone", db.String(50), nullable=True)
    Status = db.Column("Status", db.String(50), nullable=True)
    UsuarioUltimaEdicao = db.Column("UsuarioUltimaEdicao", db.String(100), nullable=True)
    DataUltimaEdicao = db.Column("DataUltimaEdicao", db.String(100), nullable=True)
    UsuarioEdicaoPendente = db.Column("UsuarioEdicaoPendente", db.String(100), nullable=True)
    DataEdicaoPendente = db.Column("DataEdicaoPendente", db.String(100), nullable=True)
    VersaoAtual = db.Column("VersaoAtual", db.String(50), nullable=True)
    AprovadoPor = db.Column("AprovadoPor", db.String(100), nullable=True)
    AprovadoEm = db.Column("AprovadoEm", db.String(100), nullable=True)

    PalavrasChave = db.relationship(
        "PalavraChave",
        back_populates="Modulo",
        cascade="all, delete-orphan",
        lazy="joined",
    )
    HistoricoEdicoes = db.relationship(
        "HistoricoEdicao",
        back_populates="Modulo",
        cascade="all, delete-orphan",
        lazy="joined",
    )
    Roteiros = db.relationship(
        "Roteiro",
        secondary=roteiros_modulos,
        back_populates="Modulos",
        lazy="joined",
    )
    Relacionados = db.relationship(
        "Modulo",
        secondary="Tb_Docs_ModulosRelacionados",
        primaryjoin=lambda: Modulo.Id == ModuloRelacionado.ModuloId,
        secondaryjoin=lambda: Modulo.Id == ModuloRelacionado.RelacionadoId,
        backref="RelacionadoPor",
        lazy="joined",
    )

    id = synonym("Id")
    nome = synonym("Nome")
    descricao = synonym("Descricao")
    icone = synonym("Icone")
    status = synonym("Status")
    ultima_edicao_user = synonym("UsuarioUltimaEdicao")
    ultima_edicao_data = synonym("DataUltimaEdicao")
    pending_edit_user = synonym("UsuarioEdicaoPendente")
    pending_edit_data = synonym("DataEdicaoPendente")
    current_version = synonym("VersaoAtual")
    last_approved_by = synonym("AprovadoPor")
    last_approved_on = synonym("AprovadoEm")
    palavras_chave = synonym("PalavrasChave")
    edit_history = synonym("HistoricoEdicoes")
    roteiros = synonym("Roteiros")
    relacionados = synonym("Relacionados")

    @property
    def InfoEdicaoPendente(self):
        return {"data": self.DataEdicaoPendente, "user": self.UsuarioEdicaoPendente}

    @property
    def pending_edit_info(self):
        return self.InfoEdicaoPendente


class PalavraChave(db.Model):
    __tablename__ = "Tb_Docs_PalavrasChave"

    Id = db.Column("Id", db.Integer, primary_key=True, autoincrement=True)
    ModuloId = db.Column("ModuloId", db.String(100), db.ForeignKey("Tb_Docs_Modulos.Id"), nullable=False)
    Palavra = db.Column("Palavra", db.String(100), nullable=False)

    Modulo = db.relationship("Modulo", back_populates="PalavrasChave")

    id = synonym("Id")
    modulo_id = synonym("ModuloId")
    palavra = synonym("Palavra")
    modulo = synonym("Modulo")


class ModuloRelacionado(db.Model):
    __tablename__ = "Tb_Docs_ModulosRelacionados"

    Id = db.Column("Id", db.Integer, primary_key=True, autoincrement=True)
    ModuloId = db.Column("ModuloId", db.String(100), db.ForeignKey("Tb_Docs_Modulos.Id"), nullable=False)
    RelacionadoId = db.Column("RelacionadoId", db.String(100), db.ForeignKey("Tb_Docs_Modulos.Id"), nullable=False)

    id = synonym("Id")
    modulo_id = synonym("ModuloId")
    relacionado_id = synonym("RelacionadoId")


class HistoricoEdicao(db.Model):
    __tablename__ = "Tb_Docs_HistoricoEdicoes"

    Id = db.Column("Id", db.Integer, primary_key=True, autoincrement=True)
    ModuloId = db.Column("ModuloId", db.String(100), db.ForeignKey("Tb_Docs_Modulos.Id"), nullable=False)
    Evento = db.Column("Evento", db.String(100))
    Versao = db.Column("Versao", db.String(50))
    Editor = db.Column("Editor", db.String(100))
    Aprovador = db.Column("Aprovador", db.String(100))
    RegistradoEm = db.Column("RegistradoEm", db.String(100))
    ArquivoBackupDocumentacao = db.Column("ArquivoBackupDocumentacao", db.String(255))
    ArquivoBackupDocumentacaoTecnica = db.Column("ArquivoBackupDocumentacaoTecnica", db.String(255))

    Modulo = db.relationship("Modulo", back_populates="HistoricoEdicoes")

    id = synonym("Id")
    modulo_id = synonym("ModuloId")
    event = synonym("Evento")
    version = synonym("Versao")
    editor = synonym("Editor")
    approver = synonym("Aprovador")
    timestamp = synonym("RegistradoEm")
    backup_file_doc = synonym("ArquivoBackupDocumentacao")
    backup_file_tech = synonym("ArquivoBackupDocumentacaoTecnica")
    modulo = synonym("Modulo")


class PalavraGlobal(db.Model):
    __tablename__ = "Tb_Docs_PalavrasGlobais"

    Palavra = db.Column("Palavra", db.String(100), primary_key=True)
    Descricao = db.Column("Descricao", db.Text)

    palavra = synonym("Palavra")
    descricao = synonym("Descricao")


class CategoriaTagMeta(db.Model):
    __tablename__ = "Tb_Docs_CategoriasTagsMeta"

    Id = db.Column("Id", db.Integer, primary_key=True)
    Nome = db.Column("Nome", db.String(100), unique=True, nullable=False)
    Descricao = db.Column("Descricao", db.Text, nullable=True)

    Tags = db.relationship(
        "TagMeta",
        back_populates="Categoria",
        cascade="all, delete-orphan",
        lazy="joined",
    )

    id = synonym("Id")
    nome = synonym("Nome")
    descricao = synonym("Descricao")
    tags = synonym("Tags")

    def __repr__(self):
        return f"<CategoriaTagMeta {self.Nome}>"


class TagMeta(db.Model):
    __tablename__ = "Tb_Docs_TagsMeta"

    Id = db.Column("Id", db.Integer, primary_key=True)
    Tag = db.Column("Tag", db.String(50), unique=True, nullable=False)
    Descricao = db.Column("Descricao", db.Text, nullable=False)
    CategoriaId = db.Column("CategoriaId", db.Integer, db.ForeignKey("Tb_Docs_CategoriasTagsMeta.Id"), nullable=False)

    Categoria = db.relationship("CategoriaTagMeta", back_populates="Tags")
    ObjetosAssociados = db.relationship(
        "RelacaoObjetoTagMeta",
        back_populates="TagRelacionada",
        cascade="all, delete-orphan",
    )

    id = synonym("Id")
    tag = synonym("Tag")
    descricao = synonym("Descricao")
    categoria_id = synonym("CategoriaId")
    categoria = synonym("Categoria")
    objetos_associados = synonym("ObjetosAssociados")

    def __repr__(self):
        return f"<TagMeta {self.Tag}>"


class RelacaoObjetoTagMeta(db.Model):
    __tablename__ = "Tb_Docs_RelacaoObjetosTagsMeta"

    Id = db.Column("Id", db.Integer, primary_key=True)
    NomeObjeto = db.Column("NomeObjeto", db.String(255), nullable=False)
    TipoObjeto = db.Column("TipoObjeto", db.String(50), nullable=False, default="TABLE")
    TagId = db.Column("TagId", db.Integer, db.ForeignKey("Tb_Docs_TagsMeta.Id"), nullable=False)

    TagRelacionada = db.relationship("TagMeta", back_populates="ObjetosAssociados")

    id = synonym("Id")
    nome_objeto = synonym("NomeObjeto")
    tipo_objeto = synonym("TipoObjeto")
    tag_id = synonym("TagId")
    tag = synonym("TagRelacionada")

    def __repr__(self):
        tag_repr = self.TagRelacionada.Tag if self.TagRelacionada else "N/A"
        return f"<RelacaoObjetoTagMeta Objeto:{self.NomeObjeto} -> Tag:{tag_repr}>"


class AvaliacaoDocumento(db.Model):
    __tablename__ = "Tb_Docs_AvaliacoesDocumentos"

    Id = db.Column("Id", db.Integer, primary_key=True)
    DocumentoId = db.Column("DocumentoId", db.String(100), db.ForeignKey("Tb_Docs_Modulos.Id"))
    Avaliacao = db.Column("Avaliacao", db.Integer)
    Comentario = db.Column("Comentario", db.Text)
    Sugestoes = db.Column("Sugestoes", db.Text)
    Trechos = db.Column("Trechos", db.Text)
    MudancasSolicitadas = db.Column("MudancasSolicitadas", db.Text)

    id = synonym("Id")
    document_id = synonym("DocumentoId")
    rating = synonym("Avaliacao")
    feedback = synonym("Comentario")
    suggestions = synonym("Sugestoes")
    techos = synonym("Trechos")
    changes = synonym("MudancasSolicitadas")


class Roteiro(db.Model):
    __tablename__ = "Tb_Docs_Roteiros"

    Id = db.Column("Id", db.Integer, primary_key=True, autoincrement=True)
    Titulo = db.Column("Titulo", db.String(255), nullable=False)
    Descricao = db.Column("Descricao", db.Text, nullable=True)
    Tipo = db.Column("Tipo", db.String(50), nullable=False, default="link")
    Conteudo = db.Column("Conteudo", db.Text, nullable=False)
    Icone = db.Column("Icone", db.String(50), nullable=True, default="bi-play-circle")
    Ordem = db.Column("Ordem", db.Integer, default=0)
    CriadoEm = db.Column("CriadoEm", db.DateTime(timezone=True))
    AtualizadoEm = db.Column("AtualizadoEm", db.DateTime(timezone=True))

    Modulos = db.relationship(
        "Modulo",
        secondary=roteiros_modulos,
        back_populates="Roteiros",
        lazy="subquery",
    )
    LogsAuditoria = db.relationship(
        "LogAuditoriaRoteiro",
        back_populates="Roteiro",
        cascade="all, delete-orphan",
    )

    id = synonym("Id")
    titulo = synonym("Titulo")
    descricao = synonym("Descricao")
    tipo = synonym("Tipo")
    conteudo = synonym("Conteudo")
    icone = synonym("Icone")
    ordem = synonym("Ordem")
    created_at = synonym("CriadoEm")
    updated_at = synonym("AtualizadoEm")
    modulos = synonym("Modulos")
    audit_logs = synonym("LogsAuditoria")

    def __repr__(self):
        return f"<Roteiro {self.Id}: {self.Titulo}>"

    @staticmethod
    def _iso(dt):
        if not dt:
            return None
        if isinstance(dt, str):
            return dt.replace(" ", "T") + "Z"
        iso = dt.isoformat()
        return iso.replace("+00:00", "Z")

    def to_dict(self):
        return {
            "id": self.Id,
            "titulo": self.Titulo,
            "descricao": self.Descricao,
            "tipo": self.Tipo,
            "conteudo": self.Conteudo,
            "icone": self.Icone,
            "ordem": self.Ordem,
            "created_at": self._iso(self.CriadoEm),
            "updated_at": self._iso(self.AtualizadoEm),
        }


class LogAuditoriaRoteiro(db.Model):
    __tablename__ = "Tb_Docs_LogAuditoriaRoteiros"

    Id = db.Column("Id", db.Integer, primary_key=True, autoincrement=True)
    RoteiroId = db.Column("RoteiroId", db.Integer, db.ForeignKey("Tb_Docs_Roteiros.Id"), nullable=False)
    UsuarioId = db.Column("UsuarioId", db.Integer, nullable=False)
    NomeUsuario = db.Column("NomeUsuario", db.String(100), nullable=False)
    Acao = db.Column("Acao", db.String(50), nullable=False)
    RegistradoEm = db.Column("RegistradoEm", db.TIMESTAMP, nullable=False, default=datetime.utcnow)

    Roteiro = db.relationship("Roteiro", back_populates="LogsAuditoria")

    id = synonym("Id")
    roteiro_id = synonym("RoteiroId")
    user_id = synonym("UsuarioId")
    user_name = synonym("NomeUsuario")
    action = synonym("Acao")
    timestamp = synonym("RegistradoEm")
    roteiro = synonym("Roteiro")

    def __repr__(self):
        return f"<LogAuditoriaRoteiro {self.Id} - Acao: {self.Acao} por {self.NomeUsuario}>"


BugReport = ReporteBug
IAFeedback = FeedbackIA
DocumentAccess = AcessoDocumento
SearchLog = LogBusca
MetaTagCategoria = CategoriaTagMeta
MetaTag = TagMeta
MetaObjetoRelTag = RelacaoObjetoTagMeta
Evaluation = AvaliacaoDocumento
RoteiroAuditLog = LogAuditoriaRoteiro
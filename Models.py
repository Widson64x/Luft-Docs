# models.py
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.sql import func
from datetime import datetime

db = SQLAlchemy()

permissoes_grupos = db.Table('Lft_Tb_Perm_Rel_Grupos',
    db.Column('permissao_id', db.Integer, db.ForeignKey('Lft_Tb_Perm_Permissoes.id'), primary_key=True),
    db.Column('grupo_id', db.Integer, db.ForeignKey('Lft_Tb_Perm_Grupos.id'), primary_key=True)
)

permissoes_usuarios = db.Table('Lft_Tb_Perm_Rel_Usuarios',
    db.Column('permissao_id', db.Integer, db.ForeignKey('Lft_Tb_Perm_Permissoes.id'), primary_key=True),
    db.Column('usuario_id', db.Integer, db.ForeignKey('Lft_Tb_Perm_Usuarios.id'), primary_key=True)
)

# Tabela de associação para o relacionamento N:N entre Roteiros e Módulos
roteiros_modulos = db.Table('Lft_Tb_Doc_Rel_RoteirosModulos',
    db.Column('roteiro_id', db.Integer, db.ForeignKey('Lft_Tb_Doc_Roteiros.id'), primary_key=True),
    db.Column('modulo_id', db.String(100), db.ForeignKey('Lft_Tb_Doc_Modulos.id'), primary_key=True)
)

class Permissao(db.Model):
    __tablename__ = 'Lft_Tb_Perm_Permissoes'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column('id_permissao', db.String(100), unique=True, nullable=False)
    descricao = db.Column(db.String(255), nullable=True)

    grupos = db.relationship('Grupo', secondary=permissoes_grupos, lazy='subquery',
                             back_populates='permissoes')
    usuarios = db.relationship('Usuario', secondary=permissoes_usuarios, lazy='subquery',
                               back_populates='permissoes')

    def __repr__(self):
        return f'<Permissao {self.nome}>'

class Grupo(db.Model):
    __tablename__ = 'Lft_Tb_Perm_Grupos'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column('nome_grupo', db.String(100), unique=True, nullable=False)
    
    permissoes = db.relationship('Permissao', secondary=permissoes_grupos, lazy='subquery',
                                 back_populates='grupos')

    def __repr__(self):
        return f'<Grupo {self.nome}>'

class Usuario(db.Model):
    __tablename__ = 'Lft_Tb_Perm_Usuarios'
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column('nome_usuario', db.String(100), unique=True, nullable=False)
    
    # O 'back_populates' agora aponta para 'usuarios', que é o nome correto 
    # do relacionamento na classe Permissao.
    permissoes = db.relationship('Permissao', secondary=permissoes_usuarios, lazy='subquery',
                                 back_populates='usuarios')

    def __repr__(self):
        return f'<Usuario {self.nome}>'
    
class BugReport(db.Model):
    """
    Representa um registro de bug ou sugestão enviado por um usuário.
    Mapeia para a tabela Lft_Tb_Fbk_BugReports.
    """
    __tablename__ = 'Lft_Tb_Fbk_BugReports'
    
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # Mantido como Integer para corresponder ao seu schema original.
    user_id = db.Column(db.Integer, nullable=False)
    report_type = db.Column(db.String(50), nullable=False)
    target_entity = db.Column(db.String(100), nullable=True)
    error_category = db.Column(db.String(100), nullable=True)
    description = db.Column(db.Text, nullable=False)
    status = db.Column(db.String(50), nullable=False, default='aberto')
    
    # Define o valor padrão para a data/hora de criação no nível do banco de dados.
    created_at = db.Column(db.TIMESTAMP, server_default=func.now(), nullable=False)

    def __repr__(self):
        return f'<BugReport {self.id} por {self.user_id}>'

class IAFeedback(db.Model):
    """
    Representa um registro de feedback de um usuário para uma resposta da IA.
    Mapeia para a tabela Lft_Tb_Fbk_IA_Feedback.
    """
    #
    # Basicamente, este é o "Livro de Reclamações" da Lia.
    # É aqui que o usuário diz:
    # "Eu perguntei sobre WMS e ela me respondeu sobre o jogo do Palmeiras x LDU."
    # Que cagada do Palmeiras, viraram um 3 x 0 na cagada...
    #
    __tablename__ = 'Lft_Tb_Fbk_IA_Feedback'

    feedback_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    response_id = db.Column(db.String, nullable=False)
    user_id = db.Column(db.String, nullable=False)
    user_question = db.Column(db.Text, nullable=True)
    model_used = db.Column(db.String(100), nullable=True)
    context_sources = db.Column(db.Text, nullable=True) # Armazenado como string JSON
    rating = db.Column(db.Integer, nullable=True) # 1 = 👍, 0 = 👎
    comment = db.Column(db.Text, nullable=True) # "Eu não entendi nada"
    timestamp = db.Column(db.TIMESTAMP, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f'<IAFeedback {self.feedback_id} for response {self.response_id}>'
    
class DocumentAccess(db.Model):
    """ Mapeia para a tabela de log de acesso a documentos. """
    __tablename__ = 'Lft_Tb_Log_DocumentAccess'
    document_id = db.Column(db.String(255), primary_key=True)
    access_count = db.Column(db.Integer, nullable=False, default=1)
    last_access = db.Column(db.TIMESTAMP, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

class SearchLog(db.Model):
    """ Mapeia para a tabela de log de termos de busca. """
    __tablename__ = 'Lft_Tb_Log_SearchLog' # Usando o novo padrão
    query_term = db.Column(db.String(255), primary_key=True)
    search_count = db.Column(db.Integer, nullable=False, default=1)
    last_searched = db.Column(db.TIMESTAMP, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

class Modulo(db.Model):
    __tablename__ = 'Lft_Tb_Doc_Modulos'
    id = db.Column(db.String(100), primary_key=True)
    nome = db.Column(db.String(255), nullable=False)
    descricao = db.Column(db.Text, nullable=True)
    icone = db.Column(db.String(50), nullable=True)
    status = db.Column(db.String(50), nullable=True)
    ultima_edicao_user = db.Column(db.String(100), nullable=True)
    ultima_edicao_data = db.Column(db.String(100), nullable=True)
    pending_edit_user = db.Column(db.String(100), nullable=True)
    pending_edit_data = db.Column(db.String(100), nullable=True)
    current_version = db.Column(db.String(50), nullable=True)
    last_approved_by = db.Column(db.String(100), nullable=True)
    last_approved_on = db.Column(db.String(100), nullable=True)

    palavras_chave = db.relationship('PalavraChave', back_populates='modulo', cascade="all, delete-orphan", lazy='joined')
    edit_history = db.relationship('HistoricoEdicao', back_populates='modulo', cascade="all, delete-orphan", lazy='joined')

    roteiros = db.relationship('Roteiro', secondary=roteiros_modulos,
                               back_populates='modulos', lazy='joined')
      
    # CORREÇÃO APLICADA AQUI: A sintaxe de 'primaryjoin' e 'secondaryjoin' foi corrigida.
    relacionados = db.relationship(
        'Modulo',
        secondary='Lft_Tb_Doc_ModulosRelacionados',
        primaryjoin=lambda: Modulo.id == ModuloRelacionado.modulo_id,
        secondaryjoin=lambda: Modulo.id == ModuloRelacionado.relacionado_id,
        backref='relacionado_por',
        lazy='joined'
    )

    @property
    def pending_edit_info(self):
        """
        Cria um dicionário para manter a compatibilidade com o template
        que espera a estrutura 'pending_edit_info.data'.
        """
        return {'data': self.pending_edit_data}

class PalavraChave(db.Model):
    __tablename__ = 'Lft_Tb_Doc_PalavrasChave'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    modulo_id = db.Column(db.String(100), db.ForeignKey('Lft_Tb_Doc_Modulos.id'), nullable=False)
    palavra = db.Column(db.String(100), nullable=False)
    modulo = db.relationship('Modulo', back_populates='palavras_chave')

class ModuloRelacionado(db.Model):
    __tablename__ = 'Lft_Tb_Doc_ModulosRelacionados'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    modulo_id = db.Column(db.String(100), db.ForeignKey('Lft_Tb_Doc_Modulos.id'), nullable=False)
    relacionado_id = db.Column(db.String(100), db.ForeignKey('Lft_Tb_Doc_Modulos.id'), nullable=False)

class HistoricoEdicao(db.Model):
    __tablename__ = 'Lft_Tb_Doc_HistoricoEdicao'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    modulo_id = db.Column(db.String(100), db.ForeignKey('Lft_Tb_Doc_Modulos.id'), nullable=False)
    event = db.Column(db.String(100))
    version = db.Column(db.String(50))
    editor = db.Column(db.String(100))
    approver = db.Column(db.String(100))
    timestamp = db.Column(db.String(100))
    backup_file_doc = db.Column(db.String(255))
    backup_file_tech = db.Column(db.String(255))
    modulo = db.relationship('Modulo', back_populates='edit_history')

class PalavraGlobal(db.Model):
    __tablename__ = 'Lft_Tb_Doc_PalavrasGlobais'
    palavra = db.Column(db.String(100), primary_key=True)
    descricao = db.Column(db.Text)



# --- MÓDULO DE METADADOS ---
# Este módulo implementa o sistema de dicionário de dados inteligente
# para catalogar e dar funcionalidade às tags de nomenclatura do banco.

class MetaTagCategoria(db.Model):
    """
    Classifica o tipo de cada tag. Ex: 'Projeto', 'Módulo', 'Tipo de Objeto'.
    """
    __tablename__ = 'Lft_Tb_Meta_TagCategorias'
    
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), unique=True, nullable=False)
    descricao = db.Column(db.Text, nullable=True)

    # Relacionamento um-para-muitos: Uma categoria pode ter várias tags.
    tags = db.relationship('MetaTag', back_populates='categoria', cascade="all, delete-orphan", lazy='joined')

    def __repr__(self):
        return f'<MetaTagCategoria {self.nome}>'

class MetaTag(db.Model):
    """
    Armazena cada tag (ex: 'Lft', 'Doc', 'Perm') e sua descrição.
    """
    __tablename__ = 'Lft_Tb_Meta_Tags'
    
    id = db.Column(db.Integer, primary_key=True)
    tag = db.Column(db.String(50), unique=True, nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    
    # Chave estrangeira para a categoria da tag.
    categoria_id = db.Column(db.Integer, db.ForeignKey('Lft_Tb_Meta_TagCategorias.id'), nullable=False)

    # Relacionamento muitos-para-um: Muitas tags pertencem a uma categoria.
    categoria = db.relationship('MetaTagCategoria', back_populates='tags')
    
    # Relacionamento um-para-muitos com a tabela de associação.
    objetos_associados = db.relationship('MetaObjetoRelTag', back_populates='tag', cascade="all, delete-orphan")

    def __repr__(self):
        return f'<MetaTag {self.tag}>'

class MetaObjetoRelTag(db.Model):
    """
    Tabela de associação que liga um objeto do banco de dados (pelo seu nome)
    a uma ou mais tags de metadados.
    """
    __tablename__ = 'Lft_Tb_Meta_Rel_ObjetoTag'
    
    id = db.Column(db.Integer, primary_key=True)
    # Armazena o nome da tabela/objeto como string. Ex: 'Lft_Tb_Perm_Usuarios'
    nome_objeto = db.Column(db.String(255), nullable=False)
    tipo_objeto = db.Column(db.String(50), nullable=False, default='TABLE')
    
    # Chave estrangeira para a tag.
    tag_id = db.Column(db.Integer, db.ForeignKey('Lft_Tb_Meta_Tags.id'), nullable=False)

    # Relacionamento muitos-para-um com a tag.
    tag = db.relationship('MetaTag', back_populates='objetos_associados')

    def __repr__(self):
        # O 'repr' mostra a relação de forma clara para debugging.
        tag_repr = self.tag.tag if self.tag else 'N/A'
        return f'<MetaObjetoRelTag Objeto:{self.nome_objeto} -> Tag:{tag_repr}>'
    

class Evaluation(db.Model):
    __tablename__ = 'Lft_Tb_Fbk_DocumentEvaluation'
    id = db.Column(db.Integer, primary_key=True)
    document_id = db.Column(db.String(100), db.ForeignKey('Lft_Tb_Doc_Modulos.id')) 
    rating = db.Column(db.Integer)
    feedback = db.Column(db.Text)
    suggestions = db.Column(db.Text)
    techos = db.Column(db.Text)
    changes = db.Column(db.Text)

    def __init__(self, document_id, rating, feedback, suggestions, techos, changes):
        self.document_id = document_id
        self.rating = rating
        self.feedback = feedback
        self.suggestions = suggestions
        self.techos = techos
        self.changes = changes


class Roteiro(db.Model):
    __tablename__ = 'Lft_Tb_Doc_Roteiros'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    titulo = db.Column(db.String(255), nullable=False)
    descricao = db.Column(db.Text, nullable=True)
    tipo = db.Column(db.String(50), nullable=False, default='link')
    conteudo = db.Column(db.Text, nullable=False)
    icone = db.Column(db.String(50), nullable=True, default='bi-play-circle')
    ordem = db.Column(db.Integer, default=0)

    # existem no SQLite + triggers; manter no model pra mapear:
    created_at = db.Column(db.DateTime(timezone=True))
    updated_at = db.Column(db.DateTime(timezone=True))

    modulos = db.relationship(
        'Modulo', secondary=roteiros_modulos, back_populates='roteiros', lazy='subquery'
    )

    audit_logs = db.relationship(
        'RoteiroAuditLog', back_populates='roteiro', cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f'<Roteiro {self.id}: {self.titulo}>'

    @staticmethod
    def _iso(dt):
        """Converte datetime ou string do SQLite em ISO-8601 (UTC) para o front."""
        if not dt:
            return None
        if isinstance(dt, str):
            # SQLite geralmente retorna 'YYYY-MM-DD HH:MM:SS'
            return dt.replace(' ', 'T') + 'Z'
        # datetime -> ISO, normalizando 'Z' se UTC
        iso = dt.isoformat()
        return iso.replace('+00:00', 'Z')

    def to_dict(self):
        return {
            'id': self.id,
            'titulo': self.titulo,
            'descricao': self.descricao,
            'tipo': self.tipo,
            'conteudo': self.conteudo,
            'icone': self.icone,
            'ordem': self.ordem,
            'created_at': self._iso(self.created_at),
            'updated_at': self._iso(self.updated_at),
        }
    
class RoteiroAuditLog(db.Model):
    """
    Tabela de log para registrar criações e edições na tabela de Roteiros.
    """
    __tablename__ = 'Lft_Tb_Log_RoteirosAudit'
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    # Chave estrangeira para o roteiro que foi modificado
    roteiro_id = db.Column(db.Integer, db.ForeignKey('Lft_Tb_Doc_Roteiros.id'), nullable=False)
    # Informações do usuário que realizou a ação
    user_id = db.Column(db.Integer, nullable=False)
    user_name = db.Column(db.String(100), nullable=False)
    # Ação realizada ('CREATE' ou 'UPDATE')
    action = db.Column(db.String(50), nullable=False)
    # Data e hora da ação
    timestamp = db.Column(db.TIMESTAMP, nullable=False, default=datetime.utcnow)
    roteiro = db.relationship('Roteiro', back_populates='audit_logs')

    def __repr__(self):
        return f'<RoteiroAuditLog {self.id} - Ação: {self.action} por {self.user_name}>'
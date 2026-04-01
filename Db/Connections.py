"""
Gerenciamento de conexões de banco de dados do LuftDocs.

Dois bancos são suportados via SQLALCHEMY_BINDS:

  BIND_PG  (None / padrão)  → PostgreSQL
      Todas as tabelas de conteúdo do LuftDocs:
      módulos, submódulos, roteiros, logs de busca, feedback, etc.

  BIND_SQL  ("sqlserver")    → SQL Server
      Tabelas do sistema intec.dbo.*:
        - Tb_Permissao, Tb_PermissaoGrupo, Tb_PermissaoUsuario, Tb_LogAcesso
        - usuario, usuariogrupo  (lookup de auth)

Uso nos Models:

    from Db.Connections import db, BIND_SQL, BIND_PG

    class MinhaTabela(db.Model):
        __bind_key__ = BIND_SQL   # → roteado para o SQL Server
        ...

    class OutraTabela(db.Model):
        # sem __bind_key__  → roteado para o PostgreSQL (default)
        ...

Inicialização no App:

    from Db.Connections import db
    app.config["SQLALCHEMY_DATABASE_URI"]  = cfg.DATABASE_URL     # PostgreSQL
    app.config["SQLALCHEMY_BINDS"]         = {"sqlserver": cfg.SQLSERVER_URL}
    db.init_app(app)
"""
from flask_sqlalchemy import SQLAlchemy

# -----------------------------------------------------------------------
# Instância única — o Flask-SQLAlchemy roteia para o banco correto
# automaticamente com base em __bind_key__ definido no modelo.
# -----------------------------------------------------------------------
db = SQLAlchemy()

# Nome do bind para o SQL Server
BIND_SQL: str = "sqlserver"

# Nome do bind para o PostgreSQL (None = SQLALCHEMY_DATABASE_URI padrão)
BIND_PG = None

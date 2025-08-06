-- Tabela para armazenar metadados e descrições das tabelas do sistema.
-- O objetivo é ter uma fonte única de verdade sobre a estrutura e propósito de cada tabela.
CREATE TABLE IF NOT EXISTS Lft_Sys_SchemaTags (
    -- O nome completo da tabela (ex: Lft_Tb_Doc_HistoricoEdicao). Chave primária.
    table_name TEXT PRIMARY KEY NOT NULL,

    -- O prefixo principal do sistema (ex: 'Lft').
    tag_prefix TEXT,

    -- O tipo de objeto (ex: 'Tb' para Tabela).
    tag_type TEXT,

    -- O módulo ou contexto funcional da tabela (ex: 'Doc', 'Fbk', 'Perm').
    tag_module TEXT,

    -- O nome específico da entidade da tabela (ex: 'PalavrasChave', 'Usuarios').
    tag_entity TEXT,

    -- Uma descrição clara e legível sobre o propósito e uso da tabela.
    -- Esta coluna é preenchida manualmente.
    description TEXT,

    -- Data e hora da última vez que o script de sincronização atualizou este registro.
    last_sync_utc TEXT
);


-- Tabela para os prefixos base do sistema.
CREATE TABLE IF NOT EXISTS Lft_Sys_TagsBase (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome_tag TEXT NOT NULL UNIQUE,
    descricao TEXT
);

-- Tabela para os componentes de nome: Tipos (Tb) e Operações (Doc, Fbk, etc).
CREATE TABLE IF NOT EXISTS Lft_Sys_TagsComponente (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome_tag TEXT NOT NULL UNIQUE,
    -- Categoria para diferenciar os tipos de tag ('Tipo', 'Operacao')
    categoria TEXT NOT NULL,
    descricao TEXT
);

-- Tabela central que relaciona as tabelas do schema com suas tags através de IDs.
CREATE TABLE IF NOT EXISTS Lft_Sys_Relacionamentos (
    -- Nome completo da tabela do banco de dados.
    nome_tabela TEXT PRIMARY KEY NOT NULL,
    
    -- Chaves estrangeiras para as tabelas de tags.
    id_tag_base INTEGER,
    id_tag_tipo INTEGER,
    id_tag_operacao INTEGER,
    
    -- O nome da entidade específica da tabela (ex: 'PalavrasChave').
    nome_entidade TEXT,
    
    -- Descrição do propósito da tabela (preenchimento manual).
    descricao TEXT,
    
    -- Data da última sincronização.
    last_sync_utc TEXT,

    FOREIGN KEY (id_tag_base) REFERENCES Lft_Sys_TagsBase (id),
    FOREIGN KEY (id_tag_tipo) REFERENCES Lft_Sys_TagsComponente (id),
    FOREIGN KEY (id_tag_operacao) REFERENCES Lft_Sys_TagsComponente (id)
);


-- Descrevendo uma tag de operação
UPDATE Lft_Sys_TagsComponente
SET descricao = 'Módulo de Permissões: gerencia usuários, grupos e acessos.'
WHERE nome_tag = 'Perm';

-- Descrevendo uma tag de tipo
UPDATE Lft_Sys_TagsComponente
SET descricao = 'Objeto do tipo Tabela, armazena dados de forma estruturada.'
WHERE nome_tag = 'Tb' AND categoria = 'Tipo';

UPDATE Lft_Sys_Relacionamentos
SET descricao = 'Armazena a relação entre usuários e os grupos aos quais pertencem.'
WHERE nome_tabela = 'Lft_Tb_Perm_Rel_Usuarios';


SELECT
    r.nome_tabela,
    tc.descricao AS descricao_do_modulo,
    r.descricao AS descricao_da_tabela
FROM
    Lft_Sys_Relacionamentos r
JOIN
    Lft_Sys_TagsComponente tc ON r.id_tag_operacao = tc.id
WHERE
    tc.nome_tag = 'Perm';


-- Adiciona uma coluna para marcar tabelas como favoritas na tabela de relacionamentos.
-- O 'DEFAULT 0' significa que nenhuma tabela é favorita por padrão.
ALTER TABLE Lft_Sys_Relacionamentos ADD COLUMN is_favorited INTEGER DEFAULT 0;
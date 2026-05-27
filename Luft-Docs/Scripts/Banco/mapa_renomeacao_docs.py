from __future__ import annotations

ColunaOrigem = str | tuple[str, ...]


MAPA_TABELAS: dict[str, str] = {
    "Lft_Tb_Perm_Permissoes": "Tb_Docs_Permissoes",
    "Lft_Tb_Perm_Grupos": "Tb_Docs_GruposPermissao",
    "Lft_Tb_Perm_Usuarios": "Tb_Docs_UsuariosPermissao",
    "Lft_Tb_Perm_Rel_Grupos": "Tb_Docs_RelacaoPermissoesGrupos",
    "Lft_Tb_Perm_Rel_Usuarios": "Tb_Docs_RelacaoPermissoesUsuarios",
    "Lft_Tb_Fbk_BugReports": "Tb_Docs_ReportesBug",
    "Lft_Tb_Fbk_IA_Feedback": "Tb_Docs_FeedbackIA",
    "Lft_Tb_Log_DocumentAccess": "Tb_Docs_LogAcessosDocumentos",
    "Lft_Tb_Log_SearchLog": "Tb_Docs_LogBuscas",
    "Lft_Tb_Doc_Modulos": "Tb_Docs_Modulos",
    "Lft_Tb_Doc_PalavrasChave": "Tb_Docs_PalavrasChave",
    "Lft_Tb_Doc_ModulosRelacionados": "Tb_Docs_ModulosRelacionados",
    "Lft_Tb_Doc_HistoricoEdicao": "Tb_Docs_HistoricoEdicoes",
    "Lft_Tb_Doc_PalavrasGlobais": "Tb_Docs_PalavrasGlobais",
    "Lft_Tb_Meta_TagCategorias": "Tb_Docs_CategoriasTagsMeta",
    "Lft_Tb_Meta_Tags": "Tb_Docs_TagsMeta",
    "Lft_Tb_Meta_Rel_ObjetoTag": "Tb_Docs_RelacaoObjetosTagsMeta",
    "Lft_Tb_Fbk_DocumentEvaluation": "Tb_Docs_AvaliacoesDocumentos",
    "Lft_Tb_Doc_Roteiros": "Tb_Docs_Roteiros",
    "Lft_Tb_Doc_Rel_RoteirosModulos": "Tb_Docs_RelacaoRoteirosModulos",
    "Lft_Tb_Log_RoteirosAudit": "Tb_Docs_LogAuditoriaRoteiros",
}


MAPA_COLUNAS: dict[str, dict[ColunaOrigem, str]] = {
    "Tb_Docs_Permissoes": {
        ("id",): "Id",
        ("id_permissao", "nome_permissao"): "NomePermissao",
        ("descricao",): "Descricao",
    },
    "Tb_Docs_GruposPermissao": {
        ("id",): "Id",
        ("nome_grupo",): "NomeGrupo",
    },
    "Tb_Docs_UsuariosPermissao": {
        ("id",): "Id",
        ("nome_usuario",): "NomeUsuario",
    },
    "Tb_Docs_RelacaoPermissoesGrupos": {
        ("permissao_id",): "PermissaoId",
        ("grupo_id",): "GrupoId",
    },
    "Tb_Docs_RelacaoPermissoesUsuarios": {
        ("permissao_id",): "PermissaoId",
        ("usuario_id",): "UsuarioId",
    },
    "Tb_Docs_ReportesBug": {
        ("id",): "Id",
        ("user_id", "usuario_id"): "UsuarioId",
        ("report_type", "tipo_reporte"): "TipoReporte",
        ("target_entity", "entidade_alvo"): "EntidadeAlvo",
        ("error_category", "categoria_erro"): "CategoriaErro",
        ("description", "descricao"): "Descricao",
        ("status",): "Status",
        ("created_at", "criado_em"): "CriadoEm",
    },
    "Tb_Docs_FeedbackIA": {
        ("feedback_id", "id"): "Id",
        ("response_id", "resposta_id"): "RespostaId",
        ("user_id", "usuario_id"): "UsuarioId",
        ("user_question", "pergunta_usuario"): "PerguntaUsuario",
        ("model_used", "modelo_utilizado"): "ModeloUtilizado",
        ("context_sources", "fontes_contexto"): "FontesContexto",
        ("rating", "avaliacao"): "Avaliacao",
        ("comment", "comentario"): "Comentario",
        ("timestamp", "registrado_em"): "RegistradoEm",
    },
    "Tb_Docs_LogAcessosDocumentos": {
        ("document_id", "documento_id"): "DocumentoId",
        ("access_count", "quantidade_acessos"): "QuantidadeAcessos",
        ("last_access", "ultimo_acesso_em"): "UltimoAcessoEm",
    },
    "Tb_Docs_LogBuscas": {
        ("query_term", "termo_busca"): "TermoBusca",
        ("search_count", "quantidade_buscas"): "QuantidadeBuscas",
        ("last_searched", "ultima_busca_em"): "UltimaBuscaEm",
    },
    "Tb_Docs_Modulos": {
        ("id",): "Id",
        ("nome",): "Nome",
        ("descricao",): "Descricao",
        ("icone",): "Icone",
        ("status",): "Status",
        ("ultima_edicao_user", "usuario_ultima_edicao"): "UsuarioUltimaEdicao",
        ("ultima_edicao_data", "data_ultima_edicao"): "DataUltimaEdicao",
        ("pending_edit_user", "usuario_edicao_pendente"): "UsuarioEdicaoPendente",
        ("pending_edit_data", "data_edicao_pendente"): "DataEdicaoPendente",
        ("current_version", "versao_atual"): "VersaoAtual",
        ("last_approved_by", "aprovado_por"): "AprovadoPor",
        ("last_approved_on", "aprovado_em"): "AprovadoEm",
    },
    "Tb_Docs_PalavrasChave": {
        ("id",): "Id",
        ("modulo_id",): "ModuloId",
        ("palavra",): "Palavra",
    },
    "Tb_Docs_ModulosRelacionados": {
        ("id",): "Id",
        ("modulo_id",): "ModuloId",
        ("relacionado_id",): "RelacionadoId",
    },
    "Tb_Docs_HistoricoEdicoes": {
        ("id",): "Id",
        ("modulo_id",): "ModuloId",
        ("event", "evento"): "Evento",
        ("version", "versao"): "Versao",
        ("editor",): "Editor",
        ("approver", "aprovador"): "Aprovador",
        ("timestamp", "registrado_em"): "RegistradoEm",
        ("backup_file_doc", "arquivo_backup_documentacao"): "ArquivoBackupDocumentacao",
        ("backup_file_tech", "arquivo_backup_documentacao_tecnica"): "ArquivoBackupDocumentacaoTecnica",
    },
    "Tb_Docs_PalavrasGlobais": {
        ("palavra",): "Palavra",
        ("descricao",): "Descricao",
    },
    "Tb_Docs_CategoriasTagsMeta": {
        ("id",): "Id",
        ("nome",): "Nome",
        ("descricao",): "Descricao",
    },
    "Tb_Docs_TagsMeta": {
        ("id",): "Id",
        ("tag",): "Tag",
        ("descricao",): "Descricao",
        ("categoria_id",): "CategoriaId",
    },
    "Tb_Docs_RelacaoObjetosTagsMeta": {
        ("id",): "Id",
        ("nome_objeto",): "NomeObjeto",
        ("tipo_objeto",): "TipoObjeto",
        ("tag_id",): "TagId",
    },
    "Tb_Docs_AvaliacoesDocumentos": {
        ("id",): "Id",
        ("document_id", "documento_id"): "DocumentoId",
        ("rating", "avaliacao"): "Avaliacao",
        ("feedback", "comentario"): "Comentario",
        ("suggestions", "sugestoes"): "Sugestoes",
        ("techos", "trechos"): "Trechos",
        ("changes", "mudancas_solicitadas"): "MudancasSolicitadas",
    },
    "Tb_Docs_Roteiros": {
        ("id",): "Id",
        ("titulo",): "Titulo",
        ("descricao",): "Descricao",
        ("tipo",): "Tipo",
        ("conteudo",): "Conteudo",
        ("icone",): "Icone",
        ("ordem",): "Ordem",
        ("created_at", "criado_em"): "CriadoEm",
        ("updated_at", "atualizado_em"): "AtualizadoEm",
    },
    "Tb_Docs_RelacaoRoteirosModulos": {
        ("roteiro_id",): "RoteiroId",
        ("modulo_id",): "ModuloId",
    },
    "Tb_Docs_LogAuditoriaRoteiros": {
        ("id",): "Id",
        ("roteiro_id",): "RoteiroId",
        ("user_id", "usuario_id"): "UsuarioId",
        ("user_name", "nome_usuario"): "NomeUsuario",
        ("action", "acao"): "Acao",
        ("timestamp", "registrado_em"): "RegistradoEm",
    },
}


def obter_mapa_reverso() -> tuple[dict[str, str], dict[str, dict[str, str]]]:
    mapa_tabelas_reverso = {destino: origem for origem, destino in MAPA_TABELAS.items()}
    mapa_colunas_reverso: dict[str, dict[str, str]] = {}

    for tabela, colunas in MAPA_COLUNAS.items():
        mapa_colunas_reverso[tabela] = {}
        for origem, destino in colunas.items():
            if isinstance(origem, tuple):
                mapa_colunas_reverso[tabela][destino] = origem[0]
            else:
                mapa_colunas_reverso[tabela][destino] = origem

    return mapa_tabelas_reverso, mapa_colunas_reverso
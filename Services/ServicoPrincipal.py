from __future__ import annotations

from typing import Any

from flask import current_app, session

from Models import ReporteBug, db
from Utils.ConfiguracaoPermissoes import MODULOS_RESTRITOS, MODULOS_TECNICOS_VISIVEIS
from Utils.auth.Autenticacao import AutenticarRequisicaoInicial, EncerrarSessaoUsuario
from Utils.data.UtilitariosModulo import CarregarModulosAprovados


class ServicoPrincipal:
    """Centraliza a regra de negocio das rotas principais da aplicacao."""

    def obterPermissoesGlobais(self) -> dict[str, bool]:
        """Retorna as permissoes globais utilizadas pelos templates base."""
        permissoes_usuario = session.get("permissions", {})
        return {
            "can_view_tecnico": permissoes_usuario.get("can_view_tecnico", False),
            "can_view_tools_in_development": permissoes_usuario.get(
                "can_view_tools_in_development", False
            ),
        }

    def autenticarRequisicaoInicial(self) -> Any:
        """Executa o fluxo inicial de autenticacao da aplicacao."""
        return AutenticarRequisicaoInicial()

    def obterContextoPaginaInicial(self) -> dict[str, Any]:
        """Monta o contexto minimo necessario para a pagina inicial."""
        permissoes_usuario = session.get("permissions", {})
        return {
            "can_access_editor": permissoes_usuario.get("can_access_editor", False),
            "can_access_permissions_menu": permissoes_usuario.get(
                "can_access_permissions_menu", False
            ),
            "can_create_modules": permissoes_usuario.get("can_create_modules", False),
            "can_view_tools_in_development": permissoes_usuario.get(
                "can_view_tools_in_development", False
            ),
            "menus": [],
        }

    def obterContextoMapaConhecimento(self) -> dict[str, Any]:
        """Monta os dados exibidos no mapa de conhecimento."""
        permissoes_usuario = session.get("permissions", {})
        pode_ver_tecnico = permissoes_usuario.get("can_view_tecnico", False)
        pode_acessar_editor = permissoes_usuario.get("can_access_editor", False)
        pode_acessar_menu_permissoes = permissoes_usuario.get(
            "can_access_permissions_menu", False
        )
        pode_ver_restritos = permissoes_usuario.get("can_see_restricted_module", False)

        modulos_aprovados, _ = CarregarModulosAprovados()
        modulos_visiveis = []
        for modulo in modulos_aprovados:
            if modulo.get("id") in MODULOS_RESTRITOS and not pode_ver_restritos:
                continue
            modulos_visiveis.append(modulo)

        identificadores_visiveis = {modulo["id"] for modulo in modulos_visiveis}
        for modulo in modulos_visiveis:
            relacionados = modulo.get("relacionados") or []
            modulo["relacionados_visiveis"] = [
                identificador
                for identificador in relacionados
                if identificador in identificadores_visiveis
            ]
            modulo["show_tecnico_button"] = (
                modulo["id"] in MODULOS_TECNICOS_VISIVEIS or pode_ver_tecnico
            )

        return {
            "modulos": modulos_visiveis,
            "can_access_editor": pode_acessar_editor,
            "can_access_permissions_menu": pode_acessar_menu_permissoes,
            "can_view_tecnico": pode_ver_tecnico,
        }

    def registrarReporte(
        self, identificador_usuario: Any, dados_reporte: dict[str, Any]
    ) -> tuple[dict[str, Any], int]:
        """Valida e persiste um reporte de problema ou sugestao."""
        if not identificador_usuario:
            return {
                "success": False,
                "message": "Sessao invalida. Por favor, faca login novamente.",
            }, 403

        tipo_reporte = str(dados_reporte.get("report_type", "")).strip()
        entidade_alvo = str(dados_reporte.get("target_entity", "") or "").strip() or None
        descricao = str(dados_reporte.get("description", "") or "").strip()
        categoria_erro = str(dados_reporte.get("error_category", "") or "").strip() or None

        if tipo_reporte not in {"tela", "modulo", "geral", "sugestao"}:
            return {
                "success": False,
                "message": "O tipo de feedback e invalido.",
            }, 400

        if tipo_reporte in {"tela", "modulo"} and not entidade_alvo:
            return {
                "success": False,
                "message": "Para este tipo de feedback, e necessario especificar o alvo.",
            }, 400

        if tipo_reporte in {"tela", "modulo"} and not categoria_erro:
            return {
                "success": False,
                "message": "Por favor, selecione a categoria do problema.",
            }, 400

        if len(descricao) < 10:
            return {
                "success": False,
                "message": "A descricao e obrigatoria e deve conter pelo menos 10 caracteres.",
            }, 400

        try:
            novo_reporte = ReporteBug(
                UsuarioId=identificador_usuario,
                TipoReporte=tipo_reporte,
                EntidadeAlvo=entidade_alvo,
                CategoriaErro=categoria_erro,
                Descricao=descricao,
            )
            db.session.add(novo_reporte)
            db.session.commit()
            return {
                "success": True,
                "message": "Feedback enviado com sucesso. Agradecemos sua colaboracao.",
            }, 201
        except Exception as erro:
            db.session.rollback()
            current_app.logger.error(
                "Erro ao inserir bug report para user_id %s: %s",
                identificador_usuario,
                erro,
            )
            return {
                "success": False,
                "message": "Ocorreu um erro interno ao salvar seu feedback. Tente novamente mais tarde.",
            }, 500

    def encerrarSessaoAtual(self) -> None:
        """Executa o fluxo de encerramento da sessao do usuario atual."""
        EncerrarSessaoUsuario()
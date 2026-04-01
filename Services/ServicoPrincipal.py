from __future__ import annotations

from typing import Any

from flask import current_app

from Db.Connections import obterSessaoPostgres
from Models import ReporteBug
from Services.PermissaoService import ChavesPermissao, PermissaoService
from Utils.auth.Autenticacao import AutenticarRequisicaoInicial, EncerrarSessaoUsuario
from Utils.data.UtilitariosModulo import (
    CarregarModulosAprovados,
    FiltrarModulosRestritos,
    ModuloPossuiDocumentacaoTecnica,
)


class ServicoPrincipal:
    """Centraliza a regra de negocio das rotas principais da aplicacao."""

    def obterPermissoesGlobais(self) -> dict[str, bool]:
        """Expõe helpers globais de autorização para os templates Jinja."""
        return {
            "tem_permissao": PermissaoService.usuarioPossuiPermissao,
        }

    def autenticarRequisicaoInicial(self) -> Any:
        """Executa o fluxo inicial de autenticacao da aplicacao."""
        return AutenticarRequisicaoInicial()

    def obterContextoPaginaInicial(self) -> dict[str, Any]:
        """Monta o contexto minimo necessario para a pagina inicial."""
        return {
            "menus": [],
        }

    def obterContextoMapaConhecimento(self) -> dict[str, Any]:
        """Monta os dados exibidos no mapa de conhecimento."""
        pode_ver_tecnico = PermissaoService.usuarioPossuiPermissao(
            ChavesPermissao.VISUALIZAR_MODULOS_TECNICOS
        )
        pode_ver_restritos = PermissaoService.usuarioPossuiPermissao(
            ChavesPermissao.VISUALIZAR_MODULOS_RESTRITOS
        )

        modulos_aprovados, _ = CarregarModulosAprovados()
        modulos_visiveis = FiltrarModulosRestritos(
            modulos_aprovados,
            pode_ver_restritos,
        )

        identificadores_visiveis = {modulo["id"] for modulo in modulos_visiveis}
        for modulo in modulos_visiveis:
            relacionados = modulo.get("relacionados") or []
            modulo["relacionados_visiveis"] = [
                identificador
                for identificador in relacionados
                if identificador in identificadores_visiveis
            ]
            modulo["show_tecnico_button"] = (
                pode_ver_tecnico
                and ModuloPossuiDocumentacaoTecnica(modulo["id"])
            )

        return {
            "modulos": modulos_visiveis,
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

        sessao = obterSessaoPostgres()
        try:
            novo_reporte = ReporteBug(
                UsuarioId=identificador_usuario,
                TipoReporte=tipo_reporte,
                EntidadeAlvo=entidade_alvo,
                CategoriaErro=categoria_erro,
                Descricao=descricao,
            )
            sessao.add(novo_reporte)
            sessao.commit()
            return {
                "success": True,
                "message": "Feedback enviado com sucesso. Agradecemos sua colaboracao.",
            }, 201
        except Exception as erro:
            sessao.rollback()
            current_app.logger.error(
                "Erro ao inserir bug report para user_id %s: %s",
                identificador_usuario,
                erro,
            )
            return {
                "success": False,
                "message": "Ocorreu um erro interno ao salvar seu feedback. Tente novamente mais tarde.",
            }, 500
        finally:
            sessao.close()

    def encerrarSessaoAtual(self) -> None:
        """Executa o fluxo de encerramento da sessao do usuario atual."""
        EncerrarSessaoUsuario()
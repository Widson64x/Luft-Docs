from __future__ import annotations

from flask import session

from Db.Connections import obterSessaoPostgres
from Models import LogAuditoriaRoteiro, Modulo, Roteiro
from Services.PermissaoService import PermissaoService


class ServicoRoteiros:
    """Centraliza a regra de negocio das rotas de roteiros."""

    def criarRoteiro(self, dados: dict[str, object]) -> tuple[dict[str, object], int]:
        """Cria um roteiro e registra a auditoria da operacao."""
        resposta_permissao = self._validarPermissaoEdicao()
        if resposta_permissao is not None:
            return resposta_permissao

        if not dados.get("titulo") or not dados.get("conteudo"):
            return self._respostaErro(
                "Titulo e conteudo sao obrigatorios.", 400
            )

        sessao = obterSessaoPostgres()
        novo_roteiro = Roteiro(
            Titulo=dados["titulo"],
            Tipo=dados.get("tipo", "link"),
            Conteudo=dados["conteudo"],
            Icone=dados.get("icone"),
            Ordem=dados.get("ordem", 0),
            Descricao=dados.get("descricao"),
        )
        try:
            sessao.add(novo_roteiro)
            sessao.add(
                LogAuditoriaRoteiro(
                    Roteiro=novo_roteiro,
                    UsuarioId=session.get("user_id"),
                    NomeUsuario=session.get("user_name"),
                    Acao="CREATE",
                )
            )
            sessao.commit()
            sessao.refresh(novo_roteiro)
            return (
                {
                    "status": "success",
                    "message": "Roteiro criado com sucesso!",
                    "roteiro": self.serializarRoteiro(novo_roteiro, incluir_modulos=True),
                },
                201,
            )
        except Exception:
            sessao.rollback()
            raise
        finally:
            sessao.close()

    def vincularRoteiroAModulo(
        self, dados: dict[str, object]
    ) -> tuple[dict[str, object], int]:
        """Vincula um roteiro existente a uma lista de modulos."""
        resposta_permissao = self._validarPermissaoEdicao(
            "Acesso negado. Voce nao tem permissao para vincular roteiros."
        )
        if resposta_permissao is not None:
            return resposta_permissao

        roteiro_id = dados.get("roteiro_id")
        modulo_ids = dados.get("modulo_ids")
        if not roteiro_id or not modulo_ids:
            return self._respostaErro(
                "ID do roteiro e lista de modulos sao obrigatorios.", 400
            )

        sessao = obterSessaoPostgres()
        try:
            roteiro = sessao.get(Roteiro, roteiro_id)
            if roteiro is None:
                return self._respostaErro("Roteiro nao encontrado.", 404)

            modulos = sessao.query(Modulo).filter(Modulo.Id.in_(modulo_ids)).all()
            for modulo in modulos:
                if modulo not in roteiro.Modulos:
                    roteiro.Modulos.append(modulo)

            sessao.commit()
            sessao.refresh(roteiro)
            return (
                {
                    "status": "success",
                    "message": f'Roteiro "{roteiro.Titulo}" vinculado a {len(modulos)} modulo(s).',
                    "roteiro": self.serializarRoteiro(roteiro, incluir_modulos=True),
                },
                200,
            )
        except Exception:
            sessao.rollback()
            raise
        finally:
            sessao.close()

    def obterRoteiro(self, roteiro_id: int) -> tuple[dict[str, object], int]:
        """Retorna um roteiro especifico para o frontend."""
        sessao = obterSessaoPostgres()
        try:
            roteiro = sessao.get(Roteiro, roteiro_id)
            if roteiro is None:
                return self._respostaErro("Roteiro nao encontrado.", 404)
            return self.serializarRoteiro(roteiro, incluir_modulos=True), 200
        finally:
            sessao.close()

    def atualizarRoteiro(
        self, roteiro_id: int, dados: dict[str, object]
    ) -> tuple[dict[str, object], int]:
        """Atualiza os dados de um roteiro existente."""
        resposta_permissao = self._validarPermissaoEdicao()
        if resposta_permissao is not None:
            return resposta_permissao

        sessao = obterSessaoPostgres()
        try:
            roteiro = sessao.get(Roteiro, roteiro_id)
            if roteiro is None:
                return self._respostaErro("Roteiro nao encontrado.", 404)

            roteiro.Titulo = dados.get("titulo", roteiro.Titulo)
            roteiro.Descricao = dados.get("descricao", roteiro.Descricao)
            roteiro.Tipo = dados.get("tipo", roteiro.Tipo)
            roteiro.Conteudo = dados.get("conteudo", roteiro.Conteudo)
            roteiro.Icone = dados.get("icone", roteiro.Icone)
            roteiro.Ordem = dados.get("ordem", roteiro.Ordem)

            sessao.add(
                LogAuditoriaRoteiro(
                    RoteiroId=roteiro.Id,
                    UsuarioId=session.get("user_id"),
                    NomeUsuario=session.get("user_name"),
                    Acao="UPDATE",
                )
            )
            sessao.commit()
            sessao.refresh(roteiro)
            return (
                {
                    "status": "success",
                    "message": "Roteiro atualizado com sucesso!",
                    "roteiro": self.serializarRoteiro(roteiro, incluir_modulos=True),
                },
                200,
            )
        except Exception:
            sessao.rollback()
            raise
        finally:
            sessao.close()

    def excluirRoteiro(self, roteiro_id: int) -> tuple[dict[str, object], int]:
        """Exclui um roteiro e registra a auditoria da operacao."""
        resposta_permissao = self._validarPermissaoEdicao(
            "Acesso negado. Voce nao tem permissao para excluir roteiros."
        )
        if resposta_permissao is not None:
            return resposta_permissao

        sessao = obterSessaoPostgres()
        try:
            roteiro = sessao.get(Roteiro, roteiro_id)
            if roteiro is None:
                return self._respostaErro("Roteiro nao encontrado.", 404)

            sessao.add(
                LogAuditoriaRoteiro(
                    RoteiroId=roteiro.Id,
                    UsuarioId=session.get("user_id"),
                    NomeUsuario=session.get("user_name"),
                    Acao="DELETE",
                )
            )
            sessao.delete(roteiro)
            sessao.commit()
            return {"status": "success", "message": "Roteiro excluido com sucesso!"}, 200
        except Exception:
            sessao.rollback()
            raise
        finally:
            sessao.close()

    def serializarRoteiro(
        self, roteiro: Roteiro, incluir_modulos: bool = False
    ) -> dict[str, object]:
        """Serializa o roteiro no formato esperado pelo frontend."""
        dados = roteiro.to_dict()
        if incluir_modulos:
            dados["modulos_vinculados"] = [modulo.Id for modulo in roteiro.Modulos]
        return dados

    def _validarPermissaoEdicao(
        self, mensagem: str = "Acesso negado."
    ) -> tuple[dict[str, object], int] | None:
        if not PermissaoService.usuarioPossuiPermissao("DOCS.ROTEIROS.EDITAR"):
            return self._respostaErro(mensagem, 403)
        return None

    @staticmethod
    def _respostaErro(mensagem: str, codigo: int) -> tuple[dict[str, object], int]:
        return {"status": "error", "message": mensagem}, codigo
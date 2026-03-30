from __future__ import annotations

from flask import session

from Models import Modulo, Roteiro, RoteiroAuditLog, db


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

        novo_roteiro = Roteiro(
            titulo=dados["titulo"],
            tipo=dados.get("tipo", "link"),
            conteudo=dados["conteudo"],
            icone=dados.get("icone"),
            ordem=dados.get("ordem", 0),
            descricao=dados.get("descricao"),
        )
        db.session.add(novo_roteiro)
        db.session.add(
            RoteiroAuditLog(
                roteiro=novo_roteiro,
                user_id=session.get("user_id"),
                user_name=session.get("user_name"),
                action="CREATE",
            )
        )

        db.session.commit()
        db.session.refresh(novo_roteiro)
        return (
            {
                "status": "success",
                "message": "Roteiro criado com sucesso!",
                "roteiro": self.serializarRoteiro(novo_roteiro, incluir_modulos=True),
            },
            201,
        )

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

        roteiro = Roteiro.query.get(roteiro_id)
        if roteiro is None:
            return self._respostaErro("Roteiro nao encontrado.", 404)

        modulos = Modulo.query.filter(Modulo.id.in_(modulo_ids)).all()
        for modulo in modulos:
            if modulo not in roteiro.modulos:
                roteiro.modulos.append(modulo)

        db.session.commit()
        db.session.refresh(roteiro)
        return (
            {
                "status": "success",
                "message": f'Roteiro "{roteiro.titulo}" vinculado a {len(modulos)} modulo(s).',
                "roteiro": self.serializarRoteiro(roteiro, incluir_modulos=True),
            },
            200,
        )

    def obterRoteiro(self, roteiro_id: int) -> tuple[dict[str, object], int]:
        """Retorna um roteiro especifico para o frontend."""
        roteiro = Roteiro.query.get(roteiro_id)
        if roteiro is None:
            return self._respostaErro("Roteiro nao encontrado.", 404)
        return self.serializarRoteiro(roteiro, incluir_modulos=True), 200

    def atualizarRoteiro(
        self, roteiro_id: int, dados: dict[str, object]
    ) -> tuple[dict[str, object], int]:
        """Atualiza os dados de um roteiro existente."""
        resposta_permissao = self._validarPermissaoEdicao()
        if resposta_permissao is not None:
            return resposta_permissao

        roteiro = Roteiro.query.get(roteiro_id)
        if roteiro is None:
            return self._respostaErro("Roteiro nao encontrado.", 404)

        roteiro.titulo = dados.get("titulo", roteiro.titulo)
        roteiro.descricao = dados.get("descricao", roteiro.descricao)
        roteiro.tipo = dados.get("tipo", roteiro.tipo)
        roteiro.conteudo = dados.get("conteudo", roteiro.conteudo)
        roteiro.icone = dados.get("icone", roteiro.icone)
        roteiro.ordem = dados.get("ordem", roteiro.ordem)

        db.session.add(
            RoteiroAuditLog(
                roteiro_id=roteiro.id,
                user_id=session.get("user_id"),
                user_name=session.get("user_name"),
                action="UPDATE",
            )
        )

        db.session.commit()
        db.session.refresh(roteiro)
        return (
            {
                "status": "success",
                "message": "Roteiro atualizado com sucesso!",
                "roteiro": self.serializarRoteiro(roteiro, incluir_modulos=True),
            },
            200,
        )

    def excluirRoteiro(self, roteiro_id: int) -> tuple[dict[str, object], int]:
        """Exclui um roteiro e registra a auditoria da operacao."""
        resposta_permissao = self._validarPermissaoEdicao(
            "Acesso negado. Voce nao tem permissao para excluir roteiros."
        )
        if resposta_permissao is not None:
            return resposta_permissao

        roteiro = Roteiro.query.get(roteiro_id)
        if roteiro is None:
            return self._respostaErro("Roteiro nao encontrado.", 404)

        db.session.add(
            RoteiroAuditLog(
                roteiro_id=roteiro.id,
                user_id=session.get("user_id"),
                user_name=session.get("user_name"),
                action="DELETE",
            )
        )
        db.session.delete(roteiro)
        db.session.commit()
        return {"status": "success", "message": "Roteiro excluido com sucesso!"}, 200

    def serializarRoteiro(
        self, roteiro: Roteiro, incluir_modulos: bool = False
    ) -> dict[str, object]:
        """Serializa o roteiro no formato esperado pelo frontend."""
        dados = roteiro.to_dict()
        if incluir_modulos:
            dados["modulos_vinculados"] = [modulo.id for modulo in roteiro.modulos]
        return dados

    def _validarPermissaoEdicao(
        self, mensagem: str = "Acesso negado."
    ) -> tuple[dict[str, object], int] | None:
        if not session.get("permissions", {}).get("can_edit_scripts", False):
            return self._respostaErro(mensagem, 403)
        return None

    @staticmethod
    def _respostaErro(mensagem: str, codigo: int) -> tuple[dict[str, object], int]:
        return {"status": "error", "message": mensagem}, codigo
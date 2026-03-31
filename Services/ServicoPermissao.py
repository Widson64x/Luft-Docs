from __future__ import annotations

from flask import flash, request, session

from Models import Grupo, Permissao, Usuario, db, permissoes_grupos, permissoes_usuarios


class ServicoPermissao:
    """Centraliza a regra de negocio das rotas de permissao."""

    def carregarPermissoes(self) -> dict[str, dict[str, object]]:
        """Carrega as permissoes do banco no formato usado pela aplicacao."""
        permissoes = Permissao.query.order_by(Permissao.NomePermissao).all()
        return {
            permissao.NomePermissao: {
                "description": permissao.Descricao,
                "groups": [grupo.NomeGrupo for grupo in permissao.Grupos],
                "users": [usuario.NomeUsuario for usuario in permissao.Usuarios],
            }
            for permissao in permissoes
        }

    def salvarPermissoes(self, dados: dict[str, dict[str, object]]) -> None:
        """Recria o estado das permissoes no banco a partir de um dicionario."""
        try:
            db.session.query(permissoes_grupos).delete()
            db.session.query(permissoes_usuarios).delete()
            db.session.query(Grupo).delete()
            db.session.query(Usuario).delete()
            db.session.query(Permissao).delete()

            for nome_permissao, informacoes in dados.items():
                permissao = Permissao(
                    NomePermissao=nome_permissao,
                    Descricao=informacoes.get("description", ""),
                )
                for nome_grupo in informacoes.get("groups", []):
                    grupo = Grupo.query.filter_by(NomeGrupo=nome_grupo).first() or Grupo(
                        NomeGrupo=nome_grupo
                    )
                    permissao.Grupos.append(grupo)

                for nome_usuario in informacoes.get("users", []):
                    usuario = Usuario.query.filter_by(NomeUsuario=nome_usuario).first() or Usuario(
                        NomeUsuario=nome_usuario
                    )
                    permissao.Usuarios.append(usuario)

                db.session.add(permissao)

            db.session.commit()
        except Exception:
            db.session.rollback()
            raise

    @staticmethod
    def obterGrupoUsuario() -> tuple[str, str]:
        """Retorna o grupo e o nome do usuario armazenados na sessao atual."""
        grupo = session.get("user_group", {}).get("acronym", "")
        nome_usuario = session.get("user_name", "")
        return grupo, nome_usuario

    def verificarPermissaoUsuario(self, nome_permissao: str) -> bool:
        """Verifica se o usuario atual possui a permissao informada."""
        nome_grupo, nome_usuario = self.obterGrupoUsuario()
        return db.session.query(
            Permissao.query.filter(
                Permissao.NomePermissao == nome_permissao,
                db.or_(
                    Permissao.Grupos.any(NomeGrupo=nome_grupo),
                    Permissao.Usuarios.any(NomeUsuario=nome_usuario),
                ),
            ).exists()
        ).scalar()

    def obterRespostaVerificacao(self, nome_permissao: str) -> dict[str, object]:
        """Retorna o payload JSON de verificacao de permissao."""
        return {"allowed": self.verificarPermissaoUsuario(nome_permissao)}

    def obterRespostaMeuGrupo(self) -> dict[str, object]:
        """Retorna o grupo, o usuario e as permissoes disponiveis na sessao atual."""
        nome_grupo, nome_usuario = self.obterGrupoUsuario()
        permissoes = Permissao.query.filter(
            db.or_(
                Permissao.Grupos.any(NomeGrupo=nome_grupo),
                Permissao.Usuarios.any(NomeUsuario=nome_usuario),
            )
        ).all()

        return {
            "user": nome_usuario,
            "group": nome_grupo,
            "permissions": {
                permissao.NomePermissao: {
                    "description": permissao.Descricao,
                    "groups": [grupo.NomeGrupo for grupo in permissao.Grupos],
                    "users": [usuario.NomeUsuario for usuario in permissao.Usuarios],
                }
                for permissao in permissoes
            },
        }

    def obterRespostaGerenciamento(self) -> dict[str, object]:
        """Processa a tela de gerenciamento de permissoes."""
        token = request.args.get("token", "").strip()
        if not token:
            return {
                "tipo": "erro",
                "codigo": 401,
                "mensagem": "Token JWT e obrigatorio para acessar esta pagina",
            }

        if request.method == "POST":
            acao = request.values.get("action", "").strip()
            try:
                if acao == "update_perm":
                    self._atualizarPermissao()
                elif acao == "add_perm":
                    self._adicionarPermissao()
                elif acao == "delete_perm":
                    self._excluirPermissao()
            except Exception as erro:
                db.session.rollback()
                flash(f"Ocorreu um erro no banco de dados: {erro}", "danger")

            return {
                "tipo": "redirecionar",
                "endpoint": "Permissoes.gerenciarPermissoes",
                "parametros": {"token": token},
            }

        return {
            "tipo": "renderizar",
            "template": "Pages/MG_Permissions.html",
            "contexto": {
                "permissions": self.carregarPermissoes(),
                "token": token,
            },
        }

    def _atualizarPermissao(self) -> None:
        nome_permissao = request.form.get("perm_name", "").strip()
        permissao = Permissao.query.filter_by(NomePermissao=nome_permissao).first()
        if permissao is None:
            flash("Permissao nao encontrada.", "danger")
            return

        permissao.Descricao = request.form.get("description", "").strip()
        nomes_grupos = {
            grupo.strip()
            for grupo in request.form.get("groups", "").split(",")
            if grupo.strip()
        }
        permissao.Grupos = [
            Grupo.query.filter_by(NomeGrupo=nome).first() or Grupo(NomeGrupo=nome)
            for nome in nomes_grupos
        ]

        nomes_usuarios = {
            usuario.strip()
            for usuario in request.form.get("users", "").split(",")
            if usuario.strip()
        }
        permissao.Usuarios = [
            Usuario.query.filter_by(NomeUsuario=nome).first() or Usuario(NomeUsuario=nome)
            for nome in nomes_usuarios
        ]
        db.session.commit()
        flash(f"Permissao '{nome_permissao}' atualizada.", "success")

    def _adicionarPermissao(self) -> None:
        nome_permissao = request.form.get("new_perm_name", "").strip()
        if not nome_permissao or Permissao.query.filter_by(NomePermissao=nome_permissao).first():
            flash("Permissao invalida ou ja existe.", "danger")
            return

        db.session.add(
            Permissao(
                NomePermissao=nome_permissao,
                Descricao=request.form.get("new_perm_desc", "").strip(),
            )
        )
        db.session.commit()
        flash(f"Permissao '{nome_permissao}' criada.", "success")

    def _excluirPermissao(self) -> None:
        nome_permissao = request.form.get("delete_perm", "").strip()
        permissao = Permissao.query.filter_by(NomePermissao=nome_permissao).first()
        if permissao is None:
            flash("Permissao nao encontrada.", "danger")
            return

        db.session.delete(permissao)
        db.session.commit()
        flash(f"Permissao '{nome_permissao}' removida.", "success")
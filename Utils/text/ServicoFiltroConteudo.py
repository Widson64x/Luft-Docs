from __future__ import annotations

import re


class ServicoFiltroConteudo:
    """Aplica filtros textuais preservando blocos de codigo em markdown."""

    @staticmethod
    def destacarTermos(conteudoMarkdown: str, consulta: str) -> str:
        """Destaca uma consulta no conteudo ignorando blocos de codigo cercados por crases."""
        if not consulta or not conteudoMarkdown:
            return conteudoMarkdown

        consulta_segura = re.escape(consulta)
        regex_destaque = re.compile(f"({consulta_segura})", re.IGNORECASE)
        partes = re.split(r"(```[\s\S]*?```)", conteudoMarkdown)

        partes_processadas = []
        for indice, parte in enumerate(partes):
            if indice % 2 == 0:
                partes_processadas.append(regex_destaque.sub(r"<mark>\1</mark>", parte))
            else:
                partes_processadas.append(parte)
        return "".join(partes_processadas)

    def aplicarFiltro(self, conteudoMarkdown: str, consulta: str | None = None) -> str:
        """Aplica o conjunto padrao de filtros ao conteudo informado."""
        if consulta:
            return self.destacarTermos(conteudoMarkdown, consulta)
        return conteudoMarkdown

    def filtrarDocumentacao(self, conteudoMarkdown: str, consulta: str | None = None) -> str:
        """Aplica filtros na documentacao principal de um modulo."""
        return self.aplicarFiltro(conteudoMarkdown, consulta)

    def filtrarDocumentacaoTecnica(
        self, conteudoMarkdown: str, consulta: str | None = None
    ) -> str:
        """Aplica filtros na documentacao tecnica de um modulo."""
        return self.aplicarFiltro(conteudoMarkdown, consulta)

    def filtrarConteudoSubmodulo(
        self, conteudoMarkdown: str, consulta: str | None = None
    ) -> str:
        """Aplica filtros no conteudo de um submodulo."""
        return self.aplicarFiltro(conteudoMarkdown, consulta)
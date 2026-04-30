from __future__ import annotations

import re

from .ConfiguracaoLLM import ConfiguracaoLLM


class GeradorRespostaLIA:
    """Centraliza o re-ranking e a geracao final das respostas da LIA."""

    URL_BASE_IMAGEM = "http://b2bi-apps.luftfarma.com.br/luft-docs"

    PROMPT_SISTEMA = """Voce e a Lia, a assistente de conhecimento da Luft. Sua missao e ajudar seus colegas a encontrar informacoes de forma clara, amigavel e direta, com tom conversacional e sem inventar nada fora do contexto recebido.

Regras obrigatorias:
1. Comece com uma abertura curta e natural em portugues.
2. Use Markdown com secoes, listas e destaques quando isso melhorar a leitura.
3. Nunca invente informacoes que nao estejam no contexto.
4. Se nao achar a resposta, diga explicitamente que nao foi possivel encontrar nos documentos.
5. Se houver caminhos de imagem no contexto no formato /data/img/..., inclua o caminho literal na resposta para que o sistema formate depois.
"""

    def reranquearEFiltrarContexto(
        self,
        pergunta: str,
        documentos: list[str],
        metadados: list[dict[str, object]],
    ) -> tuple[str, list[str]]:
        """Reclassifica os documentos candidatos e devolve o contexto final."""
        print(f"Iniciando re-ranking de {len(documentos)} documentos candidatos...")
        if not documentos:
            return "", []

        prompt_reranker = f"""
Sua tarefa e atuar como um rigoroso assistente de pesquisa. Analise a PERGUNTA DO USUARIO e a lista de DOCUMENTOS numerados abaixo.
Para cada documento, avalie o quao diretamente ele responde a pergunta do usuario. Sua avaliacao deve ser critica.

Responda com uma lista em Python dos numeros dos documentos que sao MAIS RELEVANTES e UTEIS, em ordem de importancia.
O formato da resposta deve ser apenas a lista, como: [3, 1, 5]

Nao explique sua decisao. Se nenhum documento for relevante, retorne uma lista vazia [].

---
PERGUNTA DO USUARIO: \"{pergunta}\"
---
DOCUMENTOS:
"""
        for indice, documento in enumerate(documentos):
            origem = metadados[indice].get("source", "desconhecida")
            prompt_reranker += (
                f"\n{indice + 1}. [Fonte: {origem}]:\n\"\"\"\n{documento}\n\"\"\"\n"
            )

        try:
            print("Usando Groq (Llama 3.3 70b) como reranker...")
            cliente_groq = ConfiguracaoLLM.obterCliente("groq_client")
            if not cliente_groq:
                raise ConnectionError("Cliente Groq nao disponivel para re-ranking.")

            resposta = cliente_groq.chat.completions.create(
                messages=[{"role": "user", "content": prompt_reranker}],
                model="llama-3.3-70b-versatile",
                temperature=0.0,
            )
            texto_resposta = resposta.choices[0].message.content
            indices_ranqueados = [
                int(valor) - 1 for valor in re.findall(r"\d+", texto_resposta)
            ]
            print(
                f"Ordem de relevancia definida pelo reranker: {[indice + 1 for indice in indices_ranqueados]}"
            )

            documentos_finais: list[str] = []
            metadados_finais: list[dict[str, object]] = []
            for indice in indices_ranqueados:
                if indice < len(documentos):
                    documentos_finais.append(documentos[indice])
                    metadados_finais.append(metadados[indice])

            documentos_finais = documentos_finais[:4]
            metadados_finais = metadados_finais[:4]
            if not documentos_finais:
                print("Reranker concluiu que nenhum documento e relevante.")
                return "", []

            contexto_final = "\n---\n".join(documentos_finais)
            fontes_finais = [
                str(metadado["source"]) for metadado in metadados_finais if "source" in metadado
            ]
            print(
                f"Contexto final construido a partir de {len(documentos_finais)} documentos re-rankeados."
            )
            return contexto_final, sorted(list(set(fontes_finais)))
        except Exception as erro:
            print(f"ERRO no re-ranking: {erro}. Usando os documentos originais como fallback.")
            contexto_fallback = "\n---\n".join(documentos[:3])
            fontes_fallback = [
                str(metadado["source"]) for metadado in metadados[:3] if "source" in metadado
            ]
            return contexto_fallback, sorted(list(set(fontes_fallback)))

    def gerarRespostaLlm(self, nome_modelo: str, contexto: str, pergunta: str) -> str:
        """Gera a resposta final da LIA a partir do contexto ja refinado."""
        prompt_humano = (
            f"**Contexto da Documentacao:**\n{contexto}\n\n"
            f"**Pergunta do Usuario:** \"{pergunta}\""
        )
        print(f"Gerando resposta com {nome_modelo}...")

        if nome_modelo == "groq-70b":
            cliente = ConfiguracaoLLM.obterCliente("groq_client")
            resposta = cliente.chat.completions.create(
                messages=self._montarMensagens(prompt_humano),
                model="llama-3.3-70b-versatile",
            )
            conteudo = resposta.choices[0].message.content
        elif nome_modelo == "kimi":
            cliente = ConfiguracaoLLM.obterCliente("groq_client")
            resposta = cliente.chat.completions.create(
                messages=self._montarMensagens(prompt_humano),
                model="moonshotai/kimi-k2-instruct",
            )
            conteudo = resposta.choices[0].message.content
        elif nome_modelo == "groq-8b":
            cliente = ConfiguracaoLLM.obterCliente("groq_client")
            resposta = cliente.chat.completions.create(
                messages=self._montarMensagens(prompt_humano),
                model="llama-3.1-8b-instant",
                temperature=0.3, # Ajuda a evitar falhas de contexto vazio no Llama 3.1
                max_tokens=1500
            )
            conteudo = resposta.choices[0].message.content
            print(f"\n[DEBUG LIA-8B] Conteudo gerado pela IA: {repr(conteudo)}\n")
        elif nome_modelo == "openai" and ConfiguracaoLLM.obterCliente("openai_client"):
            cliente = ConfiguracaoLLM.obterCliente("openai_client")
            resposta = cliente.chat.completions.create(
                messages=self._montarMensagens(prompt_humano),
                model="gpt-4o",
            )
            conteudo = resposta.choices[0].message.content
        elif nome_modelo == "gemini":
            modelo = ConfiguracaoLLM.obterCliente("gemini_model")
            resposta = modelo.generate_content(
                f"{self.PROMPT_SISTEMA}\n---\n{prompt_humano}"
            )
            conteudo = resposta.text
        elif nome_modelo == "openrouter-gemini" and ConfiguracaoLLM.obterCliente(
            "openrouter_client"
        ):
            cliente = ConfiguracaoLLM.obterCliente("openrouter_client")
            resposta = cliente.chat.completions.create(
                messages=self._montarMensagens(prompt_humano),
                model="google/gemini-2.5-flash",
            )
            conteudo = resposta.choices[0].message.content
        else:
            raise ValueError(f"Modelo '{nome_modelo}' invalido ou nao configurado.")

        return self._forcarFormatacaoImagem(conteudo)

    def _montarMensagens(self, prompt_humano: str) -> list[dict[str, str]]:
        return [
            {"role": "system", "content": self.PROMPT_SISTEMA},
            {"role": "user", "content": prompt_humano},
        ]

    @classmethod
    def _forcarFormatacaoImagem(cls, texto: str) -> str:
        texto = cls._normalizarMarkdownImagem(texto)
        return cls._normalizarCaminhosSoltos(texto)

    @classmethod
    def _normalizarMarkdownImagem(cls, texto: str) -> str:
        padrao_markdown = re.compile(
            r"!?\[[^\]]*\]\(([^)\s]+(?:\.(?:png|jpg|jpeg|gif|webp))[^)]*)\)",
            re.IGNORECASE,
        )

        def substituir(correspondencia: re.Match[str]) -> str:
            url_normalizada = cls._normalizarUrlImagem(correspondencia.group(1))
            if not url_normalizada:
                return correspondencia.group(0)
            return f"\n\n![Imagem do Documento]({url_normalizada})\n\n"

        return padrao_markdown.sub(substituir, texto)

    @classmethod
    def _normalizarCaminhosSoltos(cls, texto: str) -> str:
        padrao_caminho_solto = re.compile(
            r"(?<!\()(?<![\w/:.])(?P<caminho>(?:https?://[^\s\])]+?\.(?:png|jpg|jpeg|gif|webp)(?:\]\([^\s)]+)?|/luft-docs/data/img/[^\s\])]+?\.(?:png|jpg|jpeg|gif|webp)(?:\]\([^\s)]+)?|/data/img/[^\s\])]+?\.(?:png|jpg|jpeg|gif|webp)(?:\]\([^\s)]+)?))",
            re.IGNORECASE,
        )

        def substituir(correspondencia: re.Match[str]) -> str:
            url_normalizada = cls._normalizarUrlImagem(correspondencia.group("caminho"))
            if not url_normalizada:
                return correspondencia.group(0)
            return f"\n\n![Imagem do Documento]({url_normalizada})\n\n"

        return padrao_caminho_solto.sub(substituir, texto)

    @classmethod
    def _normalizarUrlImagem(cls, caminho: str) -> str | None:
        caminho = caminho.strip()
        caminho = caminho.split("](", 1)[0].strip()
        caminho = caminho.rstrip("])")

        if not cls._pareceCaminhoImagem(caminho):
            return None

        if caminho.startswith(("http://", "https://")):
            marcador_prefixado = "/luft-docs/data/img/"
            marcador_direto = "/data/img/"
            if marcador_prefixado in caminho:
                indice = caminho.find(marcador_prefixado)
                return f"{cls.URL_BASE_IMAGEM}{caminho[indice + len('/luft-docs') :]}"
            if marcador_direto in caminho:
                indice = caminho.find(marcador_direto)
                return f"{cls.URL_BASE_IMAGEM}{caminho[indice:]}"
            return caminho

        if caminho.startswith("/luft-docs/data/img/"):
            return f"{cls.URL_BASE_IMAGEM}{caminho[len('/luft-docs') :]}"
        if caminho.startswith("/data/img/"):
            return f"{cls.URL_BASE_IMAGEM}{caminho}"
        return None

    @staticmethod
    def _pareceCaminhoImagem(caminho: str) -> bool:
        return bool(
            re.search(r"\.(png|jpg|jpeg|gif|webp)$", caminho, re.IGNORECASE)
            and (
                "/data/img/" in caminho
                or "/luft-docs/data/img/" in caminho
                or "data/img/" in caminho
            )
        )
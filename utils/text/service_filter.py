# /utils/text/service_filter.py
import re

class ContentFilterService:
    """
    Serviço avançado para aplicar filtros e transformações em conteúdos,
    com destaque de busca inteligente que preserva blocos de código Markdown.
    """

    @staticmethod
    def _highlight_terms(markdown_content: str, query: str) -> str:
        """
        Destaca os termos de uma busca no conteúdo Markdown de forma segura.

        Esta função "entende" a estrutura do Markdown, dividindo o conteúdo em
        blocos de código (delimitados por ```) e texto puro. O destaque é
        aplicado SOMENTE ao texto, ignorando o conteúdo dos blocos de código.

        Args:
            markdown_content (str): O conteúdo Markdown bruto.
            query (str): A palavra ou frase a ser destacada.

        Returns:
            str: O conteúdo Markdown com os termos de busca destacados.
        """
        if not query or not markdown_content:
            return markdown_content

        # 1. Regex para encontrar o termo da busca, ignorando maiúsculas/minúsculas.
        safe_query = re.escape(query)
        highlight_regex = re.compile(f'({safe_query})', re.IGNORECASE)

        # 2. Regex para dividir o conteúdo em duas partes: texto normal e blocos de código.
        #    O padrão (```[\s\S]*?```) captura tudo entre os delimitadores ```.
        #    O resultado será uma lista alternando entre [texto, bloco_de_codigo, texto, ...]
        parts = re.split(r'(```[\s\S]*?```)', markdown_content)
        
        result_parts = []
        # 3. Itera sobre as partes do conteúdo dividido.
        for i, part in enumerate(parts):
            # As partes em índices pares (0, 2, 4...) estão FORA dos blocos de código.
            if i % 2 == 0:
                # Aplica o destaque (<mark>) somente no texto normal.
                highlighted_part = highlight_regex.sub(r'<mark>\1</mark>', part)
                result_parts.append(highlighted_part)
            else:
                # As partes em índices ímpares (1, 3, 5...) são os blocos de código.
                # Elas são adicionadas de volta sem nenhuma modificação.
                result_parts.append(part)

        # 4. Junta todas as partes para reconstruir o conteúdo Markdown final.
        return "".join(result_parts)

    def _apply_filter(self, markdown_content: str, query: str = None) -> str:
        """
        Função central que aplica todos os filtros necessários.
        """
        if query:
            return self._highlight_terms(markdown_content, query)
        return markdown_content

    def filter_documentation(self, markdown_content: str, query: str = None) -> str:
        """Aplica filtros na documentação principal de um módulo."""
        return self._apply_filter(markdown_content, query)

    def filter_technical_documentation(self, markdown_content: str, query: str = None) -> str:
        """Aplica filtros na documentação técnica de um módulo."""
        return self._apply_filter(markdown_content, query)

    def filter_submodule_content(self, markdown_content: str, query: str = None) -> str:
        """Aplica filtros no conteúdo de um submódulo."""
        return self._apply_filter(markdown_content, query)

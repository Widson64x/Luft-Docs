/**
 * Arquivo: ampliarImagem.js
 * Descricao: Identifica cliques em imagens no corpo da documentacao (markdown)
 * e aciona a visualizacao ampliada utilizando o modal padronizado do LuftCore.
 */

class VisualizadorImagem {
    /**
     * Configura o ouvinte global para capturar eventos de clique em imagens.
     */
    constructor() {
        this.containerImagens = document.getElementById('imagem-viewer');
        this.imagemExpandida = document.getElementById('imagemExpandida');

        if (this.containerImagens && this.imagemExpandida) {
            this.inicializarOuvinteDeImagens();
        }
    }

    /**
     * Adiciona funcionalidade de expansao a todas as imagens validas na documentacao.
     */
    inicializarOuvinteDeImagens() {
        const imagensDocumento = this.containerImagens.querySelectorAll('img');

        imagensDocumento.forEach(imagemElemento => {
            // Aplica estilos indicativos para orientar o usuario
            imagemElemento.style.cursor = 'pointer';
            imagemElemento.title = 'Clique para ampliar';

            imagemElemento.addEventListener('click', (evento) => {
                const urlOrigem = evento.target.src;
                
                // Evita acoes em icones pequenos ou emojis
                if (!urlOrigem || urlOrigem.includes('data:image')) return;

                this.abrirImagem(urlOrigem);
            });
        });
    }

    /**
     * Direciona a URL da imagem clicada para o componente do modal e o exibe.
     * @param {string} urlImagem - Caminho absoluto ou relativo da imagem a ser aberta.
     */
    abrirImagem(urlImagem) {
        this.imagemExpandida.src = urlImagem;
        LuftCore.abrirModal('imagemModal');
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new VisualizadorImagem();
});
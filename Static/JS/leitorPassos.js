/**
 * Arquivo: leitorPassos.js
 * Descricao: Extrai o conteudo principal do modulo e o divide em passos interativos,
 * permitindo a navegacao guiada atraves do modal padronizado do LuftCore.
 */

class LeitorPassos {
    /**
     * Inicializa as referencias dos elementos DOM e eventos do leitor.
     */
    constructor() {
        this.elementos = {
            modal: document.getElementById('stepReaderModal'),
            regiaoConteudo: document.getElementById('sr-region'),
            barraProgresso: document.querySelector('.sr-bar'),
            contador: document.querySelector('.sr-count'),
            botaoAnterior: document.querySelector('.sr-prev'),
            botaoProximo: document.querySelector('.sr-next'),
            botaoConcluir: document.querySelector('.sr-done'),
            checkboxEntendi: document.getElementById('sr-mark-reviewed'),
            conteudoOrigem: document.querySelector('.modulo-conteudo')
        };

        this.passos = [];
        this.passoAtual = 0;

        if (this.elementos.conteudoOrigem && this.elementos.modal) {
            this.inicializarEventos();
        }
    }

    /**
     * Configura os ouvintes de eventos para os botoes de navegacao.
     */
    inicializarEventos() {
        // O evento de abrir o modal ja esta no HTML (onclick="LuftCore.abrirModal(...)")
        // Mas precisamos interceptar o clique para carregar os passos na hora que o usuario clica no icone.
        const botaoAbrir = document.getElementById('sr-toggle-icon');
        if (botaoAbrir) {
            botaoAbrir.addEventListener('click', () => {
                this.extrairPassos();
                this.exibirPasso(0);
            });
        }

        this.elementos.botaoAnterior.addEventListener('click', () => this.voltarPasso());
        this.elementos.botaoProximo.addEventListener('click', () => this.avancarPasso());
        this.elementos.checkboxEntendi.addEventListener('change', () => this.validarCheckbox());
    }

    /**
     * Analisa o DOM da documentacao original e quebra o conteudo em blocos (passos)
     * baseando-se nos cabecalhos (H2, H3).
     */
    extrairPassos() {
        this.passos = [];
        const filhos = Array.from(this.elementos.conteudoOrigem.children);
        let blocoAtual = document.createElement('div');

        filhos.forEach((elemento) => {
            const ehCabecalho = ['H2', 'H3'].includes(elemento.tagName);
            
            if (ehCabecalho) {
                if (blocoAtual.innerHTML.trim() !== '') {
                    this.passos.push(blocoAtual.innerHTML);
                }
                blocoAtual = document.createElement('div');
                blocoAtual.appendChild(elemento.cloneNode(true));
            } else {
                blocoAtual.appendChild(elemento.cloneNode(true));
            }
        });

        if (blocoAtual.innerHTML.trim() !== '') {
            this.passos.push(blocoAtual.innerHTML);
        }

        // Fallback caso o documento nao tenha cabecalhos
        if (this.passos.length === 0) {
            this.passos.push(this.elementos.conteudoOrigem.innerHTML);
        }
    }

    /**
     * Renderiza o conteudo do passo especifico e atualiza os controles da interface.
     * @param {number} indice - O indice do passo a ser exibido.
     */
    exibirPasso(indice) {
        if (indice < 0 || indice >= this.passos.length) return;

        this.passoAtual = indice;
        this.elementos.regiaoConteudo.innerHTML = this.passos[this.passoAtual];
        this.elementos.regiaoConteudo.scrollTop = 0;

        // Resetar o checkbox de compreensao
        this.elementos.checkboxEntendi.checked = false;
        this.validarCheckbox();

        this.atualizarProgresso();
    }

    /**
     * Atualiza a barra de progresso, o contador textual e a visibilidade dos botoes.
     */
    atualizarProgresso() {
        const total = this.passos.length;
        const atualBaseUm = this.passoAtual + 1;
        const porcentagem = (atualBaseUm / total) * 100;

        this.elementos.barraProgresso.style.width = `${porcentagem}%`;
        this.elementos.contador.textContent = `${atualBaseUm}/${total}`;

        this.elementos.botaoAnterior.disabled = (this.passoAtual === 0);

        if (this.passoAtual === total - 1) {
            this.elementos.botaoProximo.style.display = 'none';
            this.elementos.botaoConcluir.style.display = 'inline-block';
        } else {
            this.elementos.botaoProximo.style.display = 'inline-block';
            this.elementos.botaoConcluir.style.display = 'none';
        }
    }

    /**
     * Libera ou bloqueia o botao de avanco com base no checkbox de marcacao.
     */
    validarCheckbox() {
        const estaChecado = this.elementos.checkboxEntendi.checked;
        this.elementos.botaoProximo.disabled = !estaChecado;
        this.elementos.botaoConcluir.disabled = !estaChecado;
    }

    /**
     * Avanca para o proximo passo se nao estiver no ultimo.
     */
    avancarPasso() {
        if (this.passoAtual < this.passos.length - 1) {
            this.exibirPasso(this.passoAtual + 1);
        }
    }

    /**
     * Retorna para o passo anterior se nao estiver no primeiro.
     */
    voltarPasso() {
        if (this.passoAtual > 0) {
            this.exibirPasso(this.passoAtual - 1);
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new LeitorPassos();
});
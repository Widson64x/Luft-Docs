/**
 * Arquivo: AnimacaoFundo.js
 * Descricao: Classe reutilizavel para animacao de icones flutuantes no fundo da pagina.
 * Extraida do Index.js para ser compartilhada entre paginas.
 */

class AnimacaoFundo {
    /**
     * Inicializa a logica da animacao de fundo por meio de renderizacao de DOM.
     * @param {string} idContainer - O ID do container responsavel pelo overflow da animacao.
     */
    constructor(idContainer) {
        this.container = document.getElementById(idContainer);
        this.idAnimacaoFrame = null;
        this.dadosIcones = [];
    }

    /**
     * Obtem configuracoes salvas pelo usuario ou aplica padroes para performance da animacao.
     * @returns {Object} Dicionario com quantidade, fator de velocidade e fator de aleatoriedade.
     */
    obterParametrosConfiguracao() {
        const quantidade = parseInt(localStorage.getItem('ld_bg_quantity') || '30', 10);
        const fatorVelocidade = parseFloat(localStorage.getItem('ld_bg_speed') || '1.0');
        const fatorAleatoriedade = 1 + (fatorVelocidade - 1) * 0.5;
        return { quantidade, fatorVelocidade, fatorAleatoriedade };
    }

    obterIconesPadrao() {
        return ['bi-alarm', 'bi-bag', 'bi-gear', 'bi-activity'];
    }

    normalizarClasseIcone(classeIcone) {
        const classe = String(classeIcone || '').trim();

        if (!classe) {
            return 'ph-bold ph-cube';
        }

        if (classe.includes('ph-')) {
            return classe;
        }

        return classe
            .replace('fas fa-', 'ph-bold ph-')
            .replace('bi bi-', 'ph-bold ph-')
            .replace('bi-', 'ph-bold ph-');
    }

    renderizarIcones(iconesDisponiveis, parametros, larguraTela, alturaTela) {
        const icones = Array.isArray(iconesDisponiveis) && iconesDisponiveis.length > 0
            ? iconesDisponiveis
            : this.obterIconesPadrao();

        this.container.innerHTML = '';
        this.dadosIcones = [];

        for (let indice = 0; indice < parametros.quantidade; indice++) {
            const elemento = document.createElement('i');
            const tamanho = (Math.random() * 24 * parametros.fatorAleatoriedade + 16);
            const iconeSorteado = this.normalizarClasseIcone(
                icones[Math.floor(Math.random() * icones.length)]
            );

            elemento.className = `${iconeSorteado}`;
            elemento.style.fontSize = `${tamanho}px`;
            this.container.appendChild(elemento);

            this.dadosIcones.push({
                elemento: elemento,
                posX: Math.random() * (larguraTela - tamanho),
                posY: Math.random() * (alturaTela - tamanho),
                velX: (Math.random() - 0.5) * 1.5 * parametros.fatorVelocidade,
                velY: (Math.random() - 0.5) * 1.5 * parametros.fatorVelocidade,
                tamanhoBase: tamanho
            });
        }

        this.executarLoop();
    }

    /**
     * Inicia a renderizacao em loop dos componentes visuais de fundo.
     */
    iniciar() {
        if (!this.container) return;
        
        const urlJSON = this.container.dataset.iconsUrl;
        if (!urlJSON) return;

        const parametros = this.obterParametrosConfiguracao();
        const larguraTela = this.container.offsetWidth;
        const alturaTela = this.container.offsetHeight;

        fetch(urlJSON)
            .then(resposta => {
                if (!resposta.ok) {
                    throw new Error(`Falha HTTP ${resposta.status}`);
                }

                const tipoConteudo = resposta.headers.get('content-type') || '';
                if (!tipoConteudo.includes('application/json')) {
                    throw new Error(`Conteudo inesperado: ${tipoConteudo || 'desconhecido'}`);
                }

                return resposta.json();
            })
            .then(iconesDisponiveis => {
                this.renderizarIcones(
                    iconesDisponiveis,
                    parametros,
                    larguraTela,
                    alturaTela
                );
            })
            .catch(erro => {
                console.error("Erro ao carregar mapa de icones da animacao:", erro);
                this.renderizarIcones(
                    this.obterIconesPadrao(),
                    parametros,
                    larguraTela,
                    alturaTela
                );
            });
    }

    /**
     * Metodo recursivo acoplado ao requestAnimationFrame para calculo de fisica basica (colisao).
     */
    executarLoop() {
        const larguraTela = this.container.offsetWidth;
        const alturaTela = this.container.offsetHeight;

        this.dadosIcones.forEach(icone => {
            icone.posX += icone.velX;
            icone.posY += icone.velY;

            if (icone.posX <= 0 || icone.posX + icone.tamanhoBase >= larguraTela) { icone.velX *= -1; }
            if (icone.posY <= 0 || icone.posY + icone.tamanhoBase >= alturaTela) { icone.velY *= -1; }
            
            icone.elemento.style.transform = `translate(${icone.posX}px, ${icone.posY}px)`;
        });

        this.idAnimacaoFrame = requestAnimationFrame(() => this.executarLoop());
    }

    /**
     * Interrompe o processo de animacao e descarta os dados atuais.
     */
    parar() {
        if (this.idAnimacaoFrame) {
            cancelAnimationFrame(this.idAnimacaoFrame);
            this.idAnimacaoFrame = null;
        }
        if (this.container) {
            this.container.innerHTML = '';
        }
    }
}

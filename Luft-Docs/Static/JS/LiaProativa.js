/**
 * Arquivo: LiaProativa.js
 * Descricao: Módulo de detecção de inatividade e exibição
 *            proativa do assistente LIA.
 */

class AssistenteProativo {
    constructor(contexto, config) {
        this.contexto = contexto;
        this.config = config;

        this.botaoFlutuante = document.getElementById('botaoFlutuanteLia');
        this.toastProativo  = document.getElementById('toastProativoLia');
        this.textoToast     = document.getElementById('textoToastProativo');

        if (!this.botaoFlutuante || !this.toastProativo || !this.textoToast) {
            console.warn('AssistenteProativo: Elementos essenciais não encontrados.');
            return;
        }

        this.timerInatividade  = null;
        this.timerResetPrompt  = null;
        this.mensagemAtual     = '';

        this._vincularEventos();
        this._reiniciarTimerInatividade();
        console.log('AssistenteProativo: Monitoramento de inatividade iniciado.');
    }

    _vincularEventos() {
        const eventosRastreados = ['mousemove', 'mousedown', 'keypress', 'scroll', 'touchstart'];
        eventosRastreados.forEach(evento =>
            document.addEventListener(evento, () => this._reiniciarTimerInatividade(), { passive: true })
        );
        this.toastProativo.addEventListener('click', () => this._manipularCliqueToast());
    }

    _reiniciarTimerInatividade() {
        if (this.botaoFlutuante.classList.contains('lia-proactive')) return;
        clearTimeout(this.timerInatividade);
        clearTimeout(this.timerResetPrompt);
        this.timerInatividade = setTimeout(() => this._entrarModoProativo(), this.config.timeout);
    }

    _entrarModoProativo() {
        if (!this.contexto.messages || this.contexto.messages.length === 0) return;

        const indiceAleatorio  = Math.floor(Math.random() * this.contexto.messages.length);
        const mensagemEscolhida = this.contexto.messages[indiceAleatorio];

        this.mensagemAtual       = mensagemEscolhida.modal;
        this.textoToast.textContent = mensagemEscolhida.toast;

        this.botaoFlutuante.classList.add('lia-proactive');
        this.toastProativo.classList.add('show');

        console.log(`AssistenteProativo: Modo proativo ativado. ("${mensagemEscolhida.toast}")`);

        this.timerResetPrompt = setTimeout(() => {
            this._sairModoProativo();
            this._reiniciarTimerInatividade();
        }, this.config.promptTimeout);
    }

    _sairModoProativo() {
        this.botaoFlutuante.classList.remove('lia-proactive');
        this.toastProativo.classList.remove('show');
        clearTimeout(this.timerResetPrompt);
    }

    _manipularCliqueToast() {
        if (!this.botaoFlutuante.classList.contains('lia-proactive')) return;
        window._mensagemProativaPendenteLia = this.mensagemAtual;
        this._sairModoProativo();
        this.botaoFlutuante.click();
    }
}

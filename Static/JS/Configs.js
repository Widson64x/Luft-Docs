/**
 * ============================================================================
 * LUFTDOCS - CORE CONFIGURATIONS & SYSTEM BEHAVIOR
 * Responsavel pelo gerenciamento do Modal de Configuracoes, feedback de bugs,
 * e aplicacao global de preferencias do usuario (Modo Compacto, LIA Mode, etc).
 * ============================================================================
 */

class GerenciadorConfiguracoes {
    constructor() {
        this.elementos = {
            selectAnimacao: document.getElementById('selectAnimacao'),
            selectLiaMode: document.getElementById('selectLiaMode'),
            rangeQuantidade: document.getElementById('rangeQuantidade'),
            labelQuantidade: document.getElementById('labelQuantidade'),
            rangeVelocidade: document.getElementById('rangeVelocidade'),
            labelVelocidade: document.getElementById('labelVelocidade'),
            switchCompactMode: document.getElementById('switchCompactMode'),
            btnSalvar: document.getElementById('btnSalvarConfigs')
        };

        this.inicializarEventos();
        this.carregarPreferencias();
    }

    /**
     * Associa os eventos de input aos elementos do DOM para atualizar
     * labels visuais e preparar o salvamento.
     */
    inicializarEventos() {
        if (this.elementos.rangeQuantidade) {
            this.elementos.rangeQuantidade.addEventListener('input', (evento) => {
                if (this.elementos.labelQuantidade) {
                    this.elementos.labelQuantidade.textContent = evento.target.value;
                }
            });
        }

        if (this.elementos.rangeVelocidade) {
            this.elementos.rangeVelocidade.addEventListener('input', (evento) => {
                if (this.elementos.labelVelocidade) {
                    this.elementos.labelVelocidade.textContent = `${parseFloat(evento.target.value).toFixed(1)}x`;
                }
            });
        }

        if (this.elementos.switchCompactMode) {
            this.elementos.switchCompactMode.addEventListener('change', (evento) => {
                this.aplicarModoCompacto(evento.target.checked);
            });
        }

        if (this.elementos.btnSalvar) {
            this.elementos.btnSalvar.addEventListener('click', () => this.salvarPreferencias());
        }
    }

    /**
     * Recupera dados do localStorage e popula os controles do Modal,
     * alem de engatilhar a execucao inicial dos estilos e bibliotecas.
     */
    carregarPreferencias() {
        const configuracoes = {
            animacao: localStorage.getItem('ld_bgAnimation') || 'colisao',
            liaMode: localStorage.getItem('ld_lia_mode') || 'sidebar',
            quantidade: localStorage.getItem('ld_bg_quantity') || '50',
            velocidade: localStorage.getItem('ld_bg_speed') || '1.0',
            modoCompacto: localStorage.getItem('ld_compact_mode') === 'true'
        };

        if (this.elementos.selectAnimacao) this.elementos.selectAnimacao.value = configuracoes.animacao;
        if (this.elementos.selectLiaMode) this.elementos.selectLiaMode.value = configuracoes.liaMode;
        
        if (this.elementos.rangeQuantidade) {
            this.elementos.rangeQuantidade.value = configuracoes.quantidade;
            if (this.elementos.labelQuantidade) this.elementos.labelQuantidade.textContent = configuracoes.quantidade;
        }
        
        if (this.elementos.rangeVelocidade) {
            this.elementos.rangeVelocidade.value = configuracoes.velocidade;
            if (this.elementos.labelVelocidade) this.elementos.labelVelocidade.textContent = `${parseFloat(configuracoes.velocidade).toFixed(1)}x`;
        }

        if (this.elementos.switchCompactMode) {
            this.elementos.switchCompactMode.checked = configuracoes.modoCompacto;
        }

        this.aplicarModoCompacto(configuracoes.modoCompacto);
        this.aplicarModoLia(configuracoes.liaMode);
        this.inicializarBibliotecasExternas();
    }

    /**
     * Grava os estados atuais dos inputs no armazenamento do navegador
     * e recarrega animacoes caso existam no contexto da pagina.
     */
    salvarPreferencias() {
        if (this.elementos.selectAnimacao) localStorage.setItem('ld_bgAnimation', this.elementos.selectAnimacao.value);
        if (this.elementos.selectLiaMode) localStorage.setItem('ld_lia_mode', this.elementos.selectLiaMode.value);
        if (this.elementos.rangeQuantidade) localStorage.setItem('ld_bg_quantity', this.elementos.rangeQuantidade.value);
        if (this.elementos.rangeVelocidade) localStorage.setItem('ld_bg_speed', this.elementos.rangeVelocidade.value);
        if (this.elementos.switchCompactMode) localStorage.setItem('ld_compact_mode', this.elementos.switchCompactMode.checked);

        this.aplicarModoLia(this.elementos.selectLiaMode?.value);

        // Dispara a atualizacao da animacao da pagina Index (caso esteja na tela inicial)
        if (typeof window.mudarAnimacao === 'function' && this.elementos.selectAnimacao) {
            window.mudarAnimacao(this.elementos.selectAnimacao.value);
        }

        // Fechar Modal pelo LuftCore
        if (typeof LuftCore !== 'undefined') {
            LuftCore.fecharModal('modalConfiguracoes');
        }
    }

    /**
     * Aplica uma classe estrutural no Body para densidade de UI.
     * @param {boolean} ativo - Define se o modo compacto devera estar ativo.
     */
    aplicarModoCompacto(ativo) {
        if (ativo) {
            document.body.classList.add('luft-compact-mode');
        } else {
            document.body.classList.remove('luft-compact-mode');
        }
    }

    /**
     * Atualiza o atributo semantico do body para manipulacao pelo CSS da LIA.
     * @param {string} modo - 'sidebar' ou 'modal'.
     */
    aplicarModoLia(modo) {
        document.body.setAttribute('data-lia-mode', modo || 'sidebar');
    }

    /**
     * Inicializa componentes globais como formatadores de codigo (HighlightJS)
     * e visualizadores de imagem (ViewerJS).
     */
    inicializarBibliotecasExternas() {
        if (typeof hljs !== 'undefined') {
            hljs.highlightAll();
        }

        const containerBase = document.getElementById('main-content');
        if (containerBase && typeof Viewer !== 'undefined') {
            new Viewer(containerBase, {
                filter(imagem) { return imagem.parentElement.classList.contains('modulo-conteudo'); },
                toolbar: true, navbar: false, title: false, movable: true, zoomable: true,
                rotatable: false, scalable: false, transition: true, fullscreen: true,
            });
        }
    }
}

class GerenciadorFeedback {
    constructor() {
        this.formulario = document.getElementById('bugReportForm');
        this.selectTipo = document.getElementById('reportType');
        this.containerEntidade = document.getElementById('targetEntityWrapper');
        this.containerCategoria = document.getElementById('errorCategoryWrapper');
        this.statusFeedback = document.getElementById('reportStatus');

        this.categoriasErro = {
            'visual': 'Erro visual / Quebra de layout',
            'funcionalidade': 'Botão ou funcionalidade não funciona',
            'dados': 'Informação incorreta ou ausente',
            'performance': 'Lentidão ou travamento',
            'outro': 'Outro tipo de anomalia'
        };

        if (this.formulario) {
            this.inicializarEventos();
        }
    }

    inicializarEventos() {
        this.selectTipo.addEventListener('change', () => this.manipularMudancaTipo());
        this.formulario.addEventListener('submit', (evento) => this.submeterFeedback(evento));
    }

    manipularMudancaTipo() {
        const tipoSelecionado = this.selectTipo.value;
        this.containerEntidade.innerHTML = '';
        this.containerEntidade.style.display = 'none';
        this.containerCategoria.innerHTML = '';
        this.containerCategoria.style.display = 'none';

        if (tipoSelecionado === 'tela' || tipoSelecionado === 'modulo') {
            const opcoesCategoria = Object.entries(this.categoriasErro)
                .map(([valor, texto]) => `<option value="${valor}">${texto}</option>`)
                .join('');
            
            this.containerCategoria.innerHTML = `
                <label for="errorCategory" class="luft-form-label">Qual a categoria do problema?</label>
                <select class="form-control" id="errorCategory" required>
                    <option value="" selected disabled>Selecione...</option>
                    ${opcoesCategoria}
                </select>`;
            this.containerCategoria.style.display = 'block';
        }

        if (tipoSelecionado === 'tela') {
            this.containerEntidade.style.display = 'block';
            this.containerEntidade.innerHTML = `
                <label for="targetEntity" class="luft-form-label">Em qual tela?</label>
                <input type="text" class="form-control" id="targetEntity" placeholder="Ex: Tela Inicial, Editor..." required>`;
                
        } else if (tipoSelecionado === 'modulo' && typeof allModulesForReport !== 'undefined') {
            this.containerEntidade.style.display = 'block';
            const opcoesModulo = allModulesForReport.map(mod => `<option value="${mod.id}">${mod.nome}</option>`).join('');
            this.containerEntidade.innerHTML = `
                <label for="targetEntity" class="luft-form-label">Qual módulo?</label>
                <select class="form-control" id="targetEntity" required>
                    <option value="" selected disabled>Selecione...</option>
                    ${opcoesModulo}
                </select>`;
        }
    }

    async submeterFeedback(evento) {
        evento.preventDefault();
        const botaoSubmeter = this.formulario.querySelector('button[type="submit"]');
        const dadosReporte = {
            report_type: this.selectTipo.value,
            target_entity: document.getElementById('targetEntity')?.value || null,
            error_category: document.getElementById('errorCategory')?.value || null,
            description: document.getElementById('bugDescription').value
        };

        botaoSubmeter.disabled = true;
        // Removido spinner-border do Bootstrap, usado o icone giratorio do LuftCore
        botaoSubmeter.innerHTML = '<i class="ph-bold ph-spinner-gap ph-spin"></i> A Processar...';
        this.statusFeedback.innerHTML = '';

        if (typeof bugReportURL === 'undefined') {
            this.statusFeedback.innerHTML = `<div class="luft-alert luft-alert-danger mt-3"><i class="ph-bold ph-warning-circle"></i> URL de sincronizacao nao definida.</div>`;
            this.restaurarBotao(botaoSubmeter);
            return;
        }

        try {
            const resposta = await fetch(bugReportURL, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(dadosReporte)
            });

            const dados = await resposta.json();

            if (!resposta.ok) throw new Error(dados.message || "Falha na comunicacao com o servidor.");

            this.statusFeedback.innerHTML = `<div class="luft-alert luft-alert-success mt-3"><i class="ph-bold ph-check-circle"></i> ${dados.message}</div>`;
            this.formulario.reset();
            this.selectTipo.dispatchEvent(new Event('change'));

        } catch (erro) {
            this.statusFeedback.innerHTML = `<div class="luft-alert luft-alert-danger mt-3"><i class="ph-bold ph-warning-circle"></i> ${erro.message}</div>`;
        } finally {
            this.restaurarBotao(botaoSubmeter);
        }
    }

    restaurarBotao(botao) {
        botao.disabled = false;
        botao.innerHTML = '<i class="ph-bold ph-bug"></i> Enviar Feedback para a Equipa';
    }
}

// ============================================================================
// INICIALIZADOR GLOBAL (Entrypoint)
// ============================================================================
document.addEventListener('DOMContentLoaded', () => {
    new GerenciadorConfiguracoes();
    new GerenciadorFeedback();
});
/**
 * Arquivo: LiaChat.js
 * Descricao: Modulo principal de gerenciamento do assistente virtual LIA.
 */

class AvisoChatLia {
    constructor(idOverlay, idBotaoConfirmar, idCheckbox) {
        this.elementoOverlay = document.getElementById(idOverlay);
        this.botaoConfirmar = document.getElementById(idBotaoConfirmar);
        this.checkboxNaoMostrar = document.getElementById(idCheckbox);
        
        if (!this.elementoOverlay || !this.botaoConfirmar || !this.checkboxNaoMostrar) {
            this.estaDesabilitado = true;
            return;
        }

        this.chaveArmazenamento = 'lia_aviso_dispensado_v2';
        this.estaDesabilitado = false;
        this.inicializarEventos();
    }

    inicializarEventos() {
        this.botaoConfirmar.addEventListener('click', () => {
            if (this.checkboxNaoMostrar.checked) {
                try { localStorage.setItem(this.chaveArmazenamento, '1'); } catch (erro) {}
            }
            this.ocultar();
        });

        document.addEventListener('keydown', (evento) => {
            if (evento.key === 'Escape' && this.elementoOverlay.classList.contains('show')) {
                this.ocultar();
            }
        });
    }

    exibir() {
        if (this.estaDesabilitado || localStorage.getItem(this.chaveArmazenamento) === '1') return;
        this.elementoOverlay.classList.add('show');
        this.elementoOverlay.setAttribute('aria-hidden', 'false');
        this.botaoConfirmar.focus();
    }

    ocultar() {
        if (this.estaDesabilitado) return;
        this.elementoOverlay.classList.remove('show');
        this.elementoOverlay.setAttribute('aria-hidden', 'true');
    }
}

class ChatLia {
    constructor() {
        this.urlsApi = window.ROUTES?.Lia || {};

        this.elementosModal = {
            container: document.getElementById('liaModal'),
            botaoPerguntar: document.getElementById('botaoPerguntar_modal'),
            inputPergunta: document.getElementById('inputPergunta_modal'),
            seletorModelo: document.getElementById('seletorModelo_modal'),
            containerResposta: document.getElementById('containerResposta_modal'),
            botaoAjudaModulos: document.getElementById('botaoAjudaModulos_modal'),
            listaModulos: document.getElementById('listaModulos_modal'),
            pilhaTextarea: document.getElementById('pilhaTextarea_modal'),
            espelhoDestaque: document.getElementById('espelhoDestaque_modal'),
        };

        this.elementosSidebar = {
            container: document.getElementById('sidebarLia'),
            backdrop: document.getElementById('backdropSidebarLia'),
            redimensionador: document.getElementById('redimensionadorSidebarLia'),
            botaoFechar: document.getElementById('btnFecharSidebarLia'),
            botaoPerguntar: document.getElementById('botaoPerguntar_sidebar'),
            inputPergunta: document.getElementById('inputPergunta_sidebar'),
            seletorModelo: document.getElementById('seletorModelo_sidebar'),
            containerResposta: document.getElementById('containerResposta_sidebar'),
            botaoAjudaModulos: document.getElementById('botaoAjudaModulos_sidebar'),
            listaModulos: document.getElementById('listaModulos_sidebar'),
            pilhaTextarea: document.getElementById('pilhaTextarea_sidebar'),
            espelhoDestaque: document.getElementById('espelhoDestaque_sidebar'),
        };

        this.elementosGlobais = {
            botaoFlutuante: document.getElementById('botaoFlutuanteLia'),
        };

        if (!this.elementosGlobais.botaoFlutuante) return;

        this.estadoAtual = {
            carregando: false,
            modoInterface: this.obterModoLia(),
            elementosAtivos: null,
            idResposta: null,
            idUsuario: null,
            perguntaUsuario: null,
            modeloUtilizado: null,
            fontesContexto: [],
            idTimeoutPensamento: null,
            indicePensamento: 0
        };

        this.cacheModulos = [];
        this.listaAutocompletarVisivel = false;

        this.moduloProativoNome = this.elementosGlobais.botaoFlutuante.dataset.proactiveModuleName;
        this.moduloProativoId = this.elementosGlobais.botaoFlutuante.dataset.proactiveModuleId;
        
        this.gerenciadorAviso = new AvisoChatLia('overlayAvisoLia', 'btnConfirmarAvisoLia', 'checkboxNaoMostrarNovamente');

        this.carregarLarguraSidebar();
        this.inicializarRedimensionador();
        this.inicializarEventos();
        this.inicializarBotaoProativo();
    }

    obterModoLia() {
        return localStorage.getItem('ld_lia_mode') || 'sidebar';
    }

    definirElementosAtivos(modo) {
        this.estadoAtual.modoInterface = modo;
        this.estadoAtual.elementosAtivos = (modo === 'modal') ? this.elementosModal : this.elementosSidebar;
    }

    inicializarEventos() {
        this.elementosGlobais.botaoFlutuante.addEventListener('click', () => this.abrirLia());

        const amarrarEventosEntrada = (componentes) => {
            if (componentes.inputPergunta) {
                componentes.inputPergunta.addEventListener('keypress', (e) => this.manipularTeclaPressionada(e));
                componentes.inputPergunta.addEventListener('input', () => this.manipularEntradaTexto());
                
                // Sincroniza o scroll para que o destaque nunca fique desalinhado
                componentes.inputPergunta.addEventListener('scroll', (e) => {
                    if (componentes.espelhoDestaque) {
                        componentes.espelhoDestaque.scrollTop = e.target.scrollTop;
                    }
                });
            }
            if (componentes.botaoPerguntar) {
                componentes.botaoPerguntar.addEventListener('click', () => this.processarPergunta());
            }
            if (componentes.botaoAjudaModulos) {
                componentes.botaoAjudaModulos.addEventListener('click', () => this.manipularCliqueAjudaModulos());
            }
            if (componentes.containerResposta) {
                componentes.containerResposta.addEventListener('click', (e) => this.manipularCliqueFeedback(e));
            }
        };

        amarrarEventosEntrada(this.elementosModal);
        amarrarEventosEntrada(this.elementosSidebar);

        if (this.elementosSidebar.backdrop) this.elementosSidebar.backdrop.addEventListener('click', () => this.fecharSidebar());
        if (this.elementosSidebar.botaoFechar) this.elementosSidebar.botaoFechar.addEventListener('click', () => this.fecharSidebar());
        
        document.addEventListener('click', (e) => this.manipularCliqueGlobal(e));
    }

    carregarLarguraSidebar() {
        const larguraSalva = localStorage.getItem('ld_sidebar_width');
        if (larguraSalva) document.documentElement.style.setProperty('--lia-sidebar-width', `${larguraSalva}px`);
    }

    salvarLarguraSidebar(largura) {
        localStorage.setItem('ld_sidebar_width', largura);
    }
    
    inicializarRedimensionador() {
        const redimensionador = this.elementosSidebar.redimensionador;
        if (!redimensionador) return;

        const painelLateral = this.elementosSidebar.container;
        const eventoMovimentoMouse = (evento) => {
            evento.preventDefault();
            let novaLargura = window.innerWidth - evento.clientX;
            const larguraMinima = parseInt(getComputedStyle(painelLateral).minWidth, 10) || 320;
            const larguraMaxima = parseInt(getComputedStyle(painelLateral).maxWidth, 10) || 800;
            
            if (novaLargura < larguraMinima) novaLargura = larguraMinima;
            if (novaLargura > larguraMaxima) novaLargura = larguraMaxima;
            document.documentElement.style.setProperty('--lia-sidebar-width', `${novaLargura}px`);
        };

        const eventoFimMovimento = () => {
            document.body.classList.remove('lia-sidebar-resizing');
            document.removeEventListener('mousemove', eventoMovimentoMouse);
            document.removeEventListener('mouseup', eventoFimMovimento);
            this.salvarLarguraSidebar(parseInt(getComputedStyle(painelLateral).width, 10));
        };

        redimensionador.addEventListener('mousedown', (evento) => {
            evento.preventDefault();
            document.body.classList.add('lia-sidebar-resizing');
            document.addEventListener('mousemove', eventoMovimentoMouse);
            document.addEventListener('mouseup', eventoFimMovimento);
        });
    }

    inicializarBotaoProativo() {
        if (this.moduloProativoNome && this.moduloProativoId) {
            this.elementosGlobais.botaoFlutuante.classList.add('lia-proactive');
        }
    }

    abrirLia() {
        const modo = this.obterModoLia();
        this.gerenciadorAviso.exibir();

        if (modo === 'modal') {
            if (typeof LuftCore !== 'undefined') {
                LuftCore.abrirModal('liaModal');
                setTimeout(() => this.manipularAberturaLia('modal'), 100);
            }
        } else {
            document.body.classList.add('lia-sidebar-open');
            this.manipularAberturaLia('sidebar');
        }
    }

    fecharSidebar() {
        document.body.classList.remove('lia-sidebar-open');
    }

    manipularAberturaLia(modo) {
        this.definirElementosAtivos(modo); 
        const componentes = this.estadoAtual.elementosAtivos;
        
        if (componentes && componentes.inputPergunta) {
            componentes.inputPergunta.focus();
            
            if (componentes.containerResposta.children.length === 0 || componentes.containerResposta.textContent.trim() === '') {
                const mensagemProativa = window._mensagemProativaPendenteLia;
                if (mensagemProativa) {
                    delete window._mensagemProativaPendenteLia;
                    this.renderizarMensagem(mensagemProativa, 'ai-message');
                } else {
                    let mensagemBoasVindas = '';
                    if (this.moduloProativoNome) {
                        const nomeFormatado = this.moduloProativoNome.replace(/-/g, ' ');
                        mensagemBoasVindas = `Saudações. Verifiquei que se encontra no escopo do módulo <strong>${nomeFormatado}</strong>. Posso providenciar auxílio sobre este contexto?`;
                    } else {
                        mensagemBoasVindas = 'Saudações. Sou a LIA, assistente técnica de conhecimento. Em que contexto operacional posso auxiliar?';
                    }
                    this.renderizarMensagem(mensagemBoasVindas, 'ai-message');
                }
                this.redefinirEstadoUltimaResposta();
            }

            if (this.moduloProativoId && !componentes.inputPergunta.value.includes(`@${this.moduloProativoId}`)) {
                componentes.inputPergunta.value = `@${this.moduloProativoId} `;
            }
            
            this.manipularEntradaTexto(); 
        }
    }

    manipularTeclaPressionada(evento) {
        if (evento.key === 'Enter' && !evento.shiftKey) {
            evento.preventDefault();
            this.processarPergunta();
        }
    }

    manipularEntradaTexto() {
        const componentes = this.estadoAtual.elementosAtivos;
        if (!componentes || !componentes.inputPergunta) return;

        const textoDigitado = componentes.inputPergunta.value;
        const indiceArroba = textoDigitado.lastIndexOf('@');
        
        if (indiceArroba !== -1 && !textoDigitado.includes(' ', indiceArroba)) {
            this.exibirListaModulos(textoDigitado.substring(indiceArroba + 1));
        } else {
            this.ocultarListaModulos();
        }
        
        this.redimensionarTextareaAutomaticamente();

        const textoDestacado = this.destacarMencoes(textoDigitado);
        if (componentes.espelhoDestaque) {
            componentes.espelhoDestaque.innerHTML = textoDestacado + ' '; 
        }
    }

    redimensionarTextareaAutomaticamente() {
        const componentes = this.estadoAtual.elementosAtivos;
        if (!componentes || !componentes.inputPergunta) return;

        const elementoTextarea = componentes.inputPergunta;
        
        // Redefine para calcular a altura real (com limites de 48px e 140px configurados no CSS)
        elementoTextarea.style.height = '48px'; 
        const alturaRequisitada = elementoTextarea.scrollHeight;
        const novaAltura = Math.min(Math.max(alturaRequisitada, 48), 140);
        
        elementoTextarea.style.height = novaAltura + 'px';
    }

    manipularCliqueAjudaModulos() {
        const componentes = this.estadoAtual.elementosAtivos;
        if (!componentes || !componentes.inputPergunta) return;

        if (this.listaAutocompletarVisivel) {
            this.ocultarListaModulos();
        } else {
            const valorAtual = componentes.inputPergunta.value;
            componentes.inputPergunta.value += (valorAtual.length > 0 && !valorAtual.endsWith(' ')) ? ' @' : '@';
            componentes.inputPergunta.focus();
            this.exibirListaModulos();
        }
    }

    manipularCliqueGlobal(evento) {
        if (!this.elementosModal.listaModulos.contains(evento.target) &&
            !this.elementosSidebar.listaModulos.contains(evento.target) &&
            evento.target !== this.elementosModal.inputPergunta &&
            evento.target !== this.elementosSidebar.inputPergunta &&
            evento.target !== this.elementosModal.botaoAjudaModulos &&
            !this.elementosModal.botaoAjudaModulos.contains(evento.target) &&
            evento.target !== this.elementosSidebar.botaoAjudaModulos &&
            !this.elementosSidebar.botaoAjudaModulos.contains(evento.target)) {
            this.ocultarListaModulos();
        }
    }

    async processarPergunta() {
        const componentes = this.estadoAtual.elementosAtivos;
        if (!componentes) return;

        const solicitacaoUsuario = componentes.inputPergunta.value.trim();
        if (!solicitacaoUsuario || this.estadoAtual.carregando) return;

        this.definirCarregamento(true);
        this.renderizarMensagem(solicitacaoUsuario, 'user-message');
        this.renderizarMensagemPensamento(); 
        
        componentes.inputPergunta.value = '';
        if(componentes.espelhoDestaque) componentes.espelhoDestaque.innerHTML = '';
        this.redimensionarTextareaAutomaticamente();

        try {
            const modeloSeleccionado = componentes.seletorModelo ? componentes.seletorModelo.value : 'groq-70b';
            
            const respostaServidor = await fetch(this.urlsApi.perguntar, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify({
                    user_question: solicitacaoUsuario,
                    selected_model: modeloSeleccionado
                }),
            });

            this.pararAnimacaoPensamento();
            const dadosProcessados = await respostaServidor.json();

            if (respostaServidor.ok) {
                this.renderizarMensagem(dadosProcessados.answer || '', 'ai-message');
                this.atualizarEstadoUltimaResposta(dadosProcessados, solicitacaoUsuario);
                this.renderizarContexto(dadosProcessados.context_sources_objects || dadosProcessados.context_files || []);
            } else {
                this.renderizarMensagem(`<strong>Erro de Processamento:</strong> ${dadosProcessados.error || 'Ocorreu um problema tecnico.'}`, 'error-message');
                this.redefinirEstadoUltimaResposta();
            }

        } catch (erro) {
            this.pararAnimacaoPensamento();
            this.renderizarMensagem('<strong>Falha de Conexao.</strong> Nao foi possivel estabelecer contato com o servico.', 'error-message');
            this.redefinirEstadoUltimaResposta();
        } finally {
            this.definirCarregamento(false);
        }
    }

    definirCarregamento(estado) {
        this.estadoAtual.carregando = estado;
        [this.elementosModal, this.elementosSidebar].forEach(componentes => {
            if (componentes.botaoPerguntar) componentes.botaoPerguntar.disabled = estado;
            if (componentes.inputPergunta) componentes.inputPergunta.disabled = estado;
            if (componentes.seletorModelo) componentes.seletorModelo.disabled = estado;
        });
        
        if (!estado && this.estadoAtual.elementosAtivos) {
            this.estadoAtual.elementosAtivos.inputPergunta.focus();
        }
    }

    renderizarMensagem(conteudo, classeRemetente) {
        const componentes = this.estadoAtual.elementosAtivos;
        if (!componentes || !componentes.containerResposta) return;

        const envelopeMensagem = document.createElement('div');
        envelopeMensagem.className = `luft-lia-message ${classeRemetente}`;

        if (classeRemetente === 'user-message') {
            envelopeMensagem.innerHTML = this.destacarMencoes(conteudo, true);
        } else if (classeRemetente === 'ai-message') {
            envelopeMensagem.innerHTML = typeof marked !== 'undefined' ? marked.parse(conteudo) : conteudo;
            envelopeMensagem.innerHTML += this.criarHtmlFeedback();
        } else {
            envelopeMensagem.innerHTML = conteudo;
        }

        componentes.containerResposta.appendChild(envelopeMensagem);
        componentes.containerResposta.scrollTop = componentes.containerResposta.scrollHeight;
        return envelopeMensagem;
    }

    /**
     * Injeta a caixa de contexto DENTRO do fluxo do chat (abaixo da ultima mensagem).
     */
    renderizarContexto(arquivosBase) {
        const componentes = this.estadoAtual.elementosAtivos;
        if (!componentes || !componentes.containerResposta) return;

        if (!Array.isArray(arquivosBase) || arquivosBase.length === 0) return;

        // Encontrar a última mensagem AI no chat para injetar as fontes dentro dela
        const mensagensAi = componentes.containerResposta.querySelectorAll('.luft-lia-message.ai-message');
        const ultimaMensagemAi = mensagensAi[mensagensAi.length - 1];
        if (!ultimaMensagemAi) return;

        const extratoHtml = arquivosBase.map(arquivo => {
            const eObjeto = typeof arquivo === 'object' && arquivo !== null;
            const rotulo = eObjeto ? arquivo.name : arquivo;
            const urlDirecionamento = eObjeto ? arquivo.url : '#';
            const possuiVinculo = eObjeto && urlDirecionamento && urlDirecionamento !== '#';

            if (possuiVinculo) {
                return `
                    <li class="lia-fonte-item">
                        <a href="${urlDirecionamento}" target="_blank" class="lia-fonte-link">
                            <i class="ph-bold ph-file-text"></i>
                            <span class="text-break flex-grow-1">${rotulo}</span>
                            <i class="ph-bold ph-arrow-up-right"></i>
                        </a>
                    </li>
                `;
            } else {
                return `
                    <li class="lia-fonte-item">
                        <div class="lia-fonte-link" style="cursor: default;">
                            <i class="ph-bold ph-file-text"></i>
                            <span class="text-break">${rotulo}</span>
                        </div>
                    </li>
                `;
            }
        }).join('');

        const wrapperFontes = document.createElement('div');
        wrapperFontes.className = 'lia-fontes-wrapper';
        wrapperFontes.innerHTML = `
            <div class="lia-fontes-popup" style="display: none;">
                <ul class="list-unstyled m-0">
                    ${extratoHtml}
                </ul>
            </div>
            <button class="lia-fontes-toggle" title="Fontes utilizadas (${arquivosBase.length})">
                <i class="ph-bold ph-stack"></i>
                <span>Fontes (${arquivosBase.length})</span>
                <i class="ph-bold ph-caret-up lia-fontes-toggle-icon"></i>
            </button>
        `;

        // Inserir antes da seção de feedback (se existir), ou no final
        const secaoFeedback = ultimaMensagemAi.querySelector('.feedback-section');
        if (secaoFeedback) {
            ultimaMensagemAi.insertBefore(wrapperFontes, secaoFeedback);
        } else {
            ultimaMensagemAi.appendChild(wrapperFontes);
        }

        const botaoToggle = wrapperFontes.querySelector('.lia-fontes-toggle');
        const popupFontes = wrapperFontes.querySelector('.lia-fontes-popup');
        const iconeToggle = wrapperFontes.querySelector('.lia-fontes-toggle-icon');

        botaoToggle.addEventListener('click', () => {
            const estaOculto = popupFontes.style.display === 'none';
            if (estaOculto) {
                popupFontes.style.display = 'block';
                iconeToggle.style.transform = 'rotate(180deg)';
            } else {
                popupFontes.style.display = 'none';
                iconeToggle.style.transform = 'rotate(0deg)';
            }
            componentes.containerResposta.scrollTop = componentes.containerResposta.scrollHeight;
        });

        componentes.containerResposta.scrollTop = componentes.containerResposta.scrollHeight;
    }

    renderizarMensagemPensamento() {
        const componentes = this.estadoAtual.elementosAtivos;
        if (!componentes) return;

        const passosProcessamento = [
            "A interpretar a sua questão...",
            "A procurar nos manuais de procedimentos...",
            "A organizar o conhecimento...",
            "A redigir a resposta..."
        ];

        const htmlPensamento = `
            <div class="luft-lia-message ai-message" id="indicadorPensamento-${this.estadoAtual.modoInterface}">
                <div class="d-flex align-items-center gap-3 text-muted text-sm font-semibold">
                    <i class="ph-bold ph-spinner-gap ph-spin text-primary"></i>
                    <span id="textoPassoPensamento-${this.estadoAtual.modoInterface}">${passosProcessamento[0]}</span>
                </div>
            </div>
        `;
        
        componentes.containerResposta.insertAdjacentHTML('beforeend', htmlPensamento);
        componentes.containerResposta.scrollTop = componentes.containerResposta.scrollHeight;
        
        this.estadoAtual.indicePensamento = 0;
        this.animarPensamentos(passosProcessamento);
    }

    animarPensamentos(passos) {
        const componentePasso = document.getElementById(`textoPassoPensamento-${this.estadoAtual.modoInterface}`);
        if (!componentePasso) return;

        this.estadoAtual.indicePensamento = (this.estadoAtual.indicePensamento + 1) % passos.length;
        componentePasso.style.opacity = 0;
        
        setTimeout(() => {
            componentePasso.textContent = passos[this.estadoAtual.indicePensamento];
            componentePasso.style.opacity = 1;
            componentePasso.style.transition = 'opacity 0.3s';
            this.estadoAtual.idTimeoutPensamento = setTimeout(() => this.animarPensamentos(passos), 2500);
        }, 300);
    }

    pararAnimacaoPensamento() {
        if (this.estadoAtual.idTimeoutPensamento) {
            clearTimeout(this.estadoAtual.idTimeoutPensamento);
            this.estadoAtual.idTimeoutPensamento = null;
        }

        ['modal', 'sidebar'].forEach(modo => {
            const marcadorPensamento = document.getElementById(`indicadorPensamento-${modo}`);
            if (marcadorPensamento) marcadorPensamento.remove();
        });
    }

    async buscarModulos() {
        if (this.cacheModulos.length > 0) return this.cacheModulos;
        try {
            const resposta = await fetch(this.urlsApi.obterListaModulos, {
                headers: { 'X-Requested-With': 'XMLHttpRequest' }
            });
            if (!resposta.ok) return [];
            const dadosProcessados = await resposta.json();
            this.cacheModulos = dadosProcessados.modules || [];
            return this.cacheModulos;
        } catch (erro) {
            return [];
        }
    }

    exibirListaModulos(filtro = '') {
        const componentes = this.estadoAtual.elementosAtivos;
        if (!componentes) return;

        this.buscarModulos().then(modulosDisponiveis => {
            const modulosFiltrados = modulosDisponiveis.filter(modulo => modulo.toLowerCase().includes(filtro.toLowerCase()));
            if (modulosFiltrados.length === 0) {
                this.ocultarListaModulos();
                return;
            }
            
            componentes.listaModulos.innerHTML = '';
            modulosFiltrados.forEach(modulo => {
                const elementoAncora = document.createElement('a');
                elementoAncora.href = '#';
                elementoAncora.textContent = `@${modulo}`;
                elementoAncora.onclick = (evento) => {
                    evento.preventDefault();
                    const textoVigente = componentes.inputPergunta.value;
                    const indiceArroba = textoVigente.lastIndexOf('@');
                    componentes.inputPergunta.value = textoVigente.substring(0, indiceArroba) + `@${modulo} `;
                    this.ocultarListaModulos();
                    componentes.inputPergunta.focus();
                    this.manipularEntradaTexto();
                };
                componentes.listaModulos.appendChild(elementoAncora);
            });
            
            componentes.listaModulos.style.display = 'block';
            this.listaAutocompletarVisivel = true;
        });
    }

    ocultarListaModulos() {
        if (this.elementosModal.listaModulos) this.elementosModal.listaModulos.style.display = 'none';
        if (this.elementosSidebar.listaModulos) this.elementosSidebar.listaModulos.style.display = 'none';
        this.listaAutocompletarVisivel = false;
    }

    criarHtmlFeedback() {
        return `
          <div class="feedback-section mt-3 pt-2 border-top border-opacity-25">
            <div class="feedback-buttons d-flex gap-2">
                <button class="luft-btn luft-btn-outline p-1 px-2 feedback-good-btn" title="Classificar como util"><i class="ph-bold ph-thumbs-up"></i></button>
                <button class="luft-btn luft-btn-outline p-1 px-2 feedback-bad-btn text-danger" title="Classificar como inutil"><i class="ph-bold ph-thumbs-down"></i></button>
            </div>
            <div class="feedback-comment-area mt-2" style="display: none;">
              <textarea class="form-control mb-2" rows="2" placeholder="Descreva brevemente a falha encontrada para analise..."></textarea>
              <button class="btn btn-primary btn-sm submit-comment-btn py-1">Registrar Analise</button>
            </div>
            <div class="feedback-message mt-2 text-sm font-semibold"></div>
          </div>`;
    }

    atualizarEstadoUltimaResposta(dadosRetorno, perguntaSubmetida) {
        const componentes = this.estadoAtual.elementosAtivos;
        if (!componentes) return;
        
        const modeloSeleccionado = componentes.seletorModelo ? componentes.seletorModelo.value : 'groq-70b';

        this.estadoAtual.idResposta = dadosRetorno.response_id || null;
        this.estadoAtual.idUsuario = dadosRetorno.user_id || null;
        this.estadoAtual.perguntaUsuario = dadosRetorno.original_user_question || perguntaSubmetida;
        this.estadoAtual.modeloUtilizado = dadosRetorno.model_used || modeloSeleccionado;
        this.estadoAtual.fontesContexto = dadosRetorno.context_files || [];
    }

    redefinirEstadoUltimaResposta() {
        this.estadoAtual.idResposta = null;
        this.estadoAtual.idUsuario = null;
        this.estadoAtual.perguntaUsuario = null;
        this.estadoAtual.modeloUtilizado = null;
        this.estadoAtual.fontesContexto = [];
    }

    manipularCliqueFeedback(evento) {
        const componentes = this.estadoAtual.elementosAtivos;
        if (!componentes || !componentes.containerResposta) return;

        const elementoAlvo = evento.target;
        const secaoFeedback = elementoAlvo.closest('.feedback-section');
        if (!secaoFeedback) return;

        const mensagensGeradas = componentes.containerResposta.querySelectorAll('.ai-message');
        const ultimaMensagemGerada = mensagensGeradas[mensagensGeradas.length - 1];
        
        if (!ultimaMensagemGerada || !ultimaMensagemGerada.contains(secaoFeedback)) {
            const alertaAntigo = secaoFeedback.querySelector('.feedback-message');
            if (alertaAntigo) alertaAntigo.innerHTML = '<span class="text-warning"><i class="ph-bold ph-warning"></i> Restrito a interacao recente.</span>';
            return;
        }

        if (elementoAlvo.closest('.feedback-good-btn')) {
            this.enviarFeedback(secaoFeedback, 1);
        } else if (elementoAlvo.closest('.feedback-bad-btn')) {
            const areaComentario = secaoFeedback.querySelector('.feedback-comment-area');
            areaComentario.style.display = (areaComentario.style.display === 'none' || !areaComentario.style.display) ? 'block' : 'none';
        } else if (elementoAlvo.closest('.submit-comment-btn')) {
            const inputComentario = secaoFeedback.querySelector('textarea');
            this.enviarFeedback(secaoFeedback, 0, inputComentario.value);
        }
    }

    async enviarFeedback(secaoReferencia, notaAvaliacao, comentarioAdicional = null) {
        const { idResposta, idUsuario, perguntaUsuario, modeloUtilizado, fontesContexto } = this.estadoAtual;
        const divMensagem = secaoReferencia.querySelector('.feedback-message');
        const controlesAcao = secaoReferencia.querySelector('.feedback-buttons');
        const areaComentario = secaoReferencia.querySelector('.feedback-comment-area');
        
        if (!idResposta || !idUsuario) return;

        secaoReferencia.querySelectorAll('button, textarea').forEach(el => el.disabled = true);

        try {
            const resposta = await fetch(this.urlsApi.registrarFeedback, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify({
                    response_id: idResposta, rating: notaAvaliacao, comment: comentarioAdicional,
                    user_question: perguntaUsuario, model_used: modeloUtilizado, context_sources: fontesContexto
                }),
            });
            const dadosProcessados = await resposta.json();
            
            if (resposta.ok) {
                divMensagem.innerHTML = `<span class="text-success"><i class="ph-bold ph-check-circle"></i> Registrado.</span>`;
                setTimeout(() => { controlesAcao.style.display = 'none'; areaComentario.style.display = 'none'; }, 1500);
            } else {
                secaoReferencia.querySelectorAll('button, textarea').forEach(el => el.disabled = false);
            }
        } catch (erro) {
            secaoReferencia.querySelectorAll('button, textarea').forEach(el => el.disabled = false);
        }
    }

    escaparHtml(stringBase) {
        return stringBase.replace(/[&<>"']/g, function(correspondencia) {
            return {'&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'}[correspondencia];
        });
    }

    destacarMencoes(textoBase, dentroMensagemUsuario = false) {
        if (!textoBase) return '';
        let textoLimpo = this.escaparHtml(textoBase);
        const classeMencao = dentroMensagemUsuario ? 'lia-mention-user' : 'text-primary';
        return textoLimpo.replace(/(@[\w-]+)/g, `<strong class="${classeMencao}">$1</strong>`).replace(/\n/g, '<br>');
    }
}

document.addEventListener('DOMContentLoaded', () => {
    if (window.ROUTES?.Lia) new ChatLia();
});
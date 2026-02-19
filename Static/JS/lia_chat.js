/**
 * lia_chat.js
 * * Versão 3.1 - Sidebar Redimensionável e Compacto
 * Gerencia a LIA, o aviso de consentimento e a interatividade,
 * alternando entre os modos de exibição e permitindo redimensionamento.
 */

/**
 * Classe LiaChatWarning
 * (Nenhuma mudança aqui, permanece a mesma)
 */
class LiaChatWarning {
    constructor(overlayId, confirmBtnId, checkboxId, modalId) {
        this.overlay = document.getElementById(overlayId);
        this.confirmBtn = document.getElementById(confirmBtnId);
        this.dontShowAgain = document.getElementById(checkboxId);
        this.modal = document.getElementById(modalId);
        
        if (!this.overlay || !this.confirmBtn || !this.dontShowAgain) {
            console.warn("Elementos do Aviso LIA não encontrados. O aviso será desabilitado.");
            this.isDisabled = true;
            return;
        }

        this.STORAGE_KEY = 'lia_warning_dismissed_v1';
        this.isDisabled = false;
        this._initEventListeners();
    }

    _initEventListeners() {
        this.confirmBtn.addEventListener('click', () => {
            if (this.dontShowAgain.checked) {
                try {
                    localStorage.setItem(this.STORAGE_KEY, '1');
                } catch (e) {
                    console.error("Não foi possível salvar a preferência no localStorage.", e);
                }
            }
            this.hide();
        });

        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.overlay.classList.contains('show')) {
                this.hide();
            }
        });
    }

    show() {
        if (this.isDisabled) return;
        
        const dismissed = localStorage.getItem(this.STORAGE_KEY) === '1';
        if (dismissed) return;

        this.overlay.classList.add('show');
        document.body.classList.add('lia-blur');
        this.overlay.setAttribute('aria-hidden', 'false');
        this.confirmBtn.focus();
    }

    hide() {
        if (this.isDisabled) return;

        this.overlay.classList.remove('show');
        document.body.classList.remove('lia-blur');
        this.overlay.setAttribute('aria-hidden', 'true');
    }
}

/**
 * Classe LiaChat
 * Gerencia toda a lógica do chat, alternando entre modo Modal e Sidebar.
 */
class LiaChat {
    constructor() {
        // URLs da API (do 'base.html')
        this.apiUrls = window.LIA_API_URLS || {};

        // === Mapeamento de Elementos para MODAL ===
        this.elements_modal = {
            container: document.getElementById('liaModal'),
            askButton: document.getElementById('liaAskButton_modal'),
            userQuestion: document.getElementById('liaUserQuestion_modal'),
            modelSelector: document.getElementById('liaModelSelector_modal'),
            responseContainer: document.getElementById('liaResponseContainer_modal'),
            modulesHelperBtn: document.getElementById('liaModulesHelperBtn_modal'),
            modulesListDiv: document.getElementById('liaModulesList_modal'),
            contextInfoWrapper: document.getElementById('context-info-wrapper_modal'),
            liaTextareaStack: document.getElementById('liaTextareaStack_modal'),
            liaHighlightMirror: document.getElementById('liaHighlightMirror_modal'),
        };

        // === Mapeamento de Elementos para SIDEBAR ===
        this.elements_sidebar = {
            container: document.getElementById('liaSidebar'),
            backdrop: document.getElementById('lia-sidebar-backdrop'),
            resizer: document.getElementById('lia-sidebar-resizer'), // <<< NOVO
            askButton: document.getElementById('liaAskButton_sidebar'),
            userQuestion: document.getElementById('liaUserQuestion_sidebar'),
            modelSelector: document.getElementById('liaModelSelector_sidebar'), // <<< Vai ser nulo (está display:none)
            responseContainer: document.getElementById('liaResponseContainer_sidebar'),
            modulesHelperBtn: document.getElementById('liaModulesHelperBtn_sidebar'),
            modulesListDiv: document.getElementById('liaModulesList_sidebar'),
            contextInfoWrapper: document.getElementById('context-info-wrapper_sidebar'),
            liaTextareaStack: document.getElementById('liaTextareaStack_sidebar'),
            liaHighlightMirror: document.getElementById('liaHighlightMirror_sidebar'),
        };

        // === Elementos Globais ===
        this.elements_global = {
            floatingBtn: document.querySelector('.floating-lia-btn'),
        };

        // Validação
        if (!this.elements_global.floatingBtn || !this.elements_modal.container || !this.elements_sidebar.container) {
            console.error("Elementos essenciais do chat LIA (botão ou containers) não foram encontrados. O chat não pode ser inicializado.");
            return;
        }

        // Instância do Modal Bootstrap (só precisamos de uma)
        this.bootstrapModal = new bootstrap.Modal(this.elements_modal.container);

        // Estado interno do chat
        this.state = {
            isLoading: false,
            currentMode: this._getLiaMode(),
            activeElements: null, // Qual conjunto de elementos está ativo (modal ou sidebar)
            response_id: null,
            user_id: null,
            user_question: null,
            model_used: null,
            context_sources_list: [],
            thinkingTimeoutId: null,
            thoughtIndex: 0
        };

        // Cache dos módulos de autocomplete
        this.modulesCache = [];
        this.isListVisible = false; // Controla a lista de autocomplete

        // Dados proativos do botão
        this.proactiveModuleName = this.elements_global.floatingBtn.dataset.proactiveModuleName;
        this.proactiveModuleId = this.elements_global.floatingBtn.dataset.proactiveModuleId;
        
        // Inicializa o aviso
        this.warning = new LiaChatWarning('lia-warning-overlay', 'liaWarningConfirm', 'liaDontShowAgain', 'liaModal');

        // === NOVO: Carrega largura salva e inicia o resizer ===
        this._loadSidebarWidth();
        this._initResizer();
        // === FIM NOVO ===

        this._initEventListeners();
        this._initProactiveButton();
    }

    /**
     * Helper para ler a preferência do usuário
     */
    _getLiaMode() {
        return localStorage.getItem('ld_lia_mode') || 'sidebar';
    }

    /**
     * Helper para definir qual conjunto de seletores está ativo
     */
    _setActiveElements(mode) {
        this.state.currentMode = mode;
        this.state.activeElements = (mode === 'modal') ? this.elements_modal : this.elements_sidebar;
    }

    /**
     * Anexa todos os listeners de eventos
     */
    _initEventListeners() {
        // Evento de Abrir (Botão Flutuante)
        this.elements_global.floatingBtn.addEventListener('click', this.openLia.bind(this));

        // === Eventos do MODAL ===
        this.elements_modal.container.addEventListener('shown.bs.modal', () => this._handleSidebarOpened('modal'));
        // Eventos de Input (Modal)
        if(this.elements_modal.userQuestion) this.elements_modal.userQuestion.addEventListener('keypress', this._handleKeyPress.bind(this));
        if(this.elements_modal.userQuestion) this.elements_modal.userQuestion.addEventListener('input', this._handleTextInput.bind(this));
        if(this.elements_modal.askButton) this.elements_modal.askButton.addEventListener('click', this.handleAsk.bind(this));
        if(this.elements_modal.modulesHelperBtn) this.elements_modal.modulesHelperBtn.addEventListener('click', this._handleModulesHelperClick.bind(this));
        if(this.elements_modal.responseContainer) this.elements_modal.responseContainer.addEventListener('click', this._handleFeedbackClick.bind(this));


        // === Eventos do SIDEBAR ===
        if(this.elements_sidebar.backdrop) this.elements_sidebar.backdrop.addEventListener('click', this.closeSidebar.bind(this));
        const sidebarCloseBtn = this.elements_sidebar.container.querySelector('.btn-close');
        if (sidebarCloseBtn) {
            sidebarCloseBtn.addEventListener('click', this.closeSidebar.bind(this));
        }
        // Eventos de Input (Sidebar)
        if(this.elements_sidebar.userQuestion) this.elements_sidebar.userQuestion.addEventListener('keypress', this._handleKeyPress.bind(this));
        if(this.elements_sidebar.userQuestion) this.elements_sidebar.userQuestion.addEventListener('input', this._handleTextInput.bind(this));
        if(this.elements_sidebar.askButton) this.elements_sidebar.askButton.addEventListener('click', this.handleAsk.bind(this));
        if(this.elements_sidebar.modulesHelperBtn) this.elements_sidebar.modulesHelperBtn.addEventListener('click', this._handleModulesHelperClick.bind(this));
        if(this.elements_sidebar.responseContainer) this.elements_sidebar.responseContainer.addEventListener('click', this._handleFeedbackClick.bind(this));

        // Evento Global para fechar autocomplete
        document.addEventListener('click', this._handleGlobalClick.bind(this));
    }
    
    // ==========================================================
    // === NOVO: LÓGICA DO RESIZER ==============================
    // ==========================================================
    _loadSidebarWidth() {
        const savedWidth = localStorage.getItem('ld_sidebar_width');
        if (savedWidth) {
            // Aplica a largura salva, mas respeitando os limites do CSS (min/max-width)
            document.documentElement.style.setProperty('--lia-sidebar-width', `${savedWidth}px`);
        }
    }

    _saveSidebarWidth(width) {
        localStorage.setItem('ld_sidebar_width', width);
    }
    
    _initResizer() {
        const resizer = this.elements_sidebar.resizer;
        if (!resizer) return;

        const sidebar = this.elements_sidebar.container;
        const mainContent = document.getElementById('main-content'); // Pega o main content

        const onMouseMove = (e) => {
            e.preventDefault();
            // Calcula a nova largura baseada na posição do mouse
            let newWidth = window.innerWidth - e.clientX;

            // Pega os limites do CSS
            const minWidth = parseInt(getComputedStyle(sidebar).minWidth, 10) || 320;
            const maxWidth = parseInt(getComputedStyle(sidebar).maxWidth, 10) || 800;
            
            // Limita a largura
            if (newWidth < minWidth) newWidth = minWidth;
            if (newWidth > maxWidth) newWidth = maxWidth;

            // Aplica a largura
            document.documentElement.style.setProperty('--lia-sidebar-width', `${newWidth}px`);
        };

        const onMouseUp = () => {
            document.body.classList.remove('lia-sidebar-resizing'); // Classe de estado
            if (mainContent) mainContent.style.transition = ''; // Restaura transição
            
            document.removeEventListener('mousemove', onMouseMove);
            document.removeEventListener('mouseup', onMouseUp);
            
            // Salva a largura final
            const finalWidth = parseInt(getComputedStyle(sidebar).width, 10);
            this._saveSidebarWidth(finalWidth);
        };

        resizer.addEventListener('mousedown', (e) => {
            e.preventDefault();
            document.body.classList.add('lia-sidebar-resizing'); // Classe de estado
            
            // Desativa transição do main content durante o arraste para não lagar
            if (mainContent) mainContent.style.transition = 'none'; 

            document.addEventListener('mousemove', onMouseMove);
            document.addEventListener('mouseup', onMouseUp);
        });
    }
    // ==========================================================
    // === FIM DA LÓGICA DO RESIZER =============================
    // ==========================================================

    _initProactiveButton() {
        if (this.proactiveModuleName && this.proactiveModuleId) {
            this.elements_global.floatingBtn.classList.add('lia-proactive');
        }
    }

    // ==========================================================
    // === MANIPULADORES DE ABERTURA/FECHAMENTO =================
    // ==========================================================
    
    openLia() {
        const mode = this._getLiaMode();
        this.warning.show(); // Mostra o aviso de consentimento

        if (mode === 'modal') {
            this.bootstrapModal.show();
        } else {
            this.openSidebar();
        }
    }

    openSidebar() {
        document.body.classList.add('lia-sidebar-open');
        this._handleSidebarOpened('sidebar');
    }

    closeSidebar() {
        document.body.classList.remove('lia-sidebar-open');
    }

    _handleSidebarOpened(mode) {
        this._setActiveElements(mode); 
        
        const elements = this.state.activeElements;
        elements.userQuestion.focus();
        
        if (elements.responseContainer.children.length === 0 || elements.responseContainer.textContent.trim() === '') {
            let welcomeMessage = '';
            if (this.proactiveModuleName) {
                const formattedModuleName = this.proactiveModuleName.replace(/-/g, ' ');
                welcomeMessage = `Olá! 👋 Vi que você está na página de <strong>${formattedModuleName}</strong>. Posso ajudar com alguma dúvida sobre este processo?`;
            } else {
                welcomeMessage = 'Olá! 👋 Sou a Lia, sua assistente de conhecimento. Como posso ajudar?';
            }
            this._renderMessage(welcomeMessage, 'lia-welcome');
            this._resetLastResponseState();
        }

        if (this.proactiveModuleId && !elements.userQuestion.value.includes(`@${this.proactiveModuleId}`)) {
            elements.userQuestion.value = `@${this.proactiveModuleId} `;
        }
        
        this._handleTextInput(); 
        this._autoResizeTextarea();
    }


    // ==========================================================
    // === MANIPULADORES DE INPUT (COMPARTILHADOS) ==============
    // ==========================================================

    _handleKeyPress(e) {
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            this.handleAsk();
        }
    }

    _handleTextInput() {
        const elements = this.state.activeElements;
        if (!elements || !elements.userQuestion) return;

        const text = elements.userQuestion.value;
        const atIndex = text.lastIndexOf('@');
        
        if (atIndex !== -1 && !text.includes(' ', atIndex)) {
            this._showModulesList(text.substring(atIndex + 1));
        } else {
            this._hideModulesList();
        }
        
        this._autoResizeTextarea();

        const highlightedText = this._highlightAtMentions(text);
        if (elements.liaHighlightMirror) {
            elements.liaHighlightMirror.innerHTML = highlightedText + ' '; 
        }
    }

    _autoResizeTextarea() {
        const elements = this.state.activeElements;
        if (!elements || !elements.userQuestion) return;

        const el = elements.userQuestion;
        const stack = elements.liaTextareaStack;
        const mirror = elements.liaHighlightMirror;
        
        el.style.height = 'auto'; 
        if(stack) stack.style.height = 'auto';
        if(mirror) mirror.style.height = 'auto';

        const scrollHeight = el.scrollHeight;
        
        el.style.height = scrollHeight + 'px';
        if(stack) stack.style.height = scrollHeight + 'px';
        if(mirror) mirror.style.height = scrollHeight + 'px';
    }

    _handleModulesHelperClick() {
        const elements = this.state.activeElements;
        if (!elements || !elements.userQuestion) return;

        if (this.isListVisible) {
            this._hideModulesList();
        } else {
            const val = elements.userQuestion.value;
            elements.userQuestion.value += (val.length > 0 && !val.endsWith(' ')) ? ' @' : '@';
            elements.userQuestion.focus();
            this._showModulesList();
        }
    }

    _handleGlobalClick(e) {
        // Lógica de fechar autocomplete (precisa verificar ambos os containers)
        if (!this.elements_modal.modulesListDiv.contains(e.target) &&
            !this.elements_sidebar.modulesListDiv.contains(e.target) &&
            e.target !== this.elements_modal.userQuestion &&
            e.target !== this.elements_sidebar.userQuestion &&
            e.target !== this.elements_modal.modulesHelperBtn &&
            !this.elements_modal.modulesHelperBtn.contains(e.target) &&
            e.target !== this.elements_sidebar.modulesHelperBtn &&
            !this.elements_sidebar.modulesHelperBtn.contains(e.target)) {
            this._hideModulesList();
        }
    }

    // ==========================================================
    // === LÓGICA DO CHAT (PERGUNTA E RESPOSTA) =================
    // ==========================================================

    async handleAsk() {
        const elements = this.state.activeElements;
        if (!elements) return;

        const userQuestion = elements.userQuestion.value.trim();
        if (!userQuestion || this.state.isLoading) return;

        this._setLoading(true);
        this._renderMessage(userQuestion, 'user');
        
        this._renderThinkingMessage(); 
        
        if (elements.contextInfoWrapper) {
            elements.contextInfoWrapper.style.display = 'none';
        }
        
        elements.userQuestion.value = '';
        if(elements.liaHighlightMirror) elements.liaHighlightMirror.innerHTML = '';
        this._autoResizeTextarea();

        try {
            // *** NOVO: Lógica de fallback para o modelo ***
            const selectedModel = elements.modelSelector ? elements.modelSelector.value : 'groq-70b'; // Default se o seletor não existir
            
            const response = await fetch(this.apiUrls.ask_llm, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_question: userQuestion,
                    selected_model: selectedModel // Envia o modelo (ou o default)
                }),
            });

            this._stopThinkingAnimation();

            const data = await response.json();

            if (response.ok) {
                this._renderMessage(data.answer || '', 'lia');
                this._updateLastResponseState(data, userQuestion);
                this._renderContext(data.context_files || []);
            } else {
                this._renderMessage(`<strong>Erro:</strong> ${data.error || 'Ocorreu um problema.'}`, 'error');
                this._resetLastResponseState();
            }

        } catch (error) {
            console.error("Erro na requisição para ask_llm:", error);
            this._stopThinkingAnimation();
            this._renderMessage('<strong>Erro de conexão.</strong> Não foi possível comunicar com o servidor.', 'error');
            this._resetLastResponseState();
        } finally {
            this._setLoading(false);
        }
    }

    _setLoading(isLoading) {
        this.state.isLoading = isLoading;
        // Afeta ambos os formulários para evitar duplo envio
        [this.elements_modal, this.elements_sidebar].forEach(elements => {
            if (elements.askButton) elements.askButton.disabled = isLoading;
            if (elements.userQuestion) elements.userQuestion.disabled = isLoading;
        });
        
        if (!isLoading && this.state.activeElements) {
            this.state.activeElements.userQuestion.focus();
        }
    }

    _renderMessage(content, sender) {
        const elements = this.state.activeElements;
        if (!elements || !elements.responseContainer) return;

        const messageDiv = document.createElement('div');
        messageDiv.className = 'lia-message';

        switch(sender) {
            case 'user':
                messageDiv.classList.add('user-message');
                messageDiv.innerHTML = this._highlightAtMentions(content);
                break;
            case 'lia':
                messageDiv.innerHTML = marked.parse(content);
                messageDiv.innerHTML += this._createFeedbackHTML();
                break;
            case 'error':
                messageDiv.classList.add('error-message');
                messageDiv.innerHTML = content;
                break;
            case 'lia-welcome':
                messageDiv.classList.add('lia-welcome-message');
                messageDiv.innerHTML = content;
                break;
        }

        elements.responseContainer.appendChild(messageDiv);
        elements.responseContainer.scrollTop = elements.responseContainer.scrollHeight;
    }

    _renderContext(files) {
        const elements = this.state.activeElements;
        if (!elements) return;

        const wrapper = elements.contextInfoWrapper;
        if (!wrapper || !Array.isArray(files) || files.length === 0) {
            if (wrapper) wrapper.style.display = 'none';
            return;
        }
        
        const collapseId = `liaContextCollapse-${this.state.currentMode}-${Date.now()}`;
        const filesList = files.map(file => `<li class="list-group-item">${file}</li>`).join('');
        
        wrapper.innerHTML = `
            <a class="btn-context" data-bs-toggle="collapse" href="#${collapseId}" role="button" aria-expanded="false">
              Fontes utilizadas <i class="bi bi-chevron-down ms-1"></i>
            </a>
            <div class="collapse" id="${collapseId}">
              <ul class="list-group list-group-flush mt-2">${filesList}</ul>
            </div>`;
        wrapper.style.display = 'block';
    }

    // ==========================================================
    // === ANIMAÇÃO DE PENSAMENTO ===============================
    // ==========================================================

    _renderThinkingMessage() {
        const elements = this.state.activeElements;
        if (!elements) return;

        const thoughts = [
            "Opa! Deixa eu ver o que encontro...",
            "Analisando sua pergunta...",
            "Buscando nos documentos relevantes...",
            "Filtrando os resultados...",
            "Pedindo ajuda para a IA gerar a resposta...",
            "Quase lá..."
        ];

        const thinkingHTML = `
            <div class="lia-message lia-thinking-message" id="lia-thinking-placeholder-${this.state.currentMode}">
                <div class="typing-dots">
                    <span></span><span></span><span></span>
                </div>
                <span class="thought-step" id="lia-thought-text-${this.state.currentMode}">${thoughts[0]}</span>
            </div>
        `;
        
        elements.responseContainer.insertAdjacentHTML('beforeend', thinkingHTML);
        elements.responseContainer.scrollTop = elements.responseContainer.scrollHeight;
        
        this.state.thoughtIndex = 0;
        this._animateThoughts(thoughts);
    }

    _animateThoughts(thoughts) {
        const elements = this.state.activeElements;
        if (!elements) return;

        const thoughtElement = document.getElementById(`lia-thought-text-${this.state.currentMode}`);
        if (!thoughtElement) return;

        this.state.thoughtIndex = (this.state.thoughtIndex + 1) % thoughts.length;
        thoughtElement.style.opacity = 0;
        
        setTimeout(() => {
            thoughtElement.textContent = thoughts[this.state.thoughtIndex];
            thoughtElement.style.opacity = 1;
            this.state.thinkingTimeoutId = setTimeout(() => this._animateThoughts(thoughts), 2200);
        }, 300);
    }

    _stopThinkingAnimation() {
        if (this.state.thinkingTimeoutId) {
            clearTimeout(this.state.thinkingTimeoutId);
            this.state.thinkingTimeoutId = null;
        }

        // Tenta remover de ambos os containers
        ['modal', 'sidebar'].forEach(mode => {
            const thinkingPlaceholder = document.getElementById(`lia-thinking-placeholder-${mode}`);
            if (thinkingPlaceholder) {
                thinkingPlaceholder.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
                thinkingPlaceholder.style.opacity = 0;
                thinkingPlaceholder.style.transform = 'scale(0.9)';
                setTimeout(() => thinkingPlaceholder.remove(), 300);
            }
        });
    }

    // ==========================================================
    // === LÓGICA DE AUTOCOMPLETE DE MÓDULO =====================
    // ==========================================================
    
    async _fetchModules() {
        if (this.modulesCache.length > 0) return this.modulesCache;
        try {
            const response = await fetch(this.apiUrls.get_modules);
            if (!response.ok) return [];
            const data = await response.json();
            this.modulesCache = data.modules || [];
            return this.modulesCache;
        } catch (error) {
            console.error("Erro ao buscar lista de módulos:", error);
            return [];
        }
    }

    _showModulesList(filter = '') {
        const elements = this.state.activeElements;
        if (!elements) return;

        this._fetchModules().then(modules => {
            const filteredModules = modules.filter(m => m.toLowerCase().includes(filter.toLowerCase()));
            if (filteredModules.length === 0) {
                this._hideModulesList();
                return;
            }
            
            elements.modulesListDiv.innerHTML = '';
            filteredModules.forEach(module => {
                const item = document.createElement('a');
                item.href = '#';
                item.className = 'list-group-item list-group-item-action';
                item.textContent = `@${module}`;
                item.onclick = (e) => {
                    e.preventDefault();
                    const currentText = elements.userQuestion.value;
                    const atIndex = currentText.lastIndexOf('@');
                    elements.userQuestion.value = currentText.substring(0, atIndex) + `@${module} `;
                    this._hideModulesList();
                    elements.userQuestion.focus();
                    this._handleTextInput();
                };
                elements.modulesListDiv.appendChild(item);
            });
            
            elements.modulesListDiv.style.display = 'block';
            this.isListVisible = true;
        });
    }

    _hideModulesList() {
        // Esconde ambas as listas
        if (this.elements_modal.modulesListDiv) this.elements_modal.modulesListDiv.style.display = 'none';
        if (this.elements_sidebar.modulesListDiv) this.elements_sidebar.modulesListDiv.style.display = 'none';
        this.isListVisible = false;
    }

    // ==========================================================
    // === LÓGICA DE FEEDBACK ===================================
    // ==========================================================

    _createFeedbackHTML() {
        return `
          <div class="feedback-section mt-3">
            <div class="feedback-buttons btn-group">
                <button class="btn btn-sm feedback-good-btn" title="Útil">👍</button>
                <button class="btn btn-sm feedback-bad-btn" title="Não útil">👎</button>
            </div>
            <div class="feedback-comment-area" style="display: none; margin-top: 0.5rem;">
              <textarea class="form-control" rows="2" placeholder="Opcional: Deixe um comentário..."></textarea>
              <button class="btn btn-primary btn-sm mt-2 submit-comment-btn">Enviar</button>
            </div>
            <div class="feedback-message mt-2"></div>
          </div>`;
    }

    _updateLastResponseState(data, userQuestion) {
        const elements = this.state.activeElements;
        if (!elements) return;
        
        // *** NOVO: Lógica de fallback para o modelo ***
        const selectedModel = elements.modelSelector ? elements.modelSelector.value : 'groq-70b';

        this.state.response_id = data.response_id || null;
        this.state.user_id = data.user_id || null;
        this.state.user_question = data.original_user_question || userQuestion;
        this.state.model_used = data.model_used || selectedModel;
        this.state.context_sources_list = data.context_files || [];
    }

    _resetLastResponseState() {
        this.state.response_id = null;
        this.state.user_id = null;
        this.state.user_question = null;
        this.state.model_used = null;
        this.state.context_sources_list = [];
    }

    _handleFeedbackClick(e) {
        const elements = this.state.activeElements;
        if (!elements || !elements.responseContainer) return;

        const target = e.target;
        const feedbackSection = target.closest('.feedback-section');
        if (!feedbackSection) return;

        const allLiaMessages = elements.responseContainer.querySelectorAll('.lia-message:not(.user-message):not(.lia-welcome-message):not(.lia-thinking-message)');
        const lastAiMessageDiv = allLiaMessages[allLiaMessages.length - 1];
        
        if (!lastAiMessageDiv || !lastAiMessageDiv.contains(feedbackSection)) {
            const oldFeedbackMsg = feedbackSection.querySelector('.feedback-message');
            if (oldFeedbackMsg) {
                oldFeedbackMsg.innerHTML = '<p class="alert alert-warning p-2">Apenas a última resposta pode ser avaliada.</p>';
            }
            return;
        }

        if (target.closest('.feedback-good-btn')) {
            this._submitFeedback(feedbackSection, 1);
        } else if (target.closest('.feedback-bad-btn')) {
            const commentArea = feedbackSection.querySelector('.feedback-comment-area');
            commentArea.style.display = (commentArea.style.display === 'none' || !commentArea.style.display) ? 'block' : 'none';
        } else if (target.closest('.submit-comment-btn')) {
            const commentInput = feedbackSection.querySelector('textarea');
            this._submitFeedback(feedbackSection, 0, commentInput.value);
        }
    }

    async _submitFeedback(feedbackSection, rating, comment = null) {
        const { response_id, user_id, user_question, model_used, context_sources_list } = this.state;
        
        const feedbackMessageDiv = feedbackSection.querySelector('.feedback-message');
        const feedbackButtons = feedbackSection.querySelector('.feedback-buttons');
        const commentArea = feedbackSection.querySelector('.feedback-comment-area');
        
        if (!response_id || !user_id) {
            feedbackMessageDiv.innerHTML = '<p class="alert alert-danger p-2">Erro: ID da resposta não disponível.</p>';
            return;
        }

        feedbackSection.querySelectorAll('button, textarea').forEach(el => el.disabled = true);

        try {
            const response = await fetch(this.apiUrls.submit_feedback, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    response_id: response_id,
                    rating: rating,
                    comment: comment,
                    user_question: user_question,
                    model_used: model_used,
                    context_sources: context_sources_list
                }),
            });
            
            const data = await response.json();
            
            if (response.ok) {
                feedbackMessageDiv.innerHTML = `<p class="alert alert-success p-2">${data.message}</p>`;
                setTimeout(() => {
                    feedbackButtons.style.display = 'none';
                    commentArea.style.display = 'none';
                    feedbackMessageDiv.style.display = 'none';
                }, 1500);
            } else {
                feedbackMessageDiv.innerHTML = `<p class="alert alert-danger p-2">Erro: ${data.error}</p>`;
                feedbackSection.querySelectorAll('button, textarea').forEach(el => el.disabled = false);
            }

        } catch (error) {
            console.error("Erro ao enviar feedback:", error);
            feedbackMessageDiv.innerHTML = '<p class="alert alert-danger p-2">Erro de conexão ao enviar feedback.</p>';
            feedbackSection.querySelectorAll('button, textarea').forEach(el => el.disabled = false);
        }
    }
    
    // ==========================================================
    // === NOVOS HELPERS PARA HIGHLIGHT =========================
    // ==========================================================

    _escapeHTML(str) {
        return str.replace(/[&<>"']/g, function(match) {
            return {
                '&': '&amp;',
                '<': '&lt;',
                '>': '&gt;',
                '"': '&quot;',
                "'": '&#39;'
            }[match];
        });
    }

    _highlightAtMentions(text) {
        if (!text) return '';
        
        let escapedText = this._escapeHTML(text);
        const atMentionRegex = /(@[\w-]+)/g;
        let highlightedText = escapedText.replace(atMentionRegex, '<strong>$1</strong>');
        return highlightedText.replace(/\n/g, '<br>');
    }
}

// Inicializa o chat quando o DOM estiver pronto
document.addEventListener('DOMContentLoaded', () => {
    if (window.LIA_API_URLS) {
        const liaChat = new LiaChat();
    } else {
        console.error("LIA_API_URLS não estão definidas no escopo global. O chat LIA não pode ser iniciado.");
    }
});
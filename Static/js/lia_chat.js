/**
 * lia_chat.js
 * * Versão 2.2 - Com Highlight de @
 * Gerencia o modal de chat da LIA, o aviso de consentimento
 * e toda a interatividade do frontend.
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
        
        if (!this.overlay || !this.confirmBtn || !this.dontShowAgain || !this.modal) {
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
 * Gerencia toda a lógica do chat, desde o envio de mensagens
 * até o feedback e autocomplete.
 */
class LiaChat {
    constructor() {
        // Mapeia todos os elementos do DOM
        this.elements = {
            modal: document.getElementById('liaModal'),
            floatingBtn: document.querySelector('.floating-lia-btn'),
            askButton: document.getElementById('liaAskButton'),
            userQuestion: document.getElementById('liaUserQuestion'),
            modelSelector: document.getElementById('liaModelSelector'),
            responseContainer: document.getElementById('liaResponseContainer'),
            spinner: document.getElementById('liaSpinner'),
            sendIcon: document.querySelector('#liaAskButton .bi-send-fill'), 
            modulesHelperBtn: document.getElementById('liaModulesHelperBtn'),
            modulesListDiv: document.getElementById('liaModulesList'),
            contextInfoWrapper: document.getElementById('context-info-wrapper'),
            
            // NOVO: Elementos para o highlight
            liaTextareaStack: document.getElementById('liaTextareaStack'),
            liaHighlightMirror: document.getElementById('liaHighlightMirror'),
        };

        // MODIFICADO: Validação para incluir os novos elementos
        if (!this.elements.modal || !this.elements.askButton || !this.elements.userQuestion || !this.elements.liaHighlightMirror) {
            console.error("Elementos essenciais do chat LIA não foram encontrados. O chat não pode ser inicializado.");
            return;
        }

        // URLs da API (do 'base.html')
        this.apiUrls = window.LIA_API_URLS || {};

        // Estado interno do chat
        this.state = {
            isLoading: false,
            response_id: null,
            user_id: null,
            user_question: null,
            model_used: null,
            context_sources_list: [],
            // Estado para animação de pensamento
            thinkingTimeoutId: null,
            thoughtIndex: 0
        };

        // Cache dos módulos de autocomplete
        this.modulesCache = [];
        this.isListVisible = false;

        // Dados proativos do botão
        this.proactiveModuleName = this.elements.floatingBtn ? this.elements.floatingBtn.dataset.proactiveModuleName : null;
        this.proactiveModuleId = this.elements.floatingBtn ? this.elements.floatingBtn.dataset.proactiveModuleId : null;
        
        // Inicializa o aviso
        this.warning = new LiaChatWarning('lia-warning-overlay', 'liaWarningConfirm', 'liaDontShowAgain', 'liaModal');

        this._initEventListeners();
        this._initProactiveButton();
    }

    /**
     * Anexa todos os listeners de eventos
     */
    _initEventListeners() {
        // Eventos do Modal
        this.elements.modal.addEventListener('shown.bs.modal', this._handleModalShown.bind(this));
        this.elements.modal.addEventListener('show.bs.modal', () => this.warning.show());

        // Eventos de Input
        this.elements.userQuestion.addEventListener('keypress', this._handleKeyPress.bind(this));
        // MODIFICADO: O evento de 'input' agora também atualiza o espelho
        this.elements.userQuestion.addEventListener('input', this._handleTextInput.bind(this));
        this.elements.askButton.addEventListener('click', this.handleAsk.bind(this));

        // Eventos de Autocomplete
        this.elements.modulesHelperBtn.addEventListener('click', this._handleModulesHelperClick.bind(this));
        document.addEventListener('click', this._handleGlobalClick.bind(this));

        // Eventos de Feedback (delegação)
        this.elements.responseContainer.addEventListener('click', this._handleFeedbackClick.bind(this));
    }

    _initProactiveButton() {
        // ... (Nenhuma mudança aqui)
        if (this.elements.floatingBtn && this.proactiveModuleName && this.proactiveModuleId) {
            this.elements.floatingBtn.classList.add('lia-proactive');
        }
    }

    // ==========================================================
    // === MANIPULADORES DE EVENTOS =============================
    // ==========================================================

    _handleModalShown() {
        // ... (Nenhuma mudança aqui)
        this.elements.userQuestion.focus();
        
        if (this.elements.responseContainer.children.length === 0 || this.elements.responseContainer.textContent.trim() === '') {
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

        if (this.proactiveModuleId && !this.elements.userQuestion.value.includes(`@${this.proactiveModuleId}`)) {
            this.elements.userQuestion.value = `@${this.proactiveModuleId} `;
        }
        
        // MODIFICADO: Atualiza o espelho e o resize ao abrir
        this._handleTextInput(); 
        this._autoResizeTextarea();
    }

    _handleKeyPress(e) {
        // ... (Nenhuma mudança aqui)
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault();
            this.handleAsk();
        }
    }

    _handleTextInput() {
        const text = this.elements.userQuestion.value;
        const atIndex = text.lastIndexOf('@');
        
        // Lógica do autocomplete
        if (atIndex !== -1 && !text.includes(' ', atIndex)) {
            this._showModulesList(text.substring(atIndex + 1));
        } else {
            this._hideModulesList();
        }
        
        // Auto-resize do textarea
        this._autoResizeTextarea();

        // NOVO: Atualiza o espelho de highlight
        const highlightedText = this._highlightAtMentions(text);
        // Adiciona um espaço no final para garantir que o div tenha altura ao quebrar linha
        this.elements.liaHighlightMirror.innerHTML = highlightedText + ' '; 
    }

    _autoResizeTextarea() {
        const el = this.elements.userQuestion;
        const stack = this.elements.liaTextareaStack;
        const mirror = this.elements.liaHighlightMirror;
        
        // Reseta a altura para calcular o scrollHeight
        el.style.height = 'auto'; 
        // MODIFICADO: Reseta o stack e o espelho também
        stack.style.height = 'auto';
        mirror.style.height = 'auto';

        const scrollHeight = el.scrollHeight;
        
        // Aplica a nova altura a todos
        el.style.height = scrollHeight + 'px';
        stack.style.height = scrollHeight + 'px';
        mirror.style.height = scrollHeight + 'px';
    }

    _handleModulesHelperClick() {
        // ... (Nenhuma mudança aqui)
        if (this.isListVisible) {
            this._hideModulesList();
        } else {
            const val = this.elements.userQuestion.value;
            this.elements.userQuestion.value += (val.length > 0 && !val.endsWith(' ')) ? ' @' : '@';
            this.elements.userQuestion.focus();
            this._showModulesList();
        }
    }

    _handleGlobalClick(e) {
        // ... (Nenhuma mudança aqui)
        if (!this.elements.modulesListDiv.contains(e.target) &&
            e.target !== this.elements.userQuestion &&
            e.target !== this.elements.modulesHelperBtn &&
            !this.elements.modulesHelperBtn.contains(e.target)) {
            this._hideModulesList();
        }
    }

    // ==========================================================
    // === LÓGICA DO CHAT (PERGUNTA E RESPOSTA) =================
    // ==========================================================

    async handleAsk() {
        const userQuestion = this.elements.userQuestion.value.trim();
        if (!userQuestion || this.state.isLoading) return;

        this._setLoading(true);
        // MODIFICADO: Passa o texto original para o _renderMessage
        this._renderMessage(userQuestion, 'user');
        
        // Renderiza o balão de "pensamento"
        this._renderThinkingMessage(); 
        
        if (this.elements.contextInfoWrapper) {
            this.elements.contextInfoWrapper.style.display = 'none';
        }
        
        // MODIFICADO: Limpa o textarea e o espelho
        this.elements.userQuestion.value = '';
        this.elements.liaHighlightMirror.innerHTML = '';
        this._autoResizeTextarea();

        try {
            const response = await fetch(this.apiUrls.ask_llm, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    user_question: userQuestion, // Envia o texto puro
                    selected_model: this.elements.modelSelector.value
                }),
            });

            // Para a animação e remove o balão de pensamento
            this._stopThinkingAnimation();

            const data = await response.json();

            if (response.ok) {
                // Renderiza a resposta final
                this._renderMessage(data.answer || '', 'lia');
                this._updateLastResponseState(data, userQuestion);
                this._renderContext(data.context_files || []);
            } else {
                this._renderMessage(`<strong>Erro:</strong> ${data.error || 'Ocorreu um problema.'}`, 'error');
                this._resetLastResponseState();
            }

        } catch (error) {
            console.error("Erro na requisição para ask_llm:", error);
            
            // Para a animação e remove o balão de pensamento em caso de erro
            this._stopThinkingAnimation();
            this._renderMessage('<strong>Erro de conexão.</strong> Não foi possível comunicar com o servidor.', 'error');
            this._resetLastResponseState();
        } finally {
            this._setLoading(false);
        }
    }

    _setLoading(isLoading) {
        // ... (Nenhuma mudança aqui)
        this.state.isLoading = isLoading;
        this.elements.askButton.disabled = isLoading;
        this.elements.userQuestion.disabled = isLoading;
        
        if (!isLoading) {
            this.elements.userQuestion.focus();
        }
    }

    _renderMessage(content, sender) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'lia-message';

        switch(sender) {
            case 'user':
                messageDiv.classList.add('user-message');
                // MODIFICADO: Usa o helper de highlight
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

        this.elements.responseContainer.appendChild(messageDiv);
        this.elements.responseContainer.scrollTop = this.elements.responseContainer.scrollHeight;
    }

    _renderContext(files) {
        // ... (Nenhuma mudança aqui)
        const wrapper = this.elements.contextInfoWrapper;
        if (!wrapper || !Array.isArray(files) || files.length === 0) {
            if (wrapper) wrapper.style.display = 'none';
            return;
        }
        
        const collapseId = `liaContextCollapse-${Date.now()}`;
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
        // ... (Nenhuma mudança aqui)
        const thoughts = [
            "Opa! Deixa eu ver o que encontro...",
            "Analisando sua pergunta...",
            "Buscando nos documentos relevantes...",
            "Filtrando os resultados...",
            "Pedindo ajuda para a IA gerar a resposta...",
            "Quase lá..."
        ];

        const thinkingHTML = `
            <div class="lia-message lia-thinking-message" id="lia-thinking-placeholder">
                <div class="typing-dots">
                    <span></span><span></span><span></span>
                </div>
                <span class="thought-step" id="lia-thought-text">${thoughts[0]}</span>
            </div>
        `;
        
        this.elements.responseContainer.insertAdjacentHTML('beforeend', thinkingHTML);
        this.elements.responseContainer.scrollTop = this.elements.responseContainer.scrollHeight;
        
        this.state.thoughtIndex = 0;
        this._animateThoughts(thoughts);
    }

    _animateThoughts(thoughts) {
        // ... (Nenhuma mudança aqui)
        const thoughtElement = document.getElementById('lia-thought-text');
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
        // ... (Nenhuma mudança aqui)
        if (this.state.thinkingTimeoutId) {
            clearTimeout(this.state.thinkingTimeoutId);
            this.state.thinkingTimeoutId = null;
        }

        const thinkingPlaceholder = document.getElementById('lia-thinking-placeholder');
        if (thinkingPlaceholder) {
            thinkingPlaceholder.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
            thinkingPlaceholder.style.opacity = 0;
            thinkingPlaceholder.style.transform = 'scale(0.9)';
            setTimeout(() => thinkingPlaceholder.remove(), 300);
        }
    }

    // ==========================================================
    // === LÓGICA DE AUTOCOMPLETE DE MÓDULO =====================
    // ==========================================================
    
    async _fetchModules() {
        // ... (Nenhuma mudança aqui)
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
        // ... (Nenhuma mudança aqui)
        this._fetchModules().then(modules => {
            const filteredModules = modules.filter(m => m.toLowerCase().includes(filter.toLowerCase()));
            if (filteredModules.length === 0) {
                this._hideModulesList();
                return;
            }
            
            this.elements.modulesListDiv.innerHTML = '';
            filteredModules.forEach(module => {
                const item = document.createElement('a');
                item.href = '#';
                item.className = 'list-group-item list-group-item-action';
                item.textContent = `@${module}`;
                item.onclick = (e) => {
                    e.preventDefault();
                    const currentText = this.elements.userQuestion.value;
                    const atIndex = currentText.lastIndexOf('@');
                    this.elements.userQuestion.value = currentText.substring(0, atIndex) + `@${module} `;
                    this._hideModulesList();
                    this.elements.userQuestion.focus();
                    
                    // MODIFICADO: Atualiza o espelho após o clique
                    this._handleTextInput();
                };
                this.elements.modulesListDiv.appendChild(item);
            });
            
            this.elements.modulesListDiv.style.display = 'block';
            this.isListVisible = true;
        });
    }

    _hideModulesList() {
        // ... (Nenhuma mudança aqui)
        this.elements.modulesListDiv.style.display = 'none';
        this.isListVisible = false;
    }

    // ==========================================================
    // === LÓGICA DE FEEDBACK ===================================
    // ==========================================================

    _createFeedbackHTML() {
        // ... (Nenhuma mudança aqui)
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
        // ... (Nenhuma mudança aqui)
        this.state.response_id = data.response_id || null;
        this.state.user_id = data.user_id || null;
        this.state.user_question = data.original_user_question || userQuestion;
        this.state.model_used = data.model_used || this.elements.modelSelector.value;
        this.state.context_sources_list = data.context_files || [];
    }

    _resetLastResponseState() {
        // ... (Nenhuma mudança aqui)
        this.state.response_id = null;
        this.state.user_id = null;
        this.state.user_question = null;
        this.state.model_used = null;
        this.state.context_sources_list = [];
    }

    _handleFeedbackClick(e) {
        // ... (Nenhuma mudança aqui)
        const target = e.target;
        const feedbackSection = target.closest('.feedback-section');
        if (!feedbackSection) return;

        const allLiaMessages = this.elements.responseContainer.querySelectorAll('.lia-message:not(.user-message):not(.lia-welcome-message):not(.lia-thinking-message)');
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
        // ... (Nenhuma mudança aqui)
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

    /**
     * Escapa caracteres HTML para exibição segura.
     */
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

    /**
     * Encontra menções com @ e as envolve em <strong>.
     * Também converte quebras de linha em <br>.
     */
    _highlightAtMentions(text) {
        if (!text) return '';
        
        // 1. Escapa *todo* o HTML primeiro para segurança
        let escapedText = this._escapeHTML(text);
        
        // 2. Aplica o highlight com <strong>
        // Regex: Encontra um @ seguido por um ou mais caracteres de palavra (letras, números, _) ou hífens.
        const atMentionRegex = /(@[\w-]+)/g;
        let highlightedText = escapedText.replace(atMentionRegex, '<strong>$1</strong>');
        
        // 3. Converte quebras de linha para <br> para o HTML do espelho
        return highlightedText.replace(/\n/g, '<br>');
    }
}

// Inicializa o chat quando o DOM estiver pronto
document.addEventListener('DOMContentLoaded', () => {
    // As URLs da API devem ser definidas em 'base.html'
    if (window.LIA_API_URLS) {
        const liaChat = new LiaChat();
    } else {
        console.error("LIA_API_URLS não estão definidas no escopo global. O chat LIA não pode ser iniciado.");
    }
});
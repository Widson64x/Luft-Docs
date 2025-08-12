// /static/js/lia_chat.js
document.addEventListener('DOMContentLoaded', () => {
  const liaModal = document.getElementById('liaModal');
  if (!liaModal) return;

  // --- SELETORES DE ELEMENTOS ---
  const liaFloatingBtn = document.querySelector('.floating-lia-btn');
  const askButton = document.getElementById('liaAskButton');
  const userQuestionInput = document.getElementById('liaUserQuestion');
  const modelSelector = document.getElementById('liaModelSelector');
  const responseContainer = document.getElementById('liaResponseContainer');
  const spinner = document.getElementById('liaSpinner');
  const sendIcon = askButton ? askButton.querySelector('.bi-send-fill') : null;
  const modulesHelperBtn = document.getElementById('liaModulesHelperBtn');
  const modulesListDiv = document.getElementById('liaModulesList');
  const contextInfoWrapper = document.getElementById('context-info-wrapper');

  // ==========================================================
  // === ASSISTENTE PROATIVO ==================================
  // ==========================================================
  const proactiveModuleName = liaFloatingBtn ? liaFloatingBtn.dataset.proactiveModuleName : null;
  const proactiveModuleId = liaFloatingBtn ? liaFloatingBtn.dataset.proactiveModuleId : null;

  if (liaFloatingBtn && proactiveModuleName && proactiveModuleId) {
    liaFloatingBtn.classList.add('lia-proactive');
  }

  // ==========================================================
  // === AUTOCOMPLETE DE MÓDULOS ==============================
  // ==========================================================
  let modulesCache = [];
  let isListVisible = false;

  const fetchModules = async () => {
    if (modulesCache.length > 0) return modulesCache;
    try {
      const response = await fetch(LIA_API_URLS.get_modules);
      if (!response.ok) return [];
      const data = await response.json();
      modulesCache = data.modules || [];
      return modulesCache;
    } catch (error) {
      console.error("Erro ao buscar lista de módulos:", error);
      return [];
    }
  };

  const showModulesList = (filter = '') => {
    fetchModules().then(modules => {
      const filteredModules = modules.filter(m => m.toLowerCase().includes(filter.toLowerCase()));
      if (filteredModules.length === 0) {
        hideModulesList();
        return;
      }
      modulesListDiv.innerHTML = '';
      filteredModules.forEach(module => {
        const item = document.createElement('a');
        item.href = '#';
        item.className = 'list-group-item list-group-item-action py-2 px-3';
        item.textContent = `@${module}`;
        item.onclick = (e) => {
          e.preventDefault();
          const currentText = userQuestionInput.value;
          const atIndex = currentText.lastIndexOf('@');
          userQuestionInput.value = currentText.substring(0, atIndex) + `@${module} `;
          hideModulesList();
          userQuestionInput.focus();
        };
        modulesListDiv.appendChild(item);
      });
      modulesListDiv.style.display = 'block';
      isListVisible = true;
    });
  };

  const hideModulesList = () => {
    modulesListDiv.style.display = 'none';
    isListVisible = false;
  };

  // ==========================================================
  // === ESTADO PARA FEEDBACK ================================
  // ==========================================================
  let lastAiResponseData = {
    response_id: null,
    user_id: null,
    user_question: null,
    model_used: null,
    context_sources_list: []
  };

  // ==========================================================
  // === CHAT: ENVIO E RENDERIZAÇÃO ===========================
  // ==========================================================
  const removeWelcomeMessage = () => {
    const welcome = responseContainer.querySelector('.alert-welcome');
    if (welcome) welcome.remove();
  };

  const handleAsk = async () => {
    const userQuestion = userQuestionInput.value;
    if (!userQuestion || !userQuestion.trim()) return;

    removeWelcomeMessage();
    if (contextInfoWrapper) contextInfoWrapper.style.display = 'none';

    if (spinner) spinner.style.display = 'inline-block';
    if (sendIcon) sendIcon.style.display = 'none';
    if (askButton) askButton.disabled = true;
    userQuestionInput.disabled = true;

    const userMessageDiv = document.createElement('div');
    userMessageDiv.className = 'lia-message user-message';
    userMessageDiv.textContent = userQuestion;
    responseContainer.appendChild(userMessageDiv);
    responseContainer.scrollTop = responseContainer.scrollHeight;

    userQuestionInput.value = '';

    try {
      const response = await fetch(LIA_API_URLS.ask_llm, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_question: userQuestion,
          selected_model: modelSelector.value
        }),
      });

      const data = await response.json();
      const answerDiv = document.createElement('div');
      answerDiv.className = 'lia-message';

      if (response.ok) {
        // usa "marked" que já está incluído no base.html
        answerDiv.innerHTML = marked.parse(data.answer || '');

        // Atualiza os dados para feedback
        lastAiResponseData.response_id = data.response_id || null;
        lastAiResponseData.user_id = data.user_id || null;
        lastAiResponseData.user_question = data.original_user_question || userQuestion;
        lastAiResponseData.model_used = data.model_used || modelSelector.value;
        lastAiResponseData.context_sources_list = data.context_files || [];

        // Bloco de feedback (👍/👎 + comentário opcional)
        const feedbackHtml = `
          <div class="feedback-section mt-3" style="position: relative; padding-bottom: 2rem;">
            <div class="feedback-buttons" style="position: absolute; bottom: 5px; right: 5px;">
              <small class="d-none">Esta resposta foi útil?</small>
              <div class="btn-group">
                <button class="btn btn-sm feedback-good-btn" title="Útil">👍</button>
                <button class="btn btn-sm feedback-bad-btn" title="Não útil">👎</button>
              </div>
            </div>
            <div class="feedback-comment-area" style="display: none; margin-top: 0.5rem;">
              <textarea class="form-control" rows="2" placeholder="Opcional: Deixe um comentário..."></textarea>
              <button class="btn btn-primary btn-sm mt-2 submit-comment-btn">Enviar</button>
            </div>
            <div class="feedback-message mt-2"></div>
          </div>`;
        answerDiv.innerHTML += feedbackHtml;

        // Fontes/contexto (se houver)
        if (contextInfoWrapper && Array.isArray(data.context_files) && data.context_files.length > 0) {
          const collapseId = `liaContextCollapse-${Date.now()}`;
          const filesList = data.context_files.map(file => `<li class="list-group-item">${file}</li>`).join('');
          contextInfoWrapper.innerHTML = `
            <a class="btn-context" data-bs-toggle="collapse" href="#${collapseId}" role="button" aria-expanded="false">
              Fontes utilizadas <i class="bi bi-chevron-down ms-1"></i>
            </a>
            <div class="collapse" id="${collapseId}">
              <ul class="list-group list-group-flush mt-2">${filesList}</ul>
            </div>`;
          contextInfoWrapper.style.display = 'block';
        }
      } else {
        answerDiv.classList.add('bg-danger', 'text-white');
        answerDiv.innerHTML = `<strong>Erro:</strong> ${data.error || 'Ocorreu um problema.'}`;
        lastAiResponseData = { response_id: null, user_id: null, user_question: null, model_used: null, context_sources_list: [] };
      }
      responseContainer.appendChild(answerDiv);

    } catch (error) {
      console.error("Erro na requisição para ask_llm:", error);
      const errorDiv = document.createElement('div');
      errorDiv.className = 'lia-message bg-danger text-white';
      errorDiv.innerHTML = '<strong>Erro de conexão.</strong> Não foi possível comunicar com o servidor.';
      responseContainer.appendChild(errorDiv);
      lastAiResponseData = { response_id: null, user_id: null, user_question: null, model_used: null, context_sources_list: [] };
    } finally {
      if (spinner) spinner.style.display = 'none';
      if (sendIcon) sendIcon.style.display = 'inline-block';
      if (askButton) askButton.disabled = false;
      userQuestionInput.disabled = false;
      userQuestionInput.focus();
      responseContainer.scrollTop = responseContainer.scrollHeight;
    }
  };

  // ==========================================================
  // === FEEDBACK =============================================
  // ==========================================================
  async function submitFeedback(feedbackSectionElement, rating, comment = null) {
    const { response_id, user_id, user_question, model_used, context_sources_list } = lastAiResponseData;
    const feedbackMessageDiv = feedbackSectionElement.querySelector('.feedback-message');
    const feedbackGoodBtn = feedbackSectionElement.querySelector('.feedback-good-btn');
    const feedbackBadBtn = feedbackSectionElement.querySelector('.feedback-bad-btn');
    const submitCommentBtn = feedbackSectionElement.querySelector('.submit-comment-btn');
    const feedbackButtonsDiv = feedbackSectionElement.querySelector('.feedback-buttons');
    const commentArea = feedbackSectionElement.querySelector('.feedback-comment-area');

    if (!response_id || !user_id) {
      feedbackMessageDiv.innerHTML = '<p class="alert alert-danger p-2">Erro: ID da resposta não disponível.</p>';
      return;
    }

    feedbackGoodBtn.disabled = true;
    feedbackBadBtn.disabled = true;
    if (submitCommentBtn) submitCommentBtn.disabled = true;

    try {
      const response = await fetch(LIA_API_URLS.submit_feedback, {
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
          feedbackButtonsDiv.style.display = 'none';
          commentArea.style.display = 'none';
        }, 1500);
      } else {
        feedbackMessageDiv.innerHTML = `<p class="alert alert-danger p-2">Erro: ${data.error}</p>`;
        feedbackGoodBtn.disabled = false;
        feedbackBadBtn.disabled = false;
        if (submitCommentBtn) submitCommentBtn.disabled = false;
      }
    } catch (error) {
      console.error("Erro ao enviar feedback:", error);
      feedbackMessageDiv.innerHTML = '<p class="alert alert-danger p-2">Erro de conexão ao enviar feedback.</p>';
      feedbackGoodBtn.disabled = false;
      feedbackBadBtn.disabled = false;
      if (submitCommentBtn) submitCommentBtn.disabled = false;
    }
  }

  responseContainer.addEventListener('click', (e) => {
    const target = e.target;
    const feedbackSection = target.closest('.feedback-section');
    if (!feedbackSection) return;

    // Só permite feedback na última resposta da IA
    const allLiaMessages = responseContainer.querySelectorAll('.lia-message:not(.user-message)');
    const lastAiMessageDiv = allLiaMessages[allLiaMessages.length - 1];
    if (!lastAiMessageDiv || !lastAiMessageDiv.contains(feedbackSection)) {
      const oldFeedbackMsg = feedbackSection.querySelector('.feedback-message');
      if (oldFeedbackMsg) {
        oldFeedbackMsg.innerHTML = '<p class="alert alert-warning p-2">Apenas a última resposta pode ser avaliada.</p>';
      }
      return;
    }

    if (target.closest('.feedback-good-btn')) {
      submitFeedback(feedbackSection, 1);
    } else if (target.closest('.feedback-bad-btn')) {
      feedbackSection.dataset.lastRating = 0;
      const commentArea = feedbackSection.querySelector('.feedback-comment-area');
      commentArea.style.display = (commentArea.style.display === 'none' || !commentArea.style.display) ? 'block' : 'none';
    } else if (target.closest('.submit-comment-btn')) {
      const commentInput = feedbackSection.querySelector('textarea');
      submitFeedback(feedbackSection, 0, commentInput.value);
    }
  });

  // ==========================================================
  // === EVENTOS GERAIS =======================================
  // ==========================================================
  userQuestionInput.addEventListener('keypress', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleAsk();
    }
  });

  if (askButton) askButton.addEventListener('click', handleAsk);

  if (modulesHelperBtn) {
    modulesHelperBtn.addEventListener('click', () => {
      if (isListVisible) hideModulesList();
      else {
        const val = userQuestionInput.value;
        userQuestionInput.value += (val.length > 0 && !val.endsWith(' ')) ? ' @' : '@';
        userQuestionInput.focus();
        showModulesList();
      }
    });
  }

  userQuestionInput.addEventListener('input', () => {
    const text = userQuestionInput.value;
    const atIndex = text.lastIndexOf('@');
    if (atIndex !== -1 && !text.includes(' ', atIndex)) {
      showModulesList(text.substring(atIndex + 1));
    } else {
      hideModulesList();
    }
  });

  document.addEventListener('click', (e) => {
    if (!modulesListDiv.contains(e.target) &&
        e.target !== userQuestionInput &&
        e.target !== modulesHelperBtn &&
        !modulesHelperBtn.contains(e.target)) {
      hideModulesList();
    }
  });

  liaModal.addEventListener('shown.bs.modal', () => {
    userQuestionInput.focus();
    if (responseContainer.children.length === 0 || responseContainer.textContent.trim() === '') {
      let welcomeMessage = '';
      if (proactiveModuleName) {
        const formattedModuleName = proactiveModuleName.replace(/-/g, ' ');
        welcomeMessage = `<div class="alert alert-light my-2 alert-welcome">Olá! 👋 Vi que você está na página de <strong>${formattedModuleName}</strong>. Posso ajudar com alguma dúvida sobre este processo?</div>`;
      } else {
        welcomeMessage = '<div class="alert alert-light my-2 alert-welcome">Olá! 👋 Sou a Lia, sua assistente de conhecimento.</div>';
      }
      responseContainer.innerHTML = welcomeMessage;
      lastAiResponseData = { response_id: null, user_id: null, user_question: null, model_used: null, context_sources_list: [] };
    }
    if (proactiveModuleId && !userQuestionInput.value.includes(`@${proactiveModuleId}`)) {
      userQuestionInput.value = `@${proactiveModuleId} `;
    }
  });

  // ==========================================================
  // === AVISO "LIA EM DESENVOLVIMENTO (BETA)" ================
  // ==========================================================
  (function () {
    const OVERLAY_ID = 'lia-warning-overlay';
    const DONT_SHOW_KEY = 'lia_warning_dismissed_v1';
    const overlay = document.getElementById(OVERLAY_ID);
    const btnConfirm = document.getElementById('liaWarningConfirm');
    const dontShowAgain = document.getElementById('liaDontShowAgain');

    if (!overlay) return;

    function showOverlay() {
      const dismissed = localStorage.getItem(DONT_SHOW_KEY) === '1';
      if (dismissed) return;
      overlay.classList.add('show');
      document.body.classList.add('lia-blur');
      overlay.setAttribute('aria-hidden', 'false');
      btnConfirm?.focus?.();
    }

    function hideOverlay() {
      overlay.classList.remove('show');
      document.body.classList.remove('lia-blur');
      overlay.setAttribute('aria-hidden', 'true');
    }

    btnConfirm?.addEventListener('click', () => {
      if (dontShowAgain?.checked) {
        try { localStorage.setItem(DONT_SHOW_KEY, '1'); } catch (e) {}
      }
      hideOverlay();
    });

    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && overlay.classList.contains('show')) hideOverlay();
    });

    // Mostra o aviso sempre que abrir o modal da LIA
    // Comando para limpar e voltar o não mostra novamente, no Console:
    // Digitar: allow pasting
    // localStorage.removeItem('lia_warning_dismissed_v1');
    liaModal.addEventListener('show.bs.modal', () => {
      showOverlay();
    });
  })();
});

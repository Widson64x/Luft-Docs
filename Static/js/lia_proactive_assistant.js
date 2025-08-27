/**
 * lia_proactive_assistant.js
 * (Versão 3.0 - Com Personalidade Aleatória)
 */

function initializeProactiveAssistant(context, config) {
    // Elementos da DOM
    const liaFloatingButton = document.querySelector('.floating-lia-btn');
    const liaProactiveToast = document.getElementById('lia-proactive-toast');
    const liaToastText = liaProactiveToast ? liaProactiveToast.querySelector('.toast-content span') : null; // Pega o <span> para o texto
    const liaModal = document.getElementById('liaModal');
    const liaResponseContainer = document.getElementById('liaResponseContainer');

    if (!liaFloatingButton || !liaModal || !liaToastText) {
        console.warn("Assistente Proativo: Elementos essenciais (botão, modal ou toast) não encontrados.");
        return;
    }

    // Variáveis de estado
    let inactivityTimer;
    let promptResetTimer;
    let currentProactiveMessage = ''; // Armazena a mensagem escolhida

    const resetInactivityTimer = () => {
        if (liaFloatingButton.classList.contains('lia-proactive')) {
            return;
        }
        clearTimeout(inactivityTimer);
        clearTimeout(promptResetTimer);
        inactivityTimer = setTimeout(enterProactiveMode, config.timeout);
    };

    /**
     * ATUALIZADO: Escolhe uma mensagem aleatória e a exibe.
     */
    const enterProactiveMode = () => {
        // 1. Verifica se temos um array de mensagens no contexto
        if (!context.messages || context.messages.length === 0) {
            return; // Não faz nada se não houver mensagens
        }

        // 2. Escolhe uma mensagem aleatória do array
        const randomIndex = Math.floor(Math.random() * context.messages.length);
        const chosenMessage = context.messages[randomIndex];
        currentProactiveMessage = chosenMessage.modal; // Armazena a mensagem completa para o modal

        // 3. Atualiza o texto do toast com a mensagem curta
        liaToastText.textContent = chosenMessage.toast;

        // 4. Ativa os elementos visuais
        console.log(`Assistente Proativo: Entrando em modo proativo com a mensagem: "${chosenMessage.toast}"`);
        liaFloatingButton.classList.add('lia-proactive');
        liaProactiveToast.classList.add('show');

        // 5. Configura o timer para resetar
        promptResetTimer = setTimeout(() => {
            console.log("Assistente Proativo: Resetando o prompt por tempo esgotado.");
            exitProactiveMode();
            resetInactivityTimer();
        }, config.promptTimeout);
    };
    
    const exitProactiveMode = () => {
        liaFloatingButton.classList.remove('lia-proactive');
        liaProactiveToast.classList.remove('show');
        clearTimeout(promptResetTimer);
    };

    /**
     * ATUALIZADO: Usa a mensagem que foi previamente escolhida.
    */
    const handleLiaButtonClick = () => {
        if (liaFloatingButton.classList.contains('lia-proactive')) {
            exitProactiveMode();
            
            if (liaResponseContainer.children.length === 0) {
                if (typeof appendLiaMessage === 'function') {
                    // Usa a mensagem completa que foi armazenada
                    appendLiaMessage(currentProactiveMessage);
                } else {
                    liaResponseContainer.innerHTML = `<div class="lia-message">${marked.parse(currentProactiveMessage)}</div>`;
                }
            }
        }
    };

    ['mousemove', 'mousedown', 'keypress', 'scroll', 'touchstart'].forEach(event =>
        document.addEventListener(event, resetInactivityTimer, { passive: true })
    );

    liaFloatingButton.addEventListener('click', handleLiaButtonClick);
    
    resetInactivityTimer();
    console.log("Assistente Proativo: Detecção de inatividade (v3 - com personalidade) iniciada.");
}
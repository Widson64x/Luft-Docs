document.addEventListener('DOMContentLoaded', () => {
    if (typeof initializeProactiveAssistant === 'function') {
        const moduleContainer = document.querySelector('.module-container');
        if (!moduleContainer) return;

        const moduleName = moduleContainer.dataset.moduleName || 'este módulo';
        const moduleId = moduleContainer.dataset.moduleId || '';
        const relatedCount = moduleContainer.dataset.relatedCount || 0;

        const possibleMessages = [{
            toast: "Psiu! Quer uma ajuda?",
            modal: `Olá! 👋 Notei que você está lendo sobre o módulo **${moduleName}**. Posso te ajudar a encontrar uma informação específica, fazer um resumo ou explicar algum tópico?`
        }, {
            toast: "Sabia que eu posso resumir?",
            modal: `Estou vendo que você está focado(a) em **${moduleName}**. Que tal um resumo rápido dos pontos mais importantes para começar?`
        }, {
            toast: "Uma curiosidade sobre este módulo...",
            modal: `Uma curiosidade sobre **${moduleName}**: ele tem links para **${relatedCount}** outros módulos! Quer que eu mostre quais são ou procure por um tópico específico nele?`
        }, {
            toast: "Encontrou o que procurava?",
            modal: `Olá! Se estiver com dificuldade para encontrar algo em **${moduleName}**, é só me avisar. Posso fazer uma busca inteligente para você. 😉`
        }, ];

        const proactiveContext = {
            type: 'module_page',
            moduleId: moduleId,
            moduleName: moduleName,
            messages: possibleMessages
        };

        const timerConfig = {
            timeout: 120000, // 2 minutos
            promptTimeout: 300000 // 5 minutos
        };

        initializeProactiveAssistant(proactiveContext, timerConfig);
    }
});
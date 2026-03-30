document.addEventListener('DOMContentLoaded', () => {
    const containerModulo = document.querySelector('.module-container');
    if (!containerModulo) return;

    const nomeModulo       = containerModulo.dataset.moduleName  || 'este módulo';
    const idModulo         = containerModulo.dataset.moduleId    || '';
    const totalRelacionados = containerModulo.dataset.relatedCount || 0;

    const mensagensProativas = [{
        toast: "Psiu! Quer uma ajuda?",
        modal: `Olá! 👋 Notei que você está lendo sobre o módulo **${nomeModulo}**. Posso te ajudar a encontrar uma informação específica, fazer um resumo ou explicar algum tópico?`
    }, {
        toast: "Sabia que eu posso resumir?",
        modal: `Estou vendo que você está focado(a) em **${nomeModulo}**. Que tal um resumo rápido dos pontos mais importantes para começar?`
    }, {
        toast: "Uma curiosidade sobre este módulo...",
        modal: `Uma curiosidade sobre **${nomeModulo}**: ele tem links para **${totalRelacionados}** outros módulos! Quer que eu mostre quais são ou procure por um tópico específico nele?`
    }, {
        toast: "Encontrou o que procurava?",
        modal: `Olá! Se estiver com dificuldade para encontrar algo em **${nomeModulo}**, é só me avisar. Posso fazer uma busca inteligente para você. 😉`
    }];

    const contextoProativo = {
        tipo: 'pagina_modulo',
        idModulo,
        nomeModulo,
        messages: mensagensProativas
    };

    const configTimers = {
        timeout: 120000,      // 2 minutos de inatividade
        promptTimeout: 300000 // 5 minutos de exibição do toast
    };

    new AssistenteProativo(contextoProativo, configTimers);
});

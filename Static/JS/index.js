/**
 * Arquivo de integracao da Pagina Inicial (Index).
 * * Implementa padroes de Orientacao a Objetos para o gerenciamento de modulos,
 * isolamento de lógicas de renderizacao e animacao de fundo.
 */

class GerenciadorModulos {
    /**
     * Inicializa a classe responsavel por consultar e renderizar os modulos.
     * * @param {string} idInputFiltro - O ID do elemento de input de busca.
     * @param {string} idGridModulos - O ID do container onde os cards serao renderizados.
     * @param {string} idContainerPaginacao - O ID do container da paginacao.
     * @param {string} idMensagemVazia - O ID do container exibido quando nao ha resultados.
     */
    constructor(idInputFiltro, idGridModulos, idContainerPaginacao, idMensagemVazia) {
        this.inputFiltro = document.getElementById(idInputFiltro);
        this.gridModulos = document.getElementById(idGridModulos);
        this.containerPaginacao = document.getElementById(idContainerPaginacao);
        this.mensagemVazia = document.getElementById(idMensagemVazia);
        
        const parametrosUrl = new URLSearchParams(window.location.search);
        this.tokenAutenticacao = parametrosUrl.get('token') || '';
        this.timeoutBusca = null;

        this.inicializarEventos();
    }

    /**
     * Configura os ouvintes de eventos para interacao do usuario (busca e paginacao).
     */
    inicializarEventos() {
        if (!this.inputFiltro || !this.gridModulos) return;

        this.inputFiltro.addEventListener('input', (evento) => {
            clearTimeout(this.timeoutBusca);
            this.timeoutBusca = setTimeout(() => {
                this.buscarModulos(evento.target.value.trim(), 1);
            }, 300);
        });

        if (this.containerPaginacao) {
            this.containerPaginacao.addEventListener('click', (evento) => {
                evento.preventDefault();
                const elementoAlvo = evento.target.closest('a');
                if (elementoAlvo && elementoAlvo.dataset.page) {
                    const pagina = parseInt(elementoAlvo.dataset.page, 10);
                    if (!isNaN(pagina) && !elementoAlvo.classList.contains('disabled')) {
                        this.buscarModulos(this.inputFiltro.value.trim(), pagina);
                        window.scrollTo({ top: 0, behavior: 'smooth' });
                    }
                }
            });
        }
    }

    /**
     * Realiza a chamada a API para buscar modulos baseados em filtros e paginacao.
     * * @param {string} termoBusca - Palavra-chave para filtragem dos modulos.
     * @param {number} pagina - O numero da pagina atual solicitada.
     */
    async buscarModulos(termoBusca = '', pagina = 1) {
        if (!this.gridModulos) return;

        this.gridModulos.innerHTML = '<div class="col-12 text-center py-5 text-muted">Carregando modulos...</div>';
        this.mensagemVazia.style.display = 'none';
        this.containerPaginacao.innerHTML = '';

        try {
            const parametrosQuery = new URLSearchParams({
                search: termoBusca,
                page: String(pagina),
                token: this.tokenAutenticacao
            }).toString();

            const prefixoBase = window.__BASE_PREFIX__ || '/luft-docs';
            const resposta = await fetch(`${prefixoBase}/api/modules?${parametrosQuery}`);
            
            if (!resposta.ok) {
                throw new Error(`Erro no servidor: ${resposta.statusText}`);
            }
            
            const dadosProcessados = await resposta.json();
            this.gridModulos.innerHTML = '';
            
            if (dadosProcessados.cards && dadosProcessados.cards.length > 0) {
                this.renderizarCards(dadosProcessados.cards, dadosProcessados.token || this.tokenAutenticacao);
                this.renderizarPaginacao(dadosProcessados.current_page, dadosProcessados.total_pages);
            } else {
                this.mensagemVazia.style.display = 'block';
            }
        } catch (erro) {
            console.error("Falha na obtencao de dados da API:", erro);
            this.gridModulos.innerHTML = '<div class="col-12 text-center py-5 text-danger">Falha ao carregar os modulos. Verifique a conexao.</div>';
        }
    }

    /**
     * Constroi e insere os cards de modulos no DOM baseando-se no layout LuftCore.
     * * @param {Array} modulos - Lista de objetos de modulos retornados pela API.
     * @param {string} tokenAtual - Token ativo para injecao nas URLs de destino.
     */
    renderizarCards(modulos, tokenAtual) {
        const prefixoBase = window.__BASE_PREFIX__ || '/luft-docs';

        modulos.forEach((modulo) => {
            let htmlCard = '';
            
            if (modulo.type === 'create_card') {
                htmlCard = `
                    <a href="${prefixoBase}/editor/novo?token=${encodeURIComponent(tokenAtual)}" class="luft-index-card luft-index-card-dashed">
                        <i class="ph-thin ph-plus-circle luft-index-card-icon" style="color: var(--luft-text-muted);"></i>
                        <h5 class="luft-index-card-title">Criar Novo Modulo</h5>
                    </a>
                `;
            } else {
                // Conversão paleativa de bi-icons para ph-icons caso venha do banco
                const iconeSaneado = (modulo.icone || 'ph-box').replace('bi bi-', 'ph-bold ph-');
                
                let botoesAcao = '';
                if (modulo.has_content) {
                    botoesAcao += `<a class="luft-btn luft-btn-primary" href="${prefixoBase}/modulo/?modulo=${modulo.id}&token=${encodeURIComponent(tokenAtual)}">Ver Conteudo</a>`;
                }
                if (modulo.show_tecnico_button) {
                    botoesAcao += `<a class="luft-btn luft-btn-outline" href="${prefixoBase}/modulo/?modulo_tecnico=${modulo.id}&token=${encodeURIComponent(tokenAtual)}"><i class="ph-bold ph-wrench"></i> Tecnico</a>`;
                }

                htmlCard = `
                    <div class="luft-index-card">
                        <i class="${iconeSaneado} luft-index-card-icon"></i>
                        <h5 class="luft-index-card-title">${modulo.nome}</h5>
                        <p class="luft-index-card-desc">${modulo.descricao}</p>
                        <div class="luft-index-card-actions">
                            ${botoesAcao}
                        </div>
                    </div>
                `;
            }
            this.gridModulos.insertAdjacentHTML('beforeend', htmlCard);
        });
    }

    /**
     * Renderiza o componente de paginacao padronizado.
     * * @param {number} paginaAtual - O indice da pagina atualmente ativa.
     * @param {number} totalPaginas - A quantidade total de paginas disponiveis.
     */
    renderizarPaginacao(paginaAtual, totalPaginas) {
        if (totalPaginas <= 1) return;

        let htmlPaginacao = '';
        const classeAnterior = paginaAtual === 1 ? 'disabled' : '';
        htmlPaginacao += `<a href="#" class="luft-page-btn ${classeAnterior}" data-page="${paginaAtual - 1}">Anterior</a>`;
        
        for (let indice = 1; indice <= totalPaginas; indice++) {
            const classeAtiva = indice === paginaAtual ? 'active' : '';
            htmlPaginacao += `<a href="#" class="luft-page-btn ${classeAtiva}" data-page="${indice}">${indice}</a>`;
        }

        const classeProxima = paginaAtual === totalPaginas ? 'disabled' : '';
        htmlPaginacao += `<a href="#" class="luft-page-btn ${classeProxima}" data-page="${paginaAtual + 1}">Proxima</a>`;
        
        this.containerPaginacao.innerHTML = htmlPaginacao;
    }
}

/**
 * Funcao solitaria base para instanciar e engatilhar as classes necessarias na pagina atual.
 */
function InicializarPaginaIndex() {
    const gerenciador = new GerenciadorModulos(
        'inputFiltroModulos', 
        'gridModulos', 
        'containerPaginacao', 
        'mensagemSemResultados'
    );
    
    // Inicia requisicao padrao ao montar
    gerenciador.buscarModulos();

    const animacao = new AnimacaoFundo('containerAnimacaoFundo');
    animacao.iniciar();
}

// Inicializador raiz atrelado ao ciclo de vida do DOM
document.addEventListener('DOMContentLoaded', InicializarPaginaIndex);
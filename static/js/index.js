// =========================================================================
// LÓGICA DE BUSCA, PAGINAÇÃO, RENDERIZAÇÃO E ALERTAS
// =========================================================================
document.addEventListener('DOMContentLoaded', () => {
    // ---- Lógica dos Módulos ----
    const filterInput = document.getElementById('filterInput');
    const modulesRow = document.getElementById('modules-row');
    const noResultsMessage = document.getElementById('no-results-message');
    const paginationContainer = document.getElementById('pagination-container');

    // Se os elementos não existirem na página, não continue.
    if (!modulesRow || !paginationContainer || !filterInput) return;
    
    const urlParams = new URLSearchParams(window.location.search);
    const TOKEN = urlParams.get('token');
    
    let searchTimeout;

    // Função principal que busca e renderiza os dados da API
    async function fetchAndRenderCards(searchTerm = '', page = 1) {
        modulesRow.innerHTML = '<div class="col-12 text-center py-5"><div class="spinner-border text-primary" role="status"><span class="visually-hidden">Carregando...</span></div></div>';
        noResultsMessage.style.display = 'none';
        paginationContainer.innerHTML = '';

        try {
            const response = await fetch(`/api/modules?search=${encodeURIComponent(searchTerm)}&page=${page}&token=${TOKEN}`);
            if (!response.ok) throw new Error(`Erro na rede: ${response.statusText}`);
            
            const data = await response.json();
            
            modulesRow.innerHTML = '';
            
            if (data.cards && data.cards.length > 0) {
                renderCards(data.cards, data.token);
                renderPagination(data.current_page, data.total_pages);
            } else {
                noResultsMessage.style.display = 'block';
            }
        } catch (error) {
            console.error("Falha ao buscar módulos:", error);
            modulesRow.innerHTML = '<div class="col-12 text-center py-5 text-danger"><strong>Oops!</strong> Falha ao carregar os módulos. Verifique sua conexão e tente novamente.</div>';
        }
    }

    // Função para renderizar os cards no DOM
    function renderCards(cards, token) {
        cards.forEach((m, index) => {
            let cardHtml = '';
            if (m.type === 'create_card') {
                cardHtml = `
                    <div class="col-12 col-sm-6 col-md-4 d-flex module-card-wrapper">
                        <a href="/editor/novo?token=${token}" class="card modern-card add-new-card w-100 shadow-none border-0 text-decoration-none" style="--card-index: ${index}">
                            <div class="card-body d-flex flex-column align-items-center justify-content-center" style="flex:1;">
                                <i class="bi bi-plus-circle-dotted display-4 mb-3"></i>
                                <h5 class="card-title">Criar Novo Módulo</h5>
                            </div>
                        </a>
                    </div>
                `;
            } else {
                cardHtml = `
                    <div class="col-12 col-sm-6 col-md-4 d-flex module-card-wrapper">
                        <div class="card modern-card w-100 shadow-sm border-0" style="--card-index: ${index}">
                            <div class="card-body">
                                <i class="bi ${m.icone || 'bi-box'} display-4 text-primary mb-3"></i>
                                <h5 class="card-title">${m.nome}</h5>
                                <p class="card-text">${m.descricao}</p>
                            </div>
                            <div class="pb-3 text-center">
                                ${m.has_content ? `
                                <a class="btn btn-outline-primary modern-btn me-2 page-transition-btn" href="/modulo/?modulo=${m.id}&token=${token}">
                                    <i class="bi bi-search"></i> Ver módulo
                                </a>` : ''}
                                ${m.show_tecnico_button ? `
                                <a class="btn btn-outline-secondary modern-btn ms-2 page-transition-btn" href="/modulo/?modulo_tecnico=${m.id}&token=${token}">
                                    <i class="bi bi-tools"></i> Módulo Técnico
                                </a>` : ''}
                            </div>
                        </div>
                    </div>
                `;
            }
            modulesRow.insertAdjacentHTML('beforeend', cardHtml);
        });
        // Re-aplica o listener de transição para os novos botões criados
        setupPageTransitionListeners();
    }

    // Função para renderizar a paginação no DOM
    function renderPagination(currentPage, totalPages) {
        if (totalPages <= 1) {
            paginationContainer.innerHTML = '';
            return;
        }

        let paginationHtml = '<nav aria-label="Navegação dos módulos"><ul class="pagination">';
        paginationHtml += `<li class="page-item ${currentPage === 1 ? 'disabled' : ''}"><a class="page-link" href="#" data-page="${currentPage - 1}">Anterior</a></li>`;
        
        for (let i = 1; i <= totalPages; i++) {
            paginationHtml += `<li class="page-item ${i === currentPage ? 'active' : ''}"><a class="page-link" href="#" data-page="${i}">${i}</a></li>`;
        }

        paginationHtml += `<li class="page-item ${currentPage === totalPages ? 'disabled' : ''}"><a class="page-link" href="#" data-page="${currentPage + 1}">Próxima</a></li>`;
        paginationHtml += '</ul></nav>';
        
        paginationContainer.innerHTML = paginationHtml;
    }

    // Listener para o filtro com debounce
    filterInput.addEventListener('input', (e) => {
        clearTimeout(searchTimeout);
        searchTimeout = setTimeout(() => {
            fetchAndRenderCards(e.target.value.trim(), 1);
        }, 300);
    });
    
    // Listener para paginação com delegação de eventos
    paginationContainer.addEventListener('click', (e) => {
        e.preventDefault();
        const target = e.target;
        if (target.tagName === 'A' && target.dataset.page) {
            const page = parseInt(target.dataset.page, 10);
            const searchTerm = filterInput.value.trim();
            if (!isNaN(page) && !target.closest('.page-item.disabled')) {
                fetchAndRenderCards(searchTerm, page);
                window.scrollTo({ top: 0, behavior: 'smooth' }); // Rola para o topo
            }
        }
    });

    // Carga inicial dos dados
    fetchAndRenderCards();

    // ---- Lógica de Transição de Página ----
    function setupPageTransitionListeners() {
        document.querySelectorAll('.page-transition-btn').forEach(btn => {
            btn.removeEventListener('click', handleTransitionClick); 
            btn.addEventListener('click', handleTransitionClick);
        });
    }

    function handleTransitionClick(event) {
        event.preventDefault();
        const destinationUrl = event.currentTarget.href;
        document.body.classList.add('page-transition-out');
        setTimeout(() => {
            window.location.href = destinationUrl;
        }, 500); // Duração da animação
    }

    // Configuração inicial dos listeners de transição
    setupPageTransitionListeners();

    // ---- Lógica para fechar alertas (Flashed Messages) ----
    const alerts = document.querySelectorAll('.alert');
    const alertTimeout = 5000;
    alerts.forEach((alert) => {
        setTimeout(() => {
            new bootstrap.Alert(alert).close();
        }, alertTimeout);
    });
});

// =========================================================================
// LÓGICA DA ANIMAÇÃO DE FUNDO
// =========================================================================
const bgContainer = document.querySelector('.bg-icons');
if (bgContainer) {
    let bgAnimationFrameId = null;

    function getAnimationParameters() {
        const quantity = parseInt(localStorage.getItem('ld_bg_quantity') || '50', 10);
        const speedFactor = parseFloat(localStorage.getItem('ld_bg_speed') || '1.0');
        const randomnessFactor = 1 + (speedFactor - 1) * 0.5;
        return { quantity, speedFactor, randomnessFactor };
    }

    function iniciarAnimacaoComColisao() {
        const { quantity, speedFactor, randomnessFactor } = getAnimationParameters();
        const iconsData = [];
        const screenWidth = bgContainer.offsetWidth;
        const screenHeight = bgContainer.offsetHeight;
        
        // Pega a URL do JSON do atributo data-* no HTML
        const iconsUrl = bgContainer.dataset.iconsUrl;
        if (!iconsUrl) {
            console.error('URL do arquivo de ícones não encontrada.');
            return;
        }

        fetch(iconsUrl)
            .then(res => res.json())
            .then(availableIcons => {
                for (let i = 0; i < quantity; i++) {
                    const el = document.createElement('i');
                    const size = (Math.random() * 32 * randomnessFactor + 16);

                    el.className = `bi ${availableIcons[Math.floor(Math.random() * availableIcons.length)]} bg-icon`;
                    el.style.fontSize = `${size}px`;
                    el.style.position = 'absolute';
                    bgContainer.appendChild(el);

                    iconsData.push({
                        element: el,
                        x: Math.random() * (screenWidth - size),
                        y: Math.random() * (screenHeight - size),
                        dx: (Math.random() - 0.5) * 1.5 * speedFactor,
                        dy: (Math.random() - 0.5) * 1.5 * speedFactor,
                        size: size
                    });
                }
                animate();
            })
            .catch(console.error);

        function animate() {
            iconsData.forEach(icon => {
                icon.x += icon.dx;
                icon.y += icon.dy;
                if (icon.x <= 0 || icon.x + icon.size >= screenWidth) { icon.dx *= -1; }
                if (icon.y <= 0 || icon.y + icon.size >= screenHeight) { icon.dy *= -1; }
                icon.element.style.transform = `translate(${icon.x}px, ${icon.y}px)`;
            });
            bgAnimationFrameId = requestAnimationFrame(animate);
        }
    }

    function iniciarAnimacaoOriginal() {
        const { quantity, speedFactor, randomnessFactor } = getAnimationParameters();
        const iconsUrl = bgContainer.dataset.iconsUrl;
        if (!iconsUrl) return;

        fetch(iconsUrl)
            .then(res => res.json())
            .then(icons => {
                for (let i = 0; i < quantity; i++) {
                    const cls = icons[Math.floor(Math.random() * icons.length)];
                    const el = document.createElement('i');
                    el.className = `bi ${cls} bg-icon`;

                    el.style.fontSize = `${(Math.random() * 2 * randomnessFactor + 1).toFixed(2)}rem`;
                    el.style.left = `${Math.random() * 100}%`;
                    el.style.bottom = '-2rem';
                    el.style.animationName = 'iconRise';
                    el.style.animationTimingFunction = 'ease-in-out';
                    el.style.animationIterationCount = 'infinite';
                    el.style.animationDelay = `${(Math.random() * 5).toFixed(2)}s`;
                    const baseDuration = 10 + Math.random() * 10;
                    el.style.animationDuration = `${(baseDuration / speedFactor).toFixed(2)}s`;
                    bgContainer.appendChild(el);
                }
            })
            .catch(console.error);
    }

    window.mudarAnimacao = function(modo) {
        if (bgAnimationFrameId) {
            cancelAnimationFrame(bgAnimationFrameId);
            bgAnimationFrameId = null;
        }
        bgContainer.innerHTML = '';

        if (modo === 'original') {
            iniciarAnimacaoOriginal();
        } else {
            iniciarAnimacaoComColisao();
        }
    }

    // Inicia a animação de fundo preferida do usuário
    const savedAnimation = localStorage.getItem('ld_bgAnimation') || 'colisao';
    mudarAnimacao(savedAnimation);
}
/**
 * search_recommendations.js
 * Gerencia as funcionalidades interativas da página de busca, incluindo
 * recomendações paginadas e autocomplete, usando componentes de UI customizados.
 */
document.addEventListener('DOMContentLoaded', function() {
    const token = document.body.dataset.token || '';
    const recommendationsContainer = document.getElementById('recommendations-container');
    const searchInput = document.getElementById('q');
    const autocompleteResults = document.getElementById('autocomplete-results');
    const searchForm = document.getElementById('search-form');

    // --- Variáveis de Estado para Paginação ---
    let allRecommendations = [];
    let popularSearches = [];
    let currentPage = 1;
    const itemsPerPage = 5;

    /**
     * Busca os dados da API e inicia a renderização.
     */
    function fetchAndDisplayData() {
        if (!recommendationsContainer) return;

        fetch(`/search/api/recommendations?token=${token}`)
            .then(response => {
                if (!response.ok) throw new Error('Falha ao buscar recomendações da API.');
                return response.json();
            })
            .then(data => {
                allRecommendations = data.hybrid_recommendations || [];
                popularSearches = (data.popular_searches || []).slice(0, 10);
                currentPage = 1;
                displayPage();
            })
            .catch(error => {
                console.error('Erro ao buscar recomendações:', error);
                // ATUALIZADO: Usando o componente .custom-alert
                recommendationsContainer.innerHTML = `
                    <div class='custom-alert alert-danger'>
                        <i class="bi bi-exclamation-triangle-fill alert-icon"></i>
                        <span>Não foi possível carregar as recomendações.</span>
                    </div>`;
            });
    }

    /**
     * Renderiza o conteúdo da página atual (cards, paginação e buscas populares).
     */
    function displayPage() {
        if (!recommendationsContainer) return;

        if (allRecommendations.length === 0 && popularSearches.length === 0) {
            recommendationsContainer.innerHTML = "<div class='no-results'><h5>Nenhuma recomendação disponível.</h5><p>Comece a usar o sistema para gerarmos sugestões para você.</p></div>";
            return;
        }

        let finalHtml = '';

        // 1. Renderiza os cards de recomendação para a PÁGINA ATUAL
        const startIndex = (currentPage - 1) * itemsPerPage;
        const endIndex = startIndex + itemsPerPage;
        const paginatedItems = allRecommendations.slice(startIndex, endIndex);

        if (paginatedItems.length > 0) {
            // ATUALIZADO: Usando a classe .search-summary
            let hybridHtml = `<h4 class="search-summary">Recomendado para Você</h4>`;
            paginatedItems.forEach((result, index) => {
                // Adicionando um delay de animação para o efeito escalonado
                hybridHtml += buildResultCard(result, index * 100);
            });
            finalHtml += hybridHtml;
        }

        // 2. Constrói e adiciona a barra de navegação da paginação
        finalHtml += buildPagination();

        // 3. Renderiza as buscas populares
        if (popularSearches.length > 0) {
            // ATUALIZADO: Usando a classe .recommendation-list
            let popularHtml = `
                <div class="recommendations-section">
                    <h5><i class="fas fa-chart-line me-2 text-success"></i>Buscas Populares</h5>
                    <div class="recommendation-list">`;
            popularSearches.forEach(item => {
                const searchUrl = `/search?q=${encodeURIComponent(item.query_term)}&token=${token}`;
                // ATUALIZADO: Usando a classe .recommendation-item
                popularHtml += `<a href="${searchUrl}" class="recommendation-item"><i class="fas fa-search me-2"></i>${item.query_term}</a>`;
            });
            popularHtml += `</div></div>`;
            finalHtml += popularHtml;
        }
        
        recommendationsContainer.innerHTML = finalHtml;
        setupPaginationListener();
    }
    
    /**
     * Constrói o HTML para a barra de navegação da paginação customizada.
     */
    function buildPagination() {
        const totalPages = Math.ceil(allRecommendations.length / itemsPerPage);
        if (totalPages <= 1) return '';

        // ATUALIZADO: Usando a classe .custom-pagination e estrutura simplificada
        let paginationHtml = '<nav aria-label="Paginação de recomendações"><ul class="custom-pagination">';

        paginationHtml += `<li class="${currentPage === 1 ? 'disabled' : ''}"><a href="#" data-page="${currentPage - 1}">Anterior</a></li>`;
        for (let i = 1; i <= totalPages; i++) {
            paginationHtml += `<li class="${i === currentPage ? 'active' : ''}"><a href="#" data-page="${i}">${i}</a></li>`;
        }
        paginationHtml += `<li class="${currentPage === totalPages ? 'disabled' : ''}"><a href="#" data-page="${currentPage + 1}">Próxima</a></li>`;
        
        paginationHtml += '</ul></nav>';
        return paginationHtml;
    }

    /**
     * Adiciona o listener de eventos para os cliques na paginação.
     */
    function setupPaginationListener() {
        // ATUALIZADO: Selecionando pela nova classe customizada
        const paginationElement = recommendationsContainer.querySelector('.custom-pagination');
        if (paginationElement) {
            paginationElement.addEventListener('click', function(e) {
                e.preventDefault();
                const target = e.target;
                if (target.tagName === 'A' && !target.parentElement.classList.contains('disabled') && !target.parentElement.classList.contains('active')) {
                    const newPage = parseInt(target.dataset.page, 10);
                    if (newPage !== currentPage) {
                        currentPage = newPage;
                        displayPage();
                        recommendationsContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
                    }
                }
            });
        }
    }

    /**
     * Constrói o HTML para um único card de resultado/recomendação.
     * Adiciona um delay de animação para um efeito de entrada escalonado.
     */
    function buildResultCard(result, animationDelay = 0) {
        let previewHtml = '';
        if (result.preview && result.preview.path) {
            const mediaTag = result.preview.type === 'image'
                ? `<img src="${result.preview.path}" alt="Preview">`
                : `<video src="${result.preview.path}" muted autoplay loop playsinline></video>
                   <div class="video-overlay"><i class="fas fa-play-circle play-icon"></i></div>`;
            previewHtml = `<div class="result-media-preview">${mediaTag}</div>`;
        }
        const resultUrl = `${result.url}&token=${token}`;
        return `
            <a href="${resultUrl}" class="text-decoration-none">
                <div class="result-card" style="animation-delay: ${animationDelay}ms">
                    ${previewHtml}
                    <div class="result-content">
                        <div class="result-card-header">
                            <i class="${result.module_icon || 'fas fa-file-alt'} icon"></i>
                            <span class="module-name">${result.module_nome}</span>
                            <span class="doc-type-badge">${result.doc_type}</span>
                            <span class="ms-auto access-indicator" title="Visualizações">
                                <i class="fas fa-eye me-1"></i>${result.access_count || 0}
                            </span>
                        </div>
                        <p class="result-snippet m-0">${result.snippet}</p>
                    </div>
                </div>
            </a>
        `;
    }
    
    /**
     * Configura a funcionalidade de auto-complete para a barra de busca principal.
     */
    function setupAutocomplete() {
        if (!searchInput || !autocompleteResults) return;

        let debounceTimer;
        searchInput.addEventListener('input', function() {
            const query = this.value;
            clearTimeout(debounceTimer);
            if (query.length < 2) {
                autocompleteResults.style.display = 'none';
                return;
            }
            debounceTimer = setTimeout(() => {
                fetch(`/search/api/autocomplete?q=${query}&token=${token}`)
                    .then(response => response.json())
                    .then(suggestions => {
                        let html = '';
                        if (suggestions && suggestions.length > 0) {
                            suggestions.forEach(suggestion => {
                                // A classe .autocomplete-item é estilizada pelo nosso CSS
                                html += `<a href="#" class="autocomplete-item" data-suggestion="${suggestion}">${suggestion}</a>`;
                            });
                            autocompleteResults.innerHTML = html;
                            autocompleteResults.style.display = 'block';
                        } else {
                            autocompleteResults.style.display = 'none';
                        }
                    })
                    .catch(error => console.error('Erro no auto-complete:', error));
            }, 250);
        });

        autocompleteResults.addEventListener('click', function(e) {
            e.preventDefault();
            if (e.target.classList.contains('autocomplete-item')) {
                searchInput.value = e.target.dataset.suggestion;
                autocompleteResults.style.display = 'none';
                if(searchForm) searchForm.submit();
            }
        });

        document.addEventListener('click', function(e) {
            if (!searchInput.contains(e.target) && !autocompleteResults.contains(e.target)) {
                autocompleteResults.style.display = 'none';
            }
        });
    }

    // --- INICIALIZAÇÃO DAS FUNÇÕES DA PÁGINA ---
    // Inicia a busca por recomendações se o container existir.
    fetchAndDisplayData();
    // Inicia o autocomplete se o campo de busca existir.
    setupAutocomplete();
});
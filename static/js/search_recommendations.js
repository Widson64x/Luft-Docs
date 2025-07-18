/**
 * search_recommendations.js
 * Gerencia as funcionalidades interativas da página de busca, incluindo recomendações paginadas.
 */
document.addEventListener('DOMContentLoaded', function() {
    const token = document.body.dataset.token || '';
    const recommendationsContainer = document.getElementById('recommendations-container');
    
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
                // Armazena os dados recebidos
                allRecommendations = data.hybrid_recommendations || [];
                // Limita as buscas populares aos 10 primeiros, garantindo o requisito
                popularSearches = (data.popular_searches || []).slice(0, 10);
                
                // Define a página inicial para 1 e exibe
                currentPage = 1;
                displayPage();
            })
            .catch(error => {
                console.error('Erro ao buscar recomendações:', error);
                recommendationsContainer.innerHTML = "<div class='alert alert-danger'>Não foi possível carregar as recomendações.</div>";
            });
    }

    /**
     * Renderiza o conteúdo da página atual (cards, paginação e buscas populares).
     */
    function displayPage() {
        if (!recommendationsContainer) return;

        if (allRecommendations.length === 0 && popularSearches.length === 0) {
             recommendationsContainer.innerHTML = "<div class='no-results'><h5>Nenhuma recomendação disponível.</h5><p class='text-muted'>Comece a usar o sistema para gerarmos sugestões para você.</p></div>";
             return;
        }

        let finalHtml = '';

        // 1. Renderiza os cards de recomendação para a PÁGINA ATUAL
        const startIndex = (currentPage - 1) * itemsPerPage;
        const endIndex = startIndex + itemsPerPage;
        const paginatedItems = allRecommendations.slice(startIndex, endIndex);

        if (paginatedItems.length > 0) {
            let hybridHtml = `<h4 class="results-summary">Recomendado para Você</h4>`;
            paginatedItems.forEach(result => {
                hybridHtml += buildResultCard(result);
            });
            finalHtml += hybridHtml;
        }

        // 2. Constrói e adiciona a barra de navegação da paginação
        finalHtml += buildPagination();

        // 3. Renderiza as buscas populares (sempre as mesmas, abaixo da paginação)
        if (popularSearches.length > 0) {
            let popularHtml = `
                <div class="recommendations-section">
                    <h5><i class="fas fa-chart-line me-2 text-success"></i>Buscas Populares</h5>
                    <div class="list-group list-group-flush recommendations-list">`;
            popularSearches.forEach(item => {
                const searchUrl = `/search?q=${encodeURIComponent(item.query_term)}&token=${token}`;
                popularHtml += `<a href="${searchUrl}" class="list-group-item list-group-item-action"><i class="fas fa-search me-2 text-muted"></i>${item.query_term}</a>`;
            });
            popularHtml += `</div></div>`;
            finalHtml += popularHtml;
        }
        
        // 4. Insere todo o HTML gerado no contêiner
        recommendationsContainer.innerHTML = finalHtml;
        setupPaginationListener();
    }
    
    /**
     * Constrói o HTML para a barra de navegação da paginação.
     */
    function buildPagination() {
        const totalPages = Math.ceil(allRecommendations.length / itemsPerPage);
        if (totalPages <= 1) return ''; // Não mostra paginação se houver apenas 1 página ou menos

        let paginationHtml = '<nav aria-label="Paginação de recomendações" class="pagination-nav"><ul class="pagination">';

        // Botão "Anterior"
        paginationHtml += `
            <li class="page-item ${currentPage === 1 ? 'disabled' : ''}">
                <a class="page-link" href="#" data-page="${currentPage - 1}">Anterior</a>
            </li>`;

        // Botões de página numerados
        for (let i = 1; i <= totalPages; i++) {
            paginationHtml += `
                <li class="page-item ${i === currentPage ? 'active' : ''}">
                    <a class="page-link" href="#" data-page="${i}">${i}</a>
                </li>`;
        }

        // Botão "Próxima"
        paginationHtml += `
            <li class="page-item ${currentPage === totalPages ? 'disabled' : ''}">
                <a class="page-link" href="#" data-page="${currentPage + 1}">Próxima</a>
            </li>`;

        paginationHtml += '</ul></nav>';
        return paginationHtml;
    }

    /**
     * Adiciona o listener de eventos para os cliques na paginação.
     */
    function setupPaginationListener() {
        const paginationElement = recommendationsContainer.querySelector('.pagination');
        if (paginationElement) {
            paginationElement.addEventListener('click', function(e) {
                e.preventDefault();
                const target = e.target;

                if (target.tagName === 'A' && !target.parentElement.classList.contains('disabled') && !target.parentElement.classList.contains('active')) {
                    const newPage = parseInt(target.dataset.page, 10);
                    if (newPage !== currentPage) {
                        currentPage = newPage;
                        displayPage();
                        // Opcional: rolar para o topo da lista
                        recommendationsContainer.scrollIntoView({ behavior: 'smooth' });
                    }
                }
            });
        }
    }

    /**
     * Constrói o HTML para um único card de resultado/recomendação. (Função inalterada)
     */
    function buildResultCard(result) {
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
                <div class="result-card">
                    ${previewHtml}
                    <div class="result-content">
                        <div class="result-card-header">
                            <i class="${result.module_icon} icon"></i>
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
     * Configura a funcionalidade de auto-complete. (Função inalterada)
     */
    function setupAutocomplete() {
        // ... (seu código de autocomplete existente vai aqui, sem alterações)
        const searchInput = document.getElementById('q');
        const autocompleteResults = document.getElementById('autocomplete-results');
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
                document.getElementById('search-form').submit();
            }
        });

        document.addEventListener('click', function(e) {
            if (!searchInput.contains(e.target) && !autocompleteResults.contains(e.target)) {
                autocompleteResults.style.display = 'none';
            }
        });
    }

    // --- Inicialização ---
    // Chama a função inicial que busca os dados e renderiza a primeira página
    fetchAndDisplayData();
    // Configura o autocomplete
    setupAutocomplete();
});
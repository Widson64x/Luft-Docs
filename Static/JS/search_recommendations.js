/**
 * search_recommendations.js
 * - Agora todas as chamadas usam o prefixo __BASE_PREFIX__ (ex.: /luft-docs)
 * - Corrige 404 ao buscar /search/api/... e monta URLs de resultados com prefixo.
 */
document.addEventListener('DOMContentLoaded', function () {
  const token = (document.body && document.body.dataset.token) || '';
  const BASE_PREFIX = (window.__BASE_PREFIX__ || '').replace(/\/+$/, '') || '/luft-docs'; // tira barra no fim

  const recommendationsContainer = document.getElementById('recommendations-container');
  const searchInput = document.getElementById('q');
  const autocompleteResults = document.getElementById('autocomplete-results');
  const searchForm = document.getElementById('search-form');

  // --------------------- Helpers de URL ---------------------
    function withPrefix(path) {
    if (!path) return '';

    // Se já é URL absoluta, retorna
    if (/^https?:\/\//i.test(path)) return path;

    // Remove barras extras no final do prefixo
    const BASE_PREFIX = (window.__BASE_PREFIX__ || '/luft-docs').replace(/\/+$/, '');

    // Garante que o path começa com "/"
    const p = path.startsWith('/') ? path : `/${path}`;

    // Se já começa com o prefixo, não duplica
    if (p === BASE_PREFIX || p.startsWith(`${BASE_PREFIX}/`)) return p;

    return `${BASE_PREFIX}${p}`;
    }


  function addToken(url, tkn) {
    if (!tkn) return url;
    return url + (url.includes('?') ? '&' : '?') + 'token=' + encodeURIComponent(tkn);
  }

  // --------------------- Estado da página -------------------
  let allRecommendations = [];
  let popularSearches = [];
  let currentPage = 1;
  const itemsPerPage = 5;

  // =================== Requisições ===================
  function fetchAndDisplayData() {
    if (!recommendationsContainer) return;

    const url = addToken(withPrefix('/search/api/recommendations'), token);
    fetch(url)
      .then((response) => {
        if (!response.ok) throw new Error('Falha ao buscar recomendações da API.');
        return response.json();
      })
      .then((data) => {
        allRecommendations = data.hybrid_recommendations || [];
        popularSearches = (data.popular_searches || []).slice(0, 10);
        currentPage = 1;
        displayPage();
      })
      .catch((error) => {
        console.error('Erro ao buscar recomendações:', error);
        recommendationsContainer.innerHTML = `
          <div class='custom-alert alert-danger'>
            <i class="bi bi-exclamation-triangle-fill alert-icon"></i>
            <span>Não foi possível carregar as recomendações.</span>
          </div>`;
      });
  }

  function fetchAutocomplete(query) {
    const url = addToken(withPrefix('/search/api/autocomplete') + `?q=${encodeURIComponent(query)}`, token);
    return fetch(url).then((r) => {
      if (!r.ok) throw new Error('Falha no autocomplete');
      return r.json();
    });
  }

  // =================== Renderização ===================
  function displayPage() {
    if (!recommendationsContainer) return;

    if (allRecommendations.length === 0 && popularSearches.length === 0) {
      recommendationsContainer.innerHTML =
        "<div class='no-results'><h5>Nenhuma recomendação disponível.</h5><p>Comece a usar o sistema para gerarmos sugestões para você.</p></div>";
      return;
    }

    let finalHtml = '';

    // 1) Cards da página atual
    const startIndex = (currentPage - 1) * itemsPerPage;
    const endIndex = startIndex + itemsPerPage;
    const paginatedItems = allRecommendations.slice(startIndex, endIndex);

    if (paginatedItems.length > 0) {
      let hybridHtml = `<h4 class="search-summary">Recomendado para Você</h4>`;
      paginatedItems.forEach((result, index) => {
        hybridHtml += buildResultCard(result, index * 100);
      });
      finalHtml += hybridHtml;
    }

    // 2) Paginação
    finalHtml += buildPagination();

    // 3) Buscas populares
    if (popularSearches.length > 0) {
      let popularHtml = `
        <div class="recommendations-section">
          <h5><i class="fas fa-chart-line me-2 text-success"></i>Buscas Populares</h5>
          <div class="recommendation-list">`;
      popularSearches.forEach((item) => {
        // link da busca precisa do prefixo
        const searchUrl = addToken(withPrefix('/search') + `?q=${encodeURIComponent(item.query_term)}`, token);
        popularHtml += `<a href="${searchUrl}" class="recommendation-item"><i class="fas fa-search me-2"></i>${item.query_term}</a>`;
      });
      popularHtml += `</div></div>`;
      finalHtml += popularHtml;
    }

    recommendationsContainer.innerHTML = finalHtml;
    setupPaginationListener();
  }

  function buildPagination() {
    const totalPages = Math.ceil(allRecommendations.length / itemsPerPage);
    if (totalPages <= 1) return '';

    let html = '<nav aria-label="Paginação de recomendações"><ul class="custom-pagination">';
    html += `<li class="${currentPage === 1 ? 'disabled' : ''}"><a href="#" data-page="${currentPage - 1}">Anterior</a></li>`;
    for (let i = 1; i <= totalPages; i++) {
      html += `<li class="${i === currentPage ? 'active' : ''}"><a href="#" data-page="${i}">${i}</a></li>`;
    }
    html += `<li class="${currentPage === totalPages ? 'disabled' : ''}"><a href="#" data-page="${currentPage + 1}">Próxima</a></li>`;
    html += '</ul></nav>';
    return html;
  }

  function setupPaginationListener() {
    const pg = recommendationsContainer.querySelector('.custom-pagination');
    if (!pg) return;
    pg.addEventListener('click', function (e) {
      e.preventDefault();
      const a = e.target.closest('a');
      if (!a) return;
      const li = a.parentElement;
      if (li.classList.contains('disabled') || li.classList.contains('active')) return;
      const newPage = parseInt(a.dataset.page, 10);
      if (!Number.isFinite(newPage) || newPage === currentPage) return;
      currentPage = newPage;
      displayPage();
      recommendationsContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
    });
  }

    // --------------------- Montagem do card ---------------------
    function buildResultCard(result, animationDelay = 0) {
    let previewHtml = '';

    if (result.preview && result.preview.path) {
        // Se o backend já devolveu com prefixo, a função não duplica
        const mediaSrc = withPrefix(result.preview.path);

        const mediaTag =
        result.preview.type === 'image'
            ? `<img src="${mediaSrc}" alt="Preview">`
            : `<video src="${mediaSrc}" muted autoplay loop playsinline></video>
            <div class="video-overlay"><i class="fas fa-play-circle play-icon"></i></div>`;

        previewHtml = `<div class="result-media-preview">${mediaTag}</div>`;
    }

    const resultUrl = withPrefix(result.url || '#');

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
            <p class="result-snippet m-0">${result.snippet || ''}</p>
            </div>
        </div>
        </a>
    `;
    }

  // =================== Autocomplete ===================
  function setupAutocomplete() {
    if (!searchInput || !autocompleteResults) return;

    let debounceTimer;
    searchInput.addEventListener('input', function () {
      const query = this.value;
      clearTimeout(debounceTimer);
      if ((query || '').length < 2) {
        autocompleteResults.style.display = 'none';
        return;
      }
      debounceTimer = setTimeout(() => {
        fetchAutocomplete(query)
          .then((suggestions) => {
            let html = '';
            if (Array.isArray(suggestions) && suggestions.length) {
              suggestions.forEach((s) => {
                html += `<a href="#" class="autocomplete-item" data-suggestion="${s}">${s}</a>`;
              });
              autocompleteResults.innerHTML = html;
              autocompleteResults.style.display = 'block';
            } else {
              autocompleteResults.style.display = 'none';
            }
          })
          .catch((err) => {
            console.error('Erro no auto-complete:', err);
            autocompleteResults.style.display = 'none';
          });
      }, 250);
    });

    autocompleteResults.addEventListener('click', function (e) {
      e.preventDefault();
      const item = e.target.closest('.autocomplete-item');
      if (!item) return;
      searchInput.value = item.dataset.suggestion || '';
      autocompleteResults.style.display = 'none';
      if (searchForm) searchForm.submit();
    });

    document.addEventListener('click', function (e) {
      if (!searchInput.contains(e.target) && !autocompleteResults.contains(e.target)) {
        autocompleteResults.style.display = 'none';
      }
    });
  }

  // =================== Inicialização ===================
  fetchAndDisplayData();
  setupAutocomplete();
});

/**
 * buscarAtalho.js – Paleta de busca rápida (Ctrl+K / Cmd+K)
 * Abre o modal #modalBusca gerenciado pelo LuftCore.
 */
(function () {
  'use strict';

  const isMac = /Mac|iPod|iPhone|iPad/.test(navigator.platform);
  const MOD   = isMac ? 'metaKey' : 'ctrlKey';

  function init() {
    const modal      = document.getElementById('modalBusca');
    if (!modal) return;

    const input      = document.getElementById('kpModalInput');
    const results    = document.getElementById('kpModalResults');
    const chips      = document.getElementById('kpModalChips');
    const sections   = document.getElementById('kpModalSections');
    const empty      = document.getElementById('kpModalEmpty');
    const acDropdown = document.getElementById('kpModalAutocomplete');

    if (!input) return;

    const rotas = window.ROUTES || {};
    const rotasApi = rotas.Api || {};

    let acTimer              = null;   // debounce do autocomplete
    let searchTimer         = null;   // debounce da busca completa
    let activeIndex         = -1;
    let recsCache           = null;  // cache das recomendações pré-carregadas

    // Pré-carrega recomendações em background assim que a página carrega
    api(rotasApi.listarRecomendacoes)
      .then(data => { recsCache = data; })
      .catch(() => {});

    // ── Helpers ────────────────────────────────────────────────────────────

    async function api(urlBase, params = {}) {
      const { data } = await window.LuftDocs.requestJson(urlBase, {
        query: params,
      });
      return data;
    }

    function escapeHtml(s) {
      return String(s).replace(/[&<>"']/g, m =>
        ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[m])
      );
    }

    function buildUrl(relativeUrl) {
      return window.LuftDocs.route(relativeUrl);
    }

    // ── Abrir modal ────────────────────────────────────────────────────────

    function openModal() {
      if (typeof LuftCore === 'undefined' || !LuftCore.abrirModal) return;

      // Reseta estado antes de abrir
      input.value              = '';
      results.innerHTML        = '';
      acDropdown.style.display = 'none';
      empty.hidden             = true;
      activeIndex              = -1;

      // Renderiza recomendações (do cache ou via fetch)
      renderRecommendations();

      LuftCore.abrirModal('modalBusca');
      requestAnimationFrame(() => input.focus());
    }

    // ── Atalho global Ctrl+K ───────────────────────────────────────────────

    document.addEventListener('keydown', (e) => {
      if (e[MOD] && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        openModal();
      }
    });

    // ── Fechar autocomplete ao clicar fora ────────────────────────────────

    document.addEventListener('click', (e) => {
      if (!input.contains(e.target) && !acDropdown.contains(e.target)) {
        acDropdown.style.display = 'none';
      }
    });

    // ── Input: autocomplete rápido + busca completa separados ──────────────

    input.addEventListener('input', () => {
      clearTimeout(acTimer);
      clearTimeout(searchTimer);
      const q = input.value.trim();

      if (!q) {
        results.innerHTML        = '';
        acDropdown.style.display = 'none';
        empty.hidden             = true;
        renderRecommendations();
        return;
      }

      sections.innerHTML = '';
      chips.hidden       = true;
      showSearchLoading();

      // Autocomplete: resposta rápida (200ms)
      if (q.length >= 2) {
        acTimer = setTimeout(async () => {
          try {
            const sugestoes = await api(rotasApi.listarAutocomplete, { q });
            renderAutocomplete(Array.isArray(sugestoes) ? sugestoes : []);
          } catch (_) { /* silencioso */ }
        }, 200);
      }

      // Busca completa: debounce maior (450ms) para não sobrecarregar
      searchTimer = setTimeout(async () => {
        try {
          const data = await api(rotasApi.buscar, { q });
          renderResults(data?.results || []);
        } catch (_) {
          results.innerHTML = '<li class="kp-empty px-3 py-2">Erro ao buscar. Tente novamente.</li>';
        }
      }, 450);
    });

    // ── Navegação por teclado ──────────────────────────────────────────────

    input.addEventListener('keydown', (e) => {
      const lis = results.querySelectorAll('li');

      if (e.key === 'ArrowDown' && lis.length) {
        e.preventDefault();
        selectIndex(Math.min(activeIndex + 1, lis.length - 1));
        ensureVisible(lis[activeIndex]);
      } else if (e.key === 'ArrowUp' && lis.length) {
        e.preventDefault();
        selectIndex(Math.max(activeIndex - 1, 0));
        ensureVisible(lis[activeIndex]);
      } else if (e.key === 'Enter' && lis.length && activeIndex >= 0) {
        e.preventDefault();
        const href = lis[activeIndex]?.querySelector('a')?.getAttribute('href');
        if (href) location.href = href;
      } else if (e.key === 'Escape') {
        if (acDropdown.style.display !== 'none') {
          e.stopPropagation(); // impede o Bootstrap de fechar o modal
          acDropdown.style.display = 'none';
        }
      }
    });

    // ── Recomendações (estado inicial — sem query) ─────────────────────────

    function renderRecommendations() {
      if (recsCache) {
        // Já temos cache — renderiza instantaneamente
        renderChips(recsCache.popular_searches || []);
        renderSections({
          most:   recsCache.most_accessed          || [],
          hybrid: recsCache.hybrid_recommendations || []
        });
        return;
      }

      // Sem cache ainda — mostra loading e faz fetch
      sections.innerHTML = '<div class="kp-section-loading py-3 text-center"><i class="ph ph-spinner-gap kp-spin me-2"></i>Carregando…</div>';
      chips.hidden = true;

      api(rotasApi.listarRecomendacoes).then(data => {
        recsCache = data;
        renderChips(data?.popular_searches || []);
        renderSections({
          most:   data?.most_accessed          || [],
          hybrid: data?.hybrid_recommendations || []
        });
      }).catch(() => {
        sections.innerHTML = '';
      });
    }

    // ── Chips de buscas populares ──────────────────────────────────────────

    function renderChips(items) {
      chips.innerHTML = '';
      if (!Array.isArray(items) || !items.length) { chips.hidden = true; return; }

      chips.hidden = false;
      items.slice(0, 10).forEach(it => {
        const term = typeof it === 'string' ? it : (it.query_term || '');
        if (!term) return;
        const el       = document.createElement('span');
        el.className   = 'kp-chip';
        el.textContent = term;
        el.addEventListener('click', () => {
          input.value = term;
          input.dispatchEvent(new Event('input', { bubbles: true }));
          input.focus();
        });
        chips.appendChild(el);
      });
    }

    // ── Grid de seções (mais acessados + recomendados) ─────────────────────

    function renderSections({ most = [], hybrid = [] }) {
      sections.innerHTML = `
        <div class="kp-sections-grid">
          <div class="kp-section">
            <h4><i class="ph-bold ph-trend-up me-1"></i>Mais acessados</h4>
            <ul class="kp-list" id="kpSectionMost"></ul>
          </div>
          <div class="kp-section">
            <h4><i class="ph-bold ph-sparkle me-1"></i>Recomendados para você</h4>
            <ul class="kp-list" id="kpSectionRecs"></ul>
          </div>
        </div>`;

      fillList(document.getElementById('kpSectionMost'), most);
      fillList(document.getElementById('kpSectionRecs'), hybrid);
    }

    function fillList(ul, items) {
      if (!ul) return;
      ul.innerHTML = '';
      (items || []).slice(0, 8).forEach(it => {
        const icon = (it.module_icon || 'ph-bold ph-file-text')
          .replace('fas fa-', 'ph-bold ph-').replace('bi bi-', 'ph-bold ph-');
        const href = buildUrl(it.url);
        const li   = document.createElement('li');
        li.innerHTML = `
          <a href="${href}">
            <span class="kp-ico"><i class="${escapeHtml(icon)}"></i></span>
            <span>
              <strong>${escapeHtml(it.module_nome || it.url)}</strong><br>
              <small>${escapeHtml(it.doc_type || '')}${it.access_count ? ' · ' + it.access_count + ' acessos' : ''}</small>
            </span>
          </a>`;
        ul.appendChild(li);
      });
    }

    // ── Loading state ──────────────────────────────────────────────────────

    function showSearchLoading() {
      results.innerHTML = '';
      empty.hidden      = true;
      results.innerHTML =
        '<li class="kp-searching">' +
          '<i class="ph ph-spinner-gap kp-spin me-2 text-primary" style="font-size:1.4rem;"></i>' +
          '<span class="text-muted" style="font-size:.9rem;">Buscando\u2026</span>' +
        '</li>';
    }

    // ── Autocomplete dropdown ──────────────────────────────────────────────

    function renderAutocomplete(sugestoes) {
      if (!sugestoes.length) { acDropdown.style.display = 'none'; return; }

      acDropdown.innerHTML = sugestoes.map(s =>
        `<div class="luft-autocomplete-item" data-valor="${escapeHtml(s)}">
           <i class="ph ph-magnifying-glass"></i><span>${escapeHtml(s)}</span>
         </div>`
      ).join('');
      acDropdown.style.display = 'block';

      acDropdown.querySelectorAll('.luft-autocomplete-item').forEach(item => {
        item.addEventListener('click', () => {
          input.value              = item.dataset.valor;
          acDropdown.style.display = 'none';
          input.dispatchEvent(new Event('input', { bubbles: true }));
        });
      });
    }

    // ── Resultados de busca ────────────────────────────────────────────────

    function renderResults(items) {
      sections.innerHTML = '';
      results.innerHTML  = '';
      activeIndex        = -1;

      if (!items.length) { empty.hidden = false; return; }
      empty.hidden = true;

      items.slice(0, 30).forEach((it, i) => {
        const icon = (it.module_icon || 'ph-bold ph-file-text')
          .replace('fas fa-', 'ph-bold ph-').replace('bi bi-', 'ph-bold ph-');
        const href = buildUrl(it.url);
        const li   = document.createElement('li');
        li.setAttribute('role', 'option');
        li.setAttribute('aria-selected', 'false');
        li.innerHTML = `
          <a href="${href}">
            <div class="kp-result-meta">
              <i class="${escapeHtml(icon)} text-primary kp-result-icon"></i>
              <strong>${escapeHtml(it.module_nome || it.url)}</strong>
              ${it.doc_type ? `<span class="luft-badge ms-auto">${escapeHtml(it.doc_type)}</span>` : ''}
            </div>
            ${it.snippet ? `<div class="kp-result-snippet">${it.snippet}</div>` : ''}
          </a>`;
        li.addEventListener('mousemove', () => selectIndex(i));
        results.appendChild(li);
      });
    }

    function selectIndex(i) {
      const lis = results.querySelectorAll('li');
      lis.forEach((el, idx) => el.setAttribute('aria-selected', String(idx === i)));
      activeIndex = i;
    }

    function ensureVisible(el) {
      if (!el) return;
      const pr = results.getBoundingClientRect();
      const br = el.getBoundingClientRect();
      if (br.bottom > pr.bottom) results.scrollTop += br.bottom - pr.bottom;
      if (br.top    < pr.top)    results.scrollTop -= pr.top    - br.top;
    }
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();

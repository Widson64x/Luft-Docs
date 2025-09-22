(function () {
  const isMac = /Mac|iPod|iPhone|iPad/.test(navigator.platform);
  const MOD = isMac ? 'metaKey' : 'ctrlKey';
  const base = (window.__LUFT_SEARCH_BASE__ || "/search").replace(/\/$/, "");
  const qs = new URLSearchParams(location.search);
  const token = qs.get("token") || "";

  const backdrop = document.getElementById('kp-backdrop');
  const input = document.getElementById('kp-input');
  const results = document.getElementById('kp-results');
  const btnClose = document.getElementById('kp-close');
  const empty = document.getElementById('kp-empty');
  const chips = document.getElementById('kp-chips');
  const sections = document.getElementById('kp-sections');

  let debounceTimer = null;
  let activeIndex = -1;

  function api(url, params = {}) {
    const u = new URL(base + url, location.origin);
    if (token) params.token = token;
    Object.entries(params).forEach(([k, v]) => v != null && u.searchParams.set(k, v));
    return fetch(u.toString(), { headers: { 'Accept': 'application/json' } })
      .then(r => r.json());
  }

  function openPalette() {
    backdrop.setAttribute('aria-hidden', 'false');
    renderRecommendations(); // carrega blocos iniciais
    requestAnimationFrame(() => input.focus());
  }
  function closePalette() {
    backdrop.setAttribute('aria-hidden', 'true');
    input.value = '';
    results.innerHTML = '';
    empty.hidden = true;
    chips.hidden = true;
    sections.innerHTML = '';
    activeIndex = -1;
  }

  // Teclado global
  document.addEventListener('keydown', (e) => {
    if (e[MOD] && e.key.toLowerCase() === 'k') {
      e.preventDefault();
      openPalette();
    } else if (e.key === 'Escape' && backdrop.getAttribute('aria-hidden') === 'false') {
      e.preventDefault();
      closePalette();
    }
  });
  btnClose?.addEventListener('click', closePalette);
  backdrop?.addEventListener('click', (e) => { if (e.target === backdrop) closePalette(); });

  // Input: autocomplete + busca
  input?.addEventListener('input', () => {
    clearTimeout(debounceTimer);
    const q = input.value.trim();
    if (!q) {
      results.innerHTML = '';
      empty.hidden = true;
      return;
    }
    debounceTimer = setTimeout(async () => {
      // autocomplete (chips inline opcional)
      try {
        const sugg = await api('/api/autocomplete', { q });
        renderChips(sugg || []);
      } catch {}
      // resultados
      try {
        const data = await api('/api/search', { q });
        renderResults(data?.results || []);
      } catch {
        results.innerHTML = '<li><a href="#">Erro ao buscar…</a></li>';
      }
    }, 160);
  });

  // Navegação por setas/enter
  input?.addEventListener('keydown', (e) => {
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
      const a = lis[activeIndex]?.querySelector('a');
      if (a) location.href = a.getAttribute('href');
    }
  });

  function renderRecommendations() {
    results.innerHTML = '';
    empty.hidden = true;
    chips.hidden = true;
    sections.innerHTML = '<div class="kp-section"><h4>Carregando…</h4></div>';
    api('/api/recommendations').then(data => {
      // Chips de pesquisas populares
      renderChips(data?.popular_searches || []);
      // Seções: Mais acessados + Recomendados
      renderSections({
        most: data?.most_accessed || [],
        hybrid: data?.hybrid_recommendations || []
      });
    }).catch(() => {
      sections.innerHTML = '';
    });
  }

  function renderChips(items) {
    chips.innerHTML = '';
    let arr = items;
    // cada item pode ser string ou {query_term: "..."}
    if (Array.isArray(arr) && arr.length) {
      chips.hidden = false;
      arr.slice(0, 10).forEach(it => {
        const term = typeof it === 'string' ? it : (it.query_term || '');
        if (!term) return;
        const el = document.createElement('span');
        el.className = 'kp-chip';
        el.textContent = term;
        el.addEventListener('click', () => {
          input.value = term;
          input.dispatchEvent(new Event('input', { bubbles: true }));
          input.focus();
        });
        chips.appendChild(el);
      });
    } else {
      chips.hidden = true;
    }
  }

  function renderSections({ most = [], hybrid = [] }) {
    sections.innerHTML = `
      <div class="kp-section">
        <h4>Mais acessados</h4>
        <ul class="kp-list" id="kp-most"></ul>
      </div>
      <div class="kp-section">
        <h4>Recomendados para você</h4>
        <ul class="kp-list" id="kp-recs"></ul>
      </div>
    `;
    fillList(document.getElementById('kp-most'), most);
    fillList(document.getElementById('kp-recs'), hybrid);
  }

  function fillList(ul, items) {
    ul.innerHTML = '';
    (items || []).slice(0, 12).forEach(it => {
      const li = document.createElement('li');
      li.innerHTML = `
        <a href="${it.url}">
          <span class="kp-ico"><i class="${it.module_icon || 'fas fa-file-alt'}"></i></span>
          <span>
            <strong>${escapeHtml(it.module_nome || it.url)}</strong><br>
            <small>${escapeHtml(it.doc_type || '')} • ${it.access_count || 0} acessos</small>
          </span>
        </a>`;
      ul.appendChild(li);
    });
  }

  function renderResults(items) {
    sections.innerHTML = ''; // some as seções quando começa a buscar
    results.innerHTML = '';
    activeIndex = -1;
    if (!items.length) {
      empty.hidden = false;
      return;
    }
    empty.hidden = true;
    items.slice(0, 30).forEach((it, i) => {
      const li = document.createElement('li');
      li.setAttribute('role', 'option');
      li.setAttribute('aria-selected', 'false');
      li.innerHTML = `
        <a href="${it.url}">
          <strong>${escapeHtml(it.module_nome || it.url)}</strong><br>
          <small>${escapeHtml(it.snippet || '')}</small>
        </a>`;
      li.addEventListener('mousemove', () => selectIndex(i));
      li.addEventListener('click', (e) => { e.preventDefault(); location.href = it.url; });
      results.appendChild(li);
    });
  }

  function selectIndex(i) {
    const lis = results.querySelectorAll('li');
    lis.forEach((el, idx) => el.setAttribute('aria-selected', String(idx === i)));
    activeIndex = i;
  }
  function ensureVisible(el) {
    const pr = results.getBoundingClientRect();
    const br = el.getBoundingClientRect();
    if (br.bottom > pr.bottom) results.scrollTop += (br.bottom - pr.bottom);
    if (br.top < pr.top) results.scrollTop -= (pr.top - br.top);
  }
  function escapeHtml(s) {
    return String(s).replace(/[&<>"']/g, m => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]));
  }
})();

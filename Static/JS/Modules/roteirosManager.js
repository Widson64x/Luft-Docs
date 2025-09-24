// static/js/roteirosManager.js
document.addEventListener('DOMContentLoaded', () => {
  const roteirosList = document.getElementById('roteiros-list');
  if (!roteirosList) return;

  // -------- Helpers de prefixo/URL/token --------
  function getBasePrefix() {
    // definido no template base.html
    const raw = (window.__BASE_PREFIX__ || '').replace(/\/+$/, '');
    return raw || '/luft-docs';
  }
  function withPrefix(path) {
    if (/^https?:\/\//i.test(path)) return path;
    const BASE = getBasePrefix();
    const p = path.startsWith('/') ? path : `/${path}`;
    if (p === BASE || p.startsWith(`${BASE}/`)) return p;
    return `${BASE}${p}`;
  }
  function getToken() {
    // busca token no body data-token ou na query
    const fromBody = document.body?.dataset?.token;
    if (fromBody) return fromBody;
    const qs = new URLSearchParams(window.location.search);
    return qs.get('token') || '';
  }
  function appendToken(url) {
    const token = getToken();
    if (!token) return url;
    const u = new URL(url, window.location.origin);
    if (!u.searchParams.get('token')) u.searchParams.set('token', token);
    return u.pathname + (u.search ? u.search : '');
  }

  // -------- 1. SETUP --------
  const moduloId = document.getElementById('imagem-viewer')?.dataset.docId;
  const roteiroModal = new bootstrap.Modal(document.getElementById('roteiroModal'));
  const videoModal = new bootstrap.Modal(document.getElementById('videoModal'));
  const confirmDeleteModal = new bootstrap.Modal(document.getElementById('confirmDeleteModal'));
  const roteiroForm = document.getElementById('roteiroForm');
  const roteiroModalLabel = document.getElementById('roteiroModalLabel');
  const roteiroIdField = document.getElementById('roteiroId');
  const roteiroTituloField = document.getElementById('roteiroTitulo');
  const roteiroTipoField = document.getElementById('roteiroTipo');
  const roteiroConteudoField = document.getElementById('roteiroConteudo');
  const roteiroIconeField = document.getElementById('roteiroIcone');
  const roteiroOrdemField = document.getElementById('roteiroOrdem');
  const btnCriarRoteiro = document.getElementById('btn-criar-roteiro');
  const btnConfirmDelete = document.getElementById('btnConfirmDelete');

  // Dados injetados pelo template
  const permissionsRaw = document.getElementById('roteiros-data')?.textContent || "{}";
  let permissionsData = {};
  try { permissionsData = JSON.parse(permissionsRaw); } catch { permissionsData = {}; }

  let roteiros = Array.isArray(permissionsData.roteiros) ? permissionsData.roteiros : [];
  const canEdit = Boolean(permissionsData.can_edit);

  if (!moduloId) {
    console.warn("⚠️ ID do módulo não encontrado. Roteiros podem não funcionar totalmente.");
  }

  // -------- 2. HELPERS --------
  const fmt = (iso) => {
    if (!iso) return null;
    const d = new Date(iso);
    return isNaN(d) ? null : d.toLocaleString();
  };

  const dateLabel = (r) => {
    const created = r.created_at ? new Date(r.created_at) : null;
    const updated = r.updated_at ? new Date(r.updated_at) : null;
    if (created && updated && (updated.getTime() > (created.getTime() + 1000))) {
      return `<small class="text-muted">Editado em ${fmt(r.updated_at)}</small>`;
    }
    return created ? `<small class="text-muted">Criado em ${fmt(r.created_at)}</small>` : '';
  };

  const API_BASE = withPrefix('/api/roteiros');

  const apiCall = async (path, method = "GET", body = null) => {
    try {
      const url = appendToken(withPrefix(path.startsWith('/') ? path : `${API_BASE}/${path}`));
      const options = { method, headers: { "Content-Type": "application/json" } };
      if (body) options.body = JSON.stringify(body);
      const resp = await fetch(url, options);
      if (!resp.ok) {
        // tenta extrair mensagem JSON do backend
        let msg = `Erro na requisição (${resp.status})`;
        try {
          const data = await resp.json();
          if (data && data.message) msg = data.message;
        } catch {}
        throw new Error(msg);
      }
      const ct = resp.headers.get('content-type') || '';
      return ct.includes('application/json') ? resp.json() : {};
    } catch (err) {
      console.error("❌ API Error:", err);
      alert("Erro: " + (err?.message || 'Falha de rede.'));
      return null;
    }
  };

  // -------- 3. RENDER --------
  const renderRoteiros = () => {
    roteirosList.innerHTML = "";
    if (!Array.isArray(roteiros) || roteiros.length === 0) {
      roteirosList.innerHTML = '<li class="roteiro-vazio">Nenhum roteiro encontrado.</li>';
      return;
    }
    roteiros
      .slice()
      .sort((a, b) => (a.ordem ?? 0) - (b.ordem ?? 0))
      .forEach((roteiro) => {
        const li = document.createElement("li");
        const actionsHtml = canEdit ? `
          <div class="roteiro-actions btn-group btn-group-sm">
            <button class="btn btn-outline-secondary btn-edit-roteiro" data-id="${roteiro.id}" title="Editar">
              <i class="bi bi-pencil-fill"></i>
            </button>
            <button class="btn btn-outline-danger btn-delete-roteiro" data-id="${roteiro.id}" data-titulo="${roteiro.titulo}" title="Excluir">
              <i class="bi bi-trash-fill"></i>
            </button>
          </div>` : '';

        const href = roteiro.conteudo || '#';
        li.innerHTML = `
          <div class="roteiro-item-wrapper">
            <div class="d-flex flex-column flex-grow-1">
              <a href="${href}" data-tipo="${roteiro.tipo || 'link'}" data-id="${roteiro.id}" class="roteiro-item">
                <i class="${roteiro.icone || 'bi-play-circle'}"></i>
                <span>${roteiro.titulo}</span>
              </a>
              <div class="mt-1">${dateLabel(roteiro)}</div>
            </div>
            ${actionsHtml}
          </div>
        `;
        roteirosList.appendChild(li);
      });
  };

  // -------- 4. EVENTOS --------
  if (btnCriarRoteiro) {
    btnCriarRoteiro.addEventListener("click", () => {
      roteiroModalLabel.textContent = "Criar Novo Roteiro";
      roteiroForm.reset();
      roteiroIdField.value = "";
      roteiroOrdemField.value = 0;
      roteiroModal.show();
    });
  }

  roteiroForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    const id = roteiroIdField.value.trim();
    const endpoint = id ? `${API_BASE}/${id}` : `${API_BASE}/`;
    const method = id ? "PUT" : "POST";

    const payload = {
      titulo: roteiroTituloField.value,
      tipo: roteiroTipoField.value,
      conteudo: roteiroConteudoField.value,
      icone: roteiroIconeField.value,
      ordem: parseInt(roteiroOrdemField.value || "0", 10),
    };

    const result = await apiCall(endpoint, method, payload);
    if (!result) return;

    if (!id && result.roteiro) {
      // Vincula ao módulo atual (se houver)
      if (moduloId) {
        await apiCall(`${API_BASE}/vincular`, "POST", {
          roteiro_id: result.roteiro.id,
          modulo_ids: [moduloId],
        });
      }
      roteiros.push({ ...result.roteiro });
    } else if (id && result.roteiro) {
      const idx = roteiros.findIndex((r) => String(r.id) === String(id));
      if (idx > -1) roteiros[idx] = { ...roteiros[idx], ...result.roteiro };
    }

    roteiroModal.hide();
    renderRoteiros();
  });

  roteirosList.addEventListener("click", async (e) => {
    const target = e.target.closest("a.roteiro-item, button.btn-edit-roteiro, button.btn-delete-roteiro");
    if (!target) return;

    const id = target.dataset.id;

    if (target.matches("a.roteiro-item")) {
      e.preventDefault();
      if ((target.dataset.tipo || 'link') === "modal") {
        document.getElementById("videoPlayer").src = target.getAttribute("href");
        videoModal.show();
      } else {
        window.open(target.getAttribute("href"), "_blank");
      }
      return;
    }

    if (target.matches("button.btn-edit-roteiro")) {
      const data = await apiCall(`${API_BASE}/${id}`, "GET");
      if (data) {
        roteiroModalLabel.textContent = "Editar Roteiro";
        roteiroIdField.value = data.id;
        roteiroTituloField.value = data.titulo || '';
        roteiroTipoField.value = data.tipo || 'link';
        roteiroConteudoField.value = data.conteudo || '';
        roteiroIconeField.value = data.icone || '';
        roteiroOrdemField.value = data.ordem ?? 0;

        const idx = roteiros.findIndex((r) => String(r.id) === String(id));
        if (idx > -1) roteiros[idx] = { ...roteiros[idx], ...data };

        renderRoteiros();
        roteiroModal.show();
      }
      return;
    }

    if (target.matches("button.btn-delete-roteiro")) {
      document.getElementById("roteiroNameToDelete").textContent = target.dataset.titulo || '';
      btnConfirmDelete.dataset.id = id;
      confirmDeleteModal.show();
    }
  });

  btnConfirmDelete.addEventListener("click", async () => {
    const id = btnConfirmDelete.dataset.id;
    const result = await apiCall(`${API_BASE}/${id}`, "DELETE");
    if (result) {
      roteiros = roteiros.filter((r) => String(r.id) !== String(id));
      confirmDeleteModal.hide();
      renderRoteiros();
    }
  });

  document.getElementById("videoModal")?.addEventListener("hidden.bs.modal", () => {
    const vp = document.getElementById("videoPlayer");
    if (vp) vp.src = "";
  });

  // -------- 5. INIT --------
  renderRoteiros();
});

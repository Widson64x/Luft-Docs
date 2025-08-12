/*!
 * Step Reader (Modo Foco) – LuftDocs
 * Front-end only. Requer:
 *  - Um botão com id="sr-toggle-icon" (novo ícone no header) OU id="sr-toggle" (fallback)
 *  - Um overlay com id="step-reader" (ver estrutura HTML do modal)
 *  - Um container de conteúdo com classe ".modulo-conteudo"
 *  - (Opcional) Banner de retomada com #sr-resume, #sr-resume-btn, #sr-resume-num
 *
 * Salva progresso em localStorage por página usando data-doc-id do container.
 */
(function () {
  "use strict";

  // ======================
  // CONFIGURAÇÕES BÁSICAS
  // ======================
  const CONTENT_SELECTOR = ".modulo-conteudo"; // container do conteúdo do doc
  const H_STEP_LEVEL = 2; // H2 vira passo
  const STORAGE_PREFIX = "sr:";

  // ======================
  // HELPERS
  // ======================
  const qs  = (sel, ctx = document) => ctx.querySelector(sel);
  const qsa = (sel, ctx = document) => Array.from(ctx.querySelectorAll(sel));

  const slugify = (s) =>
    (s || "")
      .toString()
      .toLowerCase()
      .trim()
      .replace(/[^\w\s-]/g, "")
      .replace(/\s+/g, "-")
      .replace(/-+/g, "-");

  const clamp = (n, min, max) => Math.max(min, Math.min(max, n));

  function getDocId(root) {
    return root.getAttribute("data-doc-id") || location.pathname;
  }

  function storageKeyFor(root) {
    return STORAGE_PREFIX + getDocId(root);
  }

  function loadProgress(key) {
    try {
      return JSON.parse(localStorage.getItem(key) || "{}");
    } catch {
      return {};
    }
  }

  function saveProgress(key, current, reviewedSet) {
    try {
      localStorage.setItem(
        key,
        JSON.stringify({ current, reviewed: Array.from(reviewedSet || []) })
      );
    } catch {}
  }

  // ======================
  // CORE
  // ======================
  function buildStepsFromContent(root) {
    // Quebra o conteúdo por H2 (ou nível definido), acumulando elementos até o próximo H2
    const children = Array.from(root.children);
    const blocks = [];
    let cur = null;

    children.forEach((el) => {
      const m = /^H(\d)$/i.exec(el.tagName);
      if (m && Number(m[1]) === H_STEP_LEVEL) {
        if (cur) blocks.push(cur);
        cur = { title: el.textContent.trim() || "Seção", nodes: [] };
      } else {
        if (!cur) cur = { title: "Introdução", nodes: [] };
        cur.nodes.push(el.cloneNode(true));
      }
    });
    if (cur) blocks.push(cur);

    // Normaliza
    blocks.forEach((b) => (b.id = slugify(b.title)));

    // Transforma em HTML leve para render no overlay
    return blocks.map((b) => ({
      id: b.id,
      title: b.title,
      html: b.nodes.length
        ? b.nodes.map((n) => n.outerHTML).join("")
        : "<p>(Sem conteúdo nesta seção)</p>",
    }));
  }

  function StepReader() {
    // ELEMENTOS
    this.root       = qs(CONTENT_SELECTOR);
    this.overlay    = qs("#step-reader");
    this.body       = qs(".sr-body", this.overlay);
    this.bar        = qs(".sr-bar", this.overlay);
    this.count      = qs(".sr-count", this.overlay);

    // Gatilho: novo ícone no header (preferência), com fallback ao antigo botão
    this.btnToggle  = qs("#sr-toggle-icon") || qs("#sr-toggle");

    this.btnClose   = qs(".sr-close", this.overlay);
    this.btnPrev    = qs(".sr-prev", this.overlay);
    this.btnNext    = qs(".sr-next", this.overlay);
    this.btnDone    = qs(".sr-done", this.overlay);
    this.chkReviewed= qs("#sr-mark-reviewed", this.overlay);

    // Banner de retomada (opcional)
    this.resumeWrap = qs("#sr-resume");
    this.resumeBtn  = qs("#sr-resume-btn");
    this.resumeNum  = qs("#sr-resume-num");

    // ESTADO
    this.steps    = [];
    this.current  = 0;
    this.reviewed = new Set();
    this.lastFocus= null;

    // INIT
    this._bindEvents();
    this._initResumeBanner(); // opcional, só se tiver o banner na página
  }

  StepReader.prototype._bindEvents = function () {
    // Abrir
    if (this.btnToggle) {
      this.btnToggle.addEventListener("click", () => this.open());
    }

    // Fechar
    if (this.btnClose) {
      this.btnClose.addEventListener("click", () => this.close());
    }

    // Navegação
    if (this.btnPrev) {
      this.btnPrev.addEventListener("click", () => {
        this.current--;
        this.render();
        this._save();
      });
    }
    if (this.btnNext) {
      this.btnNext.addEventListener("click", () => {
        this.current++;
        this.render();
        this._save();
      });
    }
    if (this.btnDone) {
      this.btnDone.addEventListener("click", () => this.close());
    }

    // Checkbox "entendi"
    if (this.chkReviewed) {
      this.chkReviewed.addEventListener("change", (e) => {
        const s = this.steps[this.current];
        if (!s) return;
        if (e.target.checked) this.reviewed.add(s.id);
        else this.reviewed.delete(s.id);
        this._save();
      });
    }

    // Fechar clicando fora
    if (this.overlay) {
      this.overlay.addEventListener("click", (e) => {
        if (e.target === this.overlay) this.close();
      });
    }

    // Teclado
    document.addEventListener("keydown", (e) => {
      if (!this.overlay || this.overlay.hidden) return;
      if (e.key === "Escape") {
        e.preventDefault();
        this.close();
      } else if (e.key === "ArrowRight") {
        e.preventDefault();
        if (!this.btnNext.hidden) {
          this.current++;
          this.render();
          this._save();
        }
      } else if (e.key === "ArrowLeft") {
        e.preventDefault();
        if (!this.btnPrev.disabled) {
          this.current--;
          this.render();
          this._save();
        }
      } else if (e.key === "Enter") {
        e.preventDefault();
        if (!this.btnNext.hidden) {
          this.current++;
          this.render();
          this._save();
        } else {
          this.btnDone.click();
        }
      }
    });
  };

  StepReader.prototype._initResumeBanner = function () {
    if (!this.resumeWrap || !this.root) return;

    const key = storageKeyFor(this.root);
    const saved = loadProgress(key);
    if (Number.isInteger(saved.current) && saved.current > 0) {
      this.resumeWrap.hidden = false;
      if (this.resumeNum) this.resumeNum.textContent = saved.current + 1;
      if (this.resumeBtn) {
        this.resumeBtn.addEventListener("click", () => this.open());
      }
    }
  };

  StepReader.prototype._save = function () {
    if (!this.root) return;
    saveProgress(storageKeyFor(this.root), this.current, this.reviewed);
  };

  StepReader.prototype.open = function () {
    if (!this.root || !this.overlay || !this.body) return;

    // Monta steps
    this.steps = buildStepsFromContent(this.root);

    if (!this.steps.length) {
      alert("Não encontrei seções (H2) para montar os passos.");
      return;
    }

    // Restaurar progresso
    const saved = loadProgress(storageKeyFor(this.root));
    this.current = clamp(saved.current ?? 0, 0, this.steps.length - 1);
    this.reviewed = new Set(saved.reviewed ?? []);

    // Abrir overlay
    this.lastFocus = document.activeElement;
    this.overlay.hidden = false;
    document.body.style.overflow = "hidden";

    // Render
    this.render();
  };

  StepReader.prototype.close = function () {
    if (!this.overlay) return;
    this.overlay.hidden = true;
    document.body.style.overflow = "";
    this._save();
    if (this.lastFocus && this.lastFocus.focus) {
      try { this.lastFocus.focus(); } catch {}
    }
  };

  StepReader.prototype.render = function () {
    if (!this.steps.length) return;
    this.current = clamp(this.current, 0, this.steps.length - 1);

    const total = this.steps.length;
    const s = this.steps[this.current];

    // Corpo
    this.body.innerHTML =
      `<section class="sr-step" aria-labelledby="h-${s.id}">` +
      `<h3 id="h-${s.id}" class="sr-step-title">${s.title}</h3>` +
      s.html +
      `</section>`;

    // Progresso
    if (this.bar)   this.bar.style.width = `${((this.current + 1) / total) * 100}%`;
    if (this.count) this.count.textContent = `${this.current + 1}/${total}`;

    // Botões
    if (this.btnPrev) this.btnPrev.disabled = this.current === 0;
    if (this.btnNext) this.btnNext.hidden   = this.current === total - 1;
    if (this.btnDone) this.btnDone.hidden   = !(this.current === total - 1);

    // Checkbox “entendi”
    if (this.chkReviewed) this.chkReviewed.checked = this.reviewed.has(s.id);

    // Foco no conteúdo
    this.body.focus({ preventScroll: true });
  };

  // ======================
  // BOOT
  // ======================
  document.addEventListener("DOMContentLoaded", () => {
    // Garante que existam os nós mínimos; se não houver, não inicializa.
    const content = qs(CONTENT_SELECTOR);
    const overlay = qs("#step-reader");
    if (!content || !overlay) return;

    // Recomendação: garantir data-doc-id no HTML. Se não tiver, o script usa pathname.
    // Ex.: <div class="modulo-conteudo" data-doc-id="{{ modulo.id or id_do_modulo }}"></div>

    // Instancia e deixa global (útil pra debug)
    window.__stepReader = new StepReader();
  });
})();

/**
 * Arquivo: gerenciadorRoteiros.js
 * Descricao: Módulo de gerenciamento de roteiros vinculados a um módulo.
 */

class GerenciadorRoteiros {
    constructor() {
        this.listaRoteiros = document.getElementById('roteiros-list');
        if (!this.listaRoteiros) return;

        this.idModulo = document.getElementById('imagem-viewer')?.dataset.docId;

        // Modais
        this.modalRoteiro          = new bootstrap.Modal(document.getElementById('roteiroModal'));
        this.modalVideo            = new bootstrap.Modal(document.getElementById('videoModal'));
        this.modalConfirmarExclusao = new bootstrap.Modal(document.getElementById('confirmDeleteModal'));

        // Formulário
        this.formulario   = document.getElementById('roteiroForm');
        this.rotuloModal  = document.getElementById('roteiroModalLabel');
        this.campoId      = document.getElementById('roteiroId');
        this.campoTitulo  = document.getElementById('roteiroTitulo');
        this.campoTipo    = document.getElementById('roteiroTipo');
        this.campoConteudo = document.getElementById('roteiroConteudo');
        this.campoIcone   = document.getElementById('roteiroIcone');
        this.campoOrdem   = document.getElementById('roteiroOrdem');

        this.btnCriar            = document.getElementById('btn-criar-roteiro');
        this.btnConfirmarExclusao = document.getElementById('btnConfirmDelete');

        // Dados injetados pelo template
        const dadosBrutos = document.getElementById('roteiros-data')?.textContent || '{}';
        let dadosPermissoes = {};
        try { dadosPermissoes = JSON.parse(dadosBrutos); } catch { dadosPermissoes = {}; }

        this.roteiros    = Array.isArray(dadosPermissoes.roteiros) ? dadosPermissoes.roteiros : [];
        this.podeEditar  = Boolean(dadosPermissoes.podeEditar);
        this.urlBase     = window.ROUTES?.Api?.roteiros || '';

        if (!this.idModulo) {
            console.warn('GerenciadorRoteiros: ID do módulo não encontrado. Roteiros podem não funcionar totalmente.');
        }

        this._inicializarEventos();
        this._renderizarLista();
    }

    // ======================================================
    // HELPERS — URL / TOKEN
    // ======================================================

    _obterPrefixoBase() {
        return (window.__BASE_PREFIX__ || '').replace(/\/+$/, '') || '/luft-docs';
    }

    _comPrefixo(caminho) {
        if (/^https?:\/\//i.test(caminho)) return caminho;
        const base = this._obterPrefixoBase();
        const p = caminho.startsWith('/') ? caminho : `/${caminho}`;
        return (p === base || p.startsWith(`${base}/`)) ? p : `${base}${p}`;
    }

    _obterToken() {
        const doBody = document.body?.dataset?.token;
        if (doBody) return doBody;
        return new URLSearchParams(window.location.search).get('token') || '';
    }

    _anexarToken(url) {
        const token = this._obterToken();
        if (!token) return url;
        const u = new URL(url, window.location.origin);
        if (!u.searchParams.get('token')) u.searchParams.set('token', token);
        return u.pathname + (u.search || '');
    }

    // ======================================================
    // HELPERS — DATA
    // ======================================================

    _formatarData(iso) {
        if (!iso) return null;
        const d = new Date(iso);
        return isNaN(d) ? null : d.toLocaleString();
    }

    _rotuloData(roteiro) {
        const criado  = roteiro.created_at ? new Date(roteiro.created_at) : null;
        const editado = roteiro.updated_at ? new Date(roteiro.updated_at) : null;
        if (criado && editado && editado.getTime() > criado.getTime() + 1000) {
            return `<small class="text-muted">Editado em ${this._formatarData(roteiro.updated_at)}</small>`;
        }
        return criado ? `<small class="text-muted">Criado em ${this._formatarData(roteiro.created_at)}</small>` : '';
    }

    // ======================================================
    // API
    // ======================================================

    async _chamarApi(caminho, metodo = 'GET', corpo = null) {
        try {
            const url = this._anexarToken(
                this._comPrefixo(caminho.startsWith('/') ? caminho : `${this.urlBase}/${caminho}`)
            );
            const opcoes = {
                method: metodo,
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                }
            };
            if (corpo) opcoes.body = JSON.stringify(corpo);

            const resposta = await fetch(url, opcoes);
            if (!resposta.ok) {
                let msg = `Erro na requisição (${resposta.status})`;
                try {
                    const dados = await resposta.json();
                    if (dados?.message) msg = dados.message;
                } catch {}
                throw new Error(msg);
            }
            const tipoConteudo = resposta.headers.get('content-type') || '';
            return tipoConteudo.includes('application/json') ? resposta.json() : {};
        } catch (erro) {
            console.error('GerenciadorRoteiros: Erro na API:', erro);
            alert('Erro: ' + (erro?.message || 'Falha de rede.'));
            return null;
        }
    }

    // ======================================================
    // RENDERIZAÇÃO
    // ======================================================

    _renderizarLista() {
        this.listaRoteiros.innerHTML = '';
        if (!this.roteiros.length) {
            this.listaRoteiros.innerHTML = '<li class="roteiro-vazio">Nenhum roteiro encontrado.</li>';
            return;
        }

        [...this.roteiros]
            .sort((a, b) => (a.ordem ?? 0) - (b.ordem ?? 0))
            .forEach(roteiro => {
                const li = document.createElement('li');

                const htmlAcoes = this.podeEditar ? `
                    <div class="roteiro-actions btn-group btn-group-sm">
                        <button class="btn btn-outline btn-edit-roteiro" data-id="${roteiro.id}" title="Editar">
                            <i class="bi bi-pencil-fill"></i>
                        </button>
                        <button class="btn btn-danger btn-delete-roteiro" data-id="${roteiro.id}" data-titulo="${roteiro.titulo}" title="Excluir">
                            <i class="bi bi-trash-fill"></i>
                        </button>
                    </div>` : '';

                const href = roteiro.conteudo || '#';
                li.innerHTML = `
                    <div class="roteiro-item-wrapper">
                        <div class="d-flex flex-col" style="flex:1;">
                            <a href="${href}" data-tipo="${roteiro.tipo || 'link'}" data-id="${roteiro.id}" class="roteiro-item">
                                <i class="${roteiro.icone || 'bi-play-circle'}"></i>
                                <span>${roteiro.titulo}</span>
                            </a>
                            <div class="mt-1">${this._rotuloData(roteiro)}</div>
                        </div>
                        ${htmlAcoes}
                    </div>
                `;
                this.listaRoteiros.appendChild(li);
            });
    }

    // ======================================================
    // EVENTOS
    // ======================================================

    _inicializarEventos() {
        if (this.btnCriar) {
            this.btnCriar.addEventListener('click', () => this._abrirModalCriar());
        }

        this.formulario.addEventListener('submit', (e) => this._manipularSubmissao(e));
        this.listaRoteiros.addEventListener('click', (e) => this._manipularCliqueLista(e));
        this.btnConfirmarExclusao.addEventListener('click', () => this._confirmarExclusao());

        document.getElementById('videoModal')?.addEventListener('hidden.bs.modal', () => {
            const player = document.getElementById('videoPlayer');
            if (player) player.src = '';
        });
    }

    _abrirModalCriar() {
        this.rotuloModal.textContent = 'Criar Novo Roteiro';
        this.formulario.reset();
        this.campoId.value    = '';
        this.campoOrdem.value = 0;
        this.modalRoteiro.show();
    }

    async _manipularSubmissao(e) {
        e.preventDefault();
        const id      = this.campoId.value.trim();
        const endpoint = id ? `${this.urlBase}/${id}` : `${this.urlBase}/`;
        const metodo  = id ? 'PUT' : 'POST';

        const carga = {
            titulo:   this.campoTitulo.value,
            tipo:     this.campoTipo.value,
            conteudo: this.campoConteudo.value,
            icone:    this.campoIcone.value,
            ordem:    parseInt(this.campoOrdem.value || '0', 10),
        };

        const resultado = await this._chamarApi(endpoint, metodo, carga);
        if (!resultado) return;

        if (!id && resultado.roteiro) {
            if (this.idModulo) {
                await this._chamarApi(`${this.urlBase}/vincular`, 'POST', {
                    roteiro_id: resultado.roteiro.id,
                    modulo_ids: [this.idModulo],
                });
            }
            this.roteiros.push({ ...resultado.roteiro });
        } else if (id && resultado.roteiro) {
            const indice = this.roteiros.findIndex(r => String(r.id) === String(id));
            if (indice > -1) this.roteiros[indice] = { ...this.roteiros[indice], ...resultado.roteiro };
        }

        this.modalRoteiro.hide();
        this._renderizarLista();
    }

    async _manipularCliqueLista(e) {
        const alvo = e.target.closest('a.roteiro-item, button.btn-edit-roteiro, button.btn-delete-roteiro');
        if (!alvo) return;

        const id = alvo.dataset.id;

        if (alvo.matches('a.roteiro-item')) {
            e.preventDefault();
            if ((alvo.dataset.tipo || 'link') === 'modal') {
                document.getElementById('videoPlayer').src = alvo.getAttribute('href');
                this.modalVideo.show();
            } else {
                window.open(alvo.getAttribute('href'), '_blank');
            }
            return;
        }

        if (alvo.matches('button.btn-edit-roteiro')) {
            const dados = await this._chamarApi(`${this.urlBase}/${id}`, 'GET');
            if (dados) {
                this.rotuloModal.textContent  = 'Editar Roteiro';
                this.campoId.value            = dados.id;
                this.campoTitulo.value        = dados.titulo   || '';
                this.campoTipo.value          = dados.tipo     || 'link';
                this.campoConteudo.value      = dados.conteudo || '';
                this.campoIcone.value         = dados.icone    || '';
                this.campoOrdem.value         = dados.ordem    ?? 0;

                const indice = this.roteiros.findIndex(r => String(r.id) === String(id));
                if (indice > -1) this.roteiros[indice] = { ...this.roteiros[indice], ...dados };

                this._renderizarLista();
                this.modalRoteiro.show();
            }
            return;
        }

        if (alvo.matches('button.btn-delete-roteiro')) {
            document.getElementById('roteiroNameToDelete').textContent = alvo.dataset.titulo || '';
            this.btnConfirmarExclusao.dataset.id = id;
            this.modalConfirmarExclusao.show();
        }
    }

    async _confirmarExclusao() {
        const id = this.btnConfirmarExclusao.dataset.id;
        const resultado = await this._chamarApi(`${this.urlBase}/${id}`, 'DELETE');
        if (resultado) {
            this.roteiros = this.roteiros.filter(r => String(r.id) !== String(id));
            this.modalConfirmarExclusao.hide();
            this._renderizarLista();
        }
    }
}

document.addEventListener('DOMContentLoaded', () => new GerenciadorRoteiros());

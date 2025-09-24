// static/js/roteiros.js

document.addEventListener('DOMContentLoaded', () => {
    const roteirosList = document.getElementById('roteiros-list');
    if (!roteirosList) return;

    const moduloId = document.body.dataset.moduloId;

    // Helpers
    function withPrefix(path) {
        if (/^https?:\/\//i.test(path)) return path;
        const BASE_PREFIX = (window.__BASE_PREFIX__ || '').replace(/\/+$/, '') || '/luft-docs';
        const p = path.startsWith('/') ? path : `/${path}`;
        if (p.startsWith(BASE_PREFIX)) return p;
        return `${BASE_PREFIX}${p}`;
    }

    // Modais
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

    let roteiros = JSON.parse(document.getElementById('roteiros-data').textContent);

    function renderRoteiros() {
        roteirosList.innerHTML = '';
        if (roteiros.length === 0) {
            roteirosList.innerHTML = '<li class="roteiro-vazio">Nenhum roteiro encontrado.</li>';
            return;
        }
        roteiros.sort((a, b) => a.ordem - b.ordem);
        roteiros.forEach(roteiro => {
            const li = document.createElement('li');
            li.innerHTML = `
                <div class="roteiro-item-wrapper">
                    <a href="${withPrefix(roteiro.conteudo)}"
                       data-tipo="${roteiro.tipo}"
                       data-id="${roteiro.id}"
                       class="roteiro-item">
                        <i class="${roteiro.icone || 'bi-play-circle'}"></i>
                        <span>${roteiro.titulo}</span>
                    </a>
                    <div class="roteiro-actions btn-group btn-group-sm">
                        <button class="btn btn-outline-secondary btn-edit-roteiro" data-id="${roteiro.id}" title="Editar">
                            <i class="bi bi-pencil-fill"></i>
                        </button>
                        <button class="btn btn-outline-danger btn-delete-roteiro" data-id="${roteiro.id}" data-titulo="${roteiro.titulo}" title="Excluir">
                            <i class="bi bi-trash-fill"></i>
                        </button>
                    </div>
                </div>
            `;
            roteirosList.appendChild(li);
        });
    }

    async function apiCall(url, method = 'GET', body = null) {
        try {
            const options = { method, headers: { 'Content-Type': 'application/json' } };
            if (body) options.body = JSON.stringify(body);
            const response = await fetch(withPrefix(url), options);
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.message || 'Erro na requisição.');
            }
            const contentType = response.headers.get("content-type");
            if (contentType && contentType.indexOf("application/json") !== -1) {
                return response.json();
            } else {
                return {};
            }
        } catch (error) {
            console.error('Erro na API:', error);
            alert('Erro: ' + error.message);
            return null;
        }
    }

    btnCriarRoteiro.addEventListener('click', () => {
        roteiroModalLabel.textContent = 'Criar Novo Roteiro';
        roteiroForm.reset();
        roteiroIdField.value = '';
        roteiroOrdemField.value = 0;
        roteiroModal.show();
    });

    roteiroForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const id = roteiroIdField.value;
        const url = id ? `/luft-docs/api/roteiros/${id}` : '/luft-docs/api/roteiros/';
        const method = id ? 'PUT' : 'POST';

        const data = {
            titulo: roteiroTituloField.value,
            tipo: roteiroTipoField.value,
            conteudo: roteiroConteudoField.value,
            icone: roteiroIconeField.value,
            ordem: parseInt(roteiroOrdemField.value, 10)
        };

        const result = await apiCall(url, method, data);
        if (result) {
            if (!id && result.roteiro) {
                await apiCall('/luft-docs/api/roteiros/vincular', 'POST', {
                    roteiro_id: result.roteiro.id,
                    modulo_ids: [moduloId]
                });
                roteiros.push({ ...data, id: result.roteiro.id });
            } else {
                const index = roteiros.findIndex(r => r.id == id);
                if (index > -1) roteiros[index] = { ...roteiros[index], ...data };
            }
            roteiroModal.hide();
            renderRoteiros();
        }
    });

    roteirosList.addEventListener('click', async (e) => {
        const target = e.target.closest('a.roteiro-item, button.btn-edit-roteiro, button.btn-delete-roteiro');
        if (!target) return;
        const id = target.dataset.id;

        if (target.matches('a.roteiro-item')) {
            e.preventDefault();
            const tipo = target.dataset.tipo;
            const conteudo = target.getAttribute('href');
            if (tipo === 'modal') {
                document.getElementById('videoPlayer').src = conteudo;
                videoModal.show();
            } else {
                window.open(conteudo, '_blank');
            }
        }

        if (target.matches('button.btn-edit-roteiro')) {
            const data = await apiCall(`/luft-docs/api/roteiros/${id}`);
            if (data) {
                roteiroModalLabel.textContent = 'Editar Roteiro';
                roteiroIdField.value = data.id;
                roteiroTituloField.value = data.titulo;
                roteiroTipoField.value = data.tipo;
                roteiroConteudoField.value = data.conteudo;
                roteiroIconeField.value = data.icone;
                roteiroOrdemField.value = data.ordem;
                roteiroModal.show();
            }
        }

        if (target.matches('button.btn-delete-roteiro')) {
            document.getElementById('roteiroNameToDelete').textContent = target.dataset.titulo;
            btnConfirmDelete.dataset.id = id;
            confirmDeleteModal.show();
        }
    });

    btnConfirmDelete.addEventListener('click', async () => {
        const id = btnConfirmDelete.dataset.id;
        const result = await apiCall(`/luft-docs/api/roteiros/${id}`, 'DELETE');
        if (result) {
            roteiros = roteiros.filter(r => r.id != id);
            confirmDeleteModal.hide();
            renderRoteiros();
        }
    });

    document.getElementById('videoModal').addEventListener('hidden.bs.modal', () => {
        document.getElementById('videoPlayer').src = '';
    });

    renderRoteiros();
});

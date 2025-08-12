document.addEventListener('DOMContentLoaded', () => {
    const roteirosList = document.getElementById('roteiros-list');
    if (!roteirosList) return;

    // --- 1. SETUP ---
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
    const permissionsData = JSON.parse(document.getElementById('roteiros-data').textContent);
    let roteiros = permissionsData.roteiros || [];
    const canEdit = permissionsData.can_edit;

    if (!moduloId) {
        console.error("ID do módulo não encontrado. A funcionalidade de Roteiros pode não funcionar corretamente.");
    }

    // --- 2. FUNÇÕES ---
    const fmt = (iso) => {
        if (!iso) return null;
        const d = new Date(iso);
        return isNaN(d) ? null : d.toLocaleString();
    };

    const dateLabel = (r) => {
        const created = r.created_at ? new Date(r.created_at) : null;
        const updated = r.updated_at ? new Date(r.updated_at) : null;

        if (created && updated && updated.getTime() > created.getTime() + 1000) { // +1s de margem
            return `<small class="text-muted">Editado em ${fmt(r.updated_at)}</small>`;
        }
        return created ? `<small class="text-muted">Criado em ${fmt(r.created_at)}</small>` : '';
    };

    const renderRoteiros = () => {
        roteirosList.innerHTML = '';
        if (roteiros.length === 0) {
            roteirosList.innerHTML = '<li class="roteiro-vazio">Nenhum roteiro encontrado.</li>';
            return;
        }
        roteiros
            .slice()
            .sort((a, b) => (a.ordem ?? 0) - (b.ordem ?? 0))
            .forEach(roteiro => {
                const li = document.createElement('li');
                const actionsHtml = canEdit ? `
                    <div class="roteiro-actions btn-group btn-group-sm">
                        <button class="btn btn-outline-secondary btn-edit-roteiro" data-id="${roteiro.id}" title="Editar"><i class="bi bi-pencil-fill"></i></button>
                        <button class="btn btn-outline-danger btn-delete-roteiro" data-id="${roteiro.id}" data-titulo="${roteiro.titulo}" title="Excluir"><i class="bi bi-trash-fill"></i></button>
                    </div>` : '';

                li.innerHTML = `
                    <div class="roteiro-item-wrapper">
                        <div class="d-flex flex-column flex-grow-1">
                            <a href="${roteiro.conteudo}" data-tipo="${roteiro.tipo}" data-id="${roteiro.id}" class="roteiro-item">
                                <i class="${roteiro.icone || 'bi-play-circle'}"></i>
                                <span>${roteiro.titulo}</span>
                            </a>
                            <div class="mt-1">${dateLabel(roteiro)}</div>
                        </div>
                        ${actionsHtml}
                    </div>`;
                roteirosList.appendChild(li);
            });
    };

    const apiCall = async (url, method = 'GET', body = null) => {
        try {
            const options = { method, headers: { 'Content-Type': 'application/json' } };
            if (body) options.body = JSON.stringify(body);
            const response = await fetch(url, options);
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.message || 'Erro na requisição.');
            }
            const contentType = response.headers.get("content-type");
            return contentType?.includes("application/json") ? response.json() : {};
        } catch (error) {
            alert('Erro: ' + error.message);
            return null;
        }
    };

    // --- 3. EVENTOS ---
    if (btnCriarRoteiro) {
        btnCriarRoteiro.addEventListener('click', () => {
            roteiroModalLabel.textContent = 'Criar Novo Roteiro';
            roteiroForm.reset();
            roteiroIdField.value = '';
            roteiroOrdemField.value = 0;
            roteiroModal.show();
        });
    }

    roteiroForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const id = roteiroIdField.value;
        const url = id ? `/api/roteiros/${id}` : '/api/roteiros/';
        const method = id ? 'PUT' : 'POST';
        const payload = {
            titulo: roteiroTituloField.value,
            tipo: roteiroTipoField.value,
            conteudo: roteiroConteudoField.value,
            icone: roteiroIconeField.value,
            ordem: parseInt(roteiroOrdemField.value || '0', 10)
        };

        const result = await apiCall(url, method, payload);
        if (!result) return;

        if (!id && result.roteiro) {
            await apiCall('/api/roteiros/vincular', 'POST', { roteiro_id: result.roteiro.id, modulo_ids: [moduloId] });
            roteiros.push({ ...result.roteiro });
        } else if (id && result.roteiro) {
            const index = roteiros.findIndex(r => String(r.id) === String(id));
            if (index > -1) {
                roteiros[index] = { ...roteiros[index], ...result.roteiro };
            }
        }

        roteiroModal.hide();
        renderRoteiros();
    });

    roteirosList.addEventListener('click', async (e) => {
        const target = e.target.closest('a.roteiro-item, button.btn-edit-roteiro, button.btn-delete-roteiro');
        if (!target) return;
        const id = target.dataset.id;

        if (target.matches('a.roteiro-item')) {
            e.preventDefault();
            if (target.dataset.tipo === 'modal') {
                document.getElementById('videoPlayer').src = target.getAttribute('href');
                videoModal.show();
            } else {
                window.open(target.getAttribute('href'), '_blank');
            }
        }

        if (target.matches('button.btn-edit-roteiro')) {
            const data = await apiCall(`/api/roteiros/${id}`);
            if (data) {
                roteiroModalLabel.textContent = 'Editar Roteiro';
                roteiroIdField.value = data.id;
                roteiroTituloField.value = data.titulo;
                roteiroTipoField.value = data.tipo;
                roteiroConteudoField.value = data.conteudo;
                roteiroIconeField.value = data.icone || '';
                roteiroOrdemField.value = data.ordem ?? 0;
                
                const idx = roteiros.findIndex(r => String(r.id) === String(id));
                if (idx > -1) roteiros[idx] = { ...roteiros[idx], ...data };
                renderRoteiros();
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
        const result = await apiCall(`/api/roteiros/${id}`, 'DELETE');
        if (result) {
            roteiros = roteiros.filter(r => String(r.id) !== String(id));
            confirmDeleteModal.hide();
            renderRoteiros();
        }
    });

    document.getElementById('videoModal').addEventListener('hidden.bs.modal', () => {
        document.getElementById('videoPlayer').src = '';
    });

    // --- 4. INICIALIZAÇÃO ---
    renderRoteiros();
});
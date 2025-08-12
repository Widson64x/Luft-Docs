// static/js/roteiros.js

document.addEventListener('DOMContentLoaded', () => {
    // Verifica se estamos na página de módulo e se os elementos necessários existem
    const roteirosList = document.getElementById('roteiros-list');
    if (!roteirosList) {
        return; // Sai do script se não for a página de módulo
    }

    // --- 1. SETUP INICIAL ---
    const moduloId = document.body.dataset.moduloId;
    
    // Modais
    const roteiroModal = new bootstrap.Modal(document.getElementById('roteiroModal'));
    const videoModal = new bootstrap.Modal(document.getElementById('videoModal'));
    const confirmDeleteModal = new bootstrap.Modal(document.getElementById('confirmDeleteModal'));

    // Formulário do Modal
    const roteiroForm = document.getElementById('roteiroForm');
    const roteiroModalLabel = document.getElementById('roteiroModalLabel');
    const roteiroIdField = document.getElementById('roteiroId');
    const roteiroTituloField = document.getElementById('roteiroTitulo');
    const roteiroTipoField = document.getElementById('roteiroTipo');
    const roteiroConteudoField = document.getElementById('roteiroConteudo');
    const roteiroIconeField = document.getElementById('roteiroIcone');
    const roteiroOrdemField = document.getElementById('roteiroOrdem');

    // Botões
    const btnCriarRoteiro = document.getElementById('btn-criar-roteiro');
    const btnConfirmDelete = document.getElementById('btnConfirmDelete');
    
    // Dados iniciais (passados do template para o JS)
    let roteiros = JSON.parse(document.getElementById('roteiros-data').textContent);

    // --- 2. FUNÇÕES DE RENDERIZAÇÃO E API ---

    /**
     * Renderiza a lista de roteiros na tela.
     */
    function renderRoteiros() {
        roteirosList.innerHTML = ''; // Limpa a lista atual
        
        if (roteiros.length === 0) {
            roteirosList.innerHTML = '<li class="roteiro-vazio">Nenhum roteiro encontrado.</li>';
            return;
        }
        
        // Ordena os roteiros pela propriedade 'ordem'
        roteiros.sort((a, b) => a.ordem - b.ordem);

        roteiros.forEach(roteiro => {
            const li = document.createElement('li');
            li.innerHTML = `
                <div class="roteiro-item-wrapper">
                    <a href="${roteiro.conteudo}" 
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

    /**
     * Função genérica para chamadas fetch
     */
    async function apiCall(url, method = 'GET', body = null) {
        try {
            const options = {
                method,
                headers: { 'Content-Type': 'application/json' }
            };
            if (body) {
                options.body = JSON.stringify(body);
            }
            const response = await fetch(url, options);
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.message || 'Ocorreu um erro na requisição.');
            }
            // Retorna um objeto vazio para respostas sem corpo (como DELETE)
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

    // --- 3. LÓGICA DE EVENTOS (CLICKS, SUBMIT, ETC) ---

    // Abrir modal para CRIAR um roteiro
    btnCriarRoteiro.addEventListener('click', () => {
        roteiroModalLabel.textContent = 'Criar Novo Roteiro';
        roteiroForm.reset();
        roteiroIdField.value = '';
        roteiroOrdemField.value = 0;
        roteiroModal.show();
    });

    // Lógica para o formulário de SALVAR (Criar ou Editar)
    roteiroForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const id = roteiroIdField.value;
        const url = id ? `/api/roteiros/${id}` : '/api/roteiros/';
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
            // Se for um novo roteiro, precisamos vinculá-lo a este módulo
            if (!id && result.roteiro) {
                await apiCall('/api/roteiros/vincular', 'POST', {
                    roteiro_id: result.roteiro.id,
                    modulo_ids: [moduloId]
                });
                // Adiciona o novo roteiro à lista local para renderização
                roteiros.push({ ...data, id: result.roteiro.id });
            } else {
                // Atualiza o roteiro na lista local
                const index = roteiros.findIndex(r => r.id == id);
                if (index > -1) {
                    roteiros[index] = { ...roteiros[index], ...data };
                }
            }
            
            roteiroModal.hide();
            renderRoteiros();
        }
    });

    // Delegação de eventos na lista de roteiros
    roteirosList.addEventListener('click', async (e) => {
        const target = e.target.closest('a.roteiro-item, button.btn-edit-roteiro, button.btn-delete-roteiro');
        if (!target) return;

        const id = target.dataset.id;
        
        // Ação: VER o roteiro (clicou no link principal)
        if (target.matches('a.roteiro-item')) {
            e.preventDefault();
            const tipo = target.dataset.tipo;
            const conteudo = target.getAttribute('href');

            if (tipo === 'modal') {
                document.getElementById('videoPlayer').src = conteudo;
                videoModal.show();
            } else {
                window.open(conteudo, '_blank'); // Abre link em nova aba
            }
        }
        
        // Ação: EDITAR o roteiro
        if (target.matches('button.btn-edit-roteiro')) {
            const data = await apiCall(`/api/roteiros/${id}`);
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
        
        // Ação: DELETAR o roteiro
        if (target.matches('button.btn-delete-roteiro')) {
            document.getElementById('roteiroNameToDelete').textContent = target.dataset.titulo;
            btnConfirmDelete.dataset.id = id;
            confirmDeleteModal.show();
        }
    });
    
    // Confirmação da exclusão
    btnConfirmDelete.addEventListener('click', async () => {
        const id = btnConfirmDelete.dataset.id;
        const result = await apiCall(`/api/roteiros/${id}`, 'DELETE');
        if (result) {
            // Remove o roteiro da lista local e renderiza novamente
            roteiros = roteiros.filter(r => r.id != id);
            confirmDeleteModal.hide();
            renderRoteiros();
        }
    });

    // Esconde o modal de vídeo quando ele é fechado para parar a reprodução
    document.getElementById('videoModal').addEventListener('hidden.bs.modal', () => {
        document.getElementById('videoPlayer').src = '';
    });

    // --- 4. INICIALIZAÇÃO ---
    renderRoteiros(); // Renderiza a lista inicial ao carregar a página
});
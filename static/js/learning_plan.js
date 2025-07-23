document.addEventListener('DOMContentLoaded', () => {
    // ---- ESTADO DA APLICAÇÃO ----
    let state = {
        trails: [],
        allModules: [],
        currentTrailId: null,
        cytoscapeInstance: null,
        sortableInstance: null
    };

    const apiToken = "{{ request.args.get('token') }}";

    // ---- ELEMENTOS DO DOM ----
    const trailsListEl = document.getElementById('trails-list');
    const trailTitleEl = document.getElementById('trail-title');
    const cyContainer = document.getElementById('cytoscape-container');

    // ---- MODAIS ----
    const createTrailModal = new bootstrap.Modal(document.getElementById('createTrailModal'));
    const editTrailModal = new bootstrap.Modal(document.getElementById('editTrailModal'));
    const addModuleModal = new bootstrap.Modal(document.getElementById('addModuleModal'));

    // ---- FUNÇÕES DE RENDERIZAÇÃO ----

    /** Renderiza a lista de trilhas na barra lateral */
    function renderNavigator() {
        trailsListEl.innerHTML = '';
        state.trails.forEach(trail => {
            const isActive = trail.id == state.currentTrailId;
            const trailEl = document.createElement('div');
            trailEl.className = `trail-link ${isActive ? 'active' : ''}`;
            trailEl.dataset.trailId = trail.id;

            let actionsHtml = '';
            if (trail.id !== 'recommended') {
                actionsHtml = `
                    <div class="trail-actions">
                        <button class="btn btn-outline-primary btn-edit" title="Editar"><i class="bi bi-pencil-fill"></i></button>
                        <button class="btn btn-outline-danger btn-delete" title="Deletar"><i class="bi bi-trash-fill"></i></button>
                    </div>`;
            }

            trailEl.innerHTML = `
                <span><i class="bi bi-compass me-2"></i>${trail.name}</span>
                ${actionsHtml}
            `;
            trailsListEl.appendChild(trailEl);
        });
    }

    /** Carrega os dados de uma trilha e renderiza o gráfico */
    async function loadTrailData(trailId) {
        state.currentTrailId = trailId;
        renderNavigator(); // Re-renderiza para destacar a trilha ativa

        try {
            const response = await fetch(`/api/trail-data/${trailId}?token=${apiToken}`);
            if (!response.ok) throw new Error('Falha ao carregar dados da trilha.');
            
            const data = await response.json();
            trailTitleEl.textContent = data.trail_name;
            
            // Inicializa ou atualiza o Cytoscape
            state.cytoscapeInstance = cytoscape({
                container: cyContainer,
                elements: data.cytoscape_elements,
                style: [
                    { selector: 'node', style: { 'background-color': '#0d6efd', 'label': 'data(label)', 'color': '#fff', 'text-halign': 'center', 'text-valign': 'center', 'font-size': '10px' } },
                    { selector: 'edge', style: { 'width': 2, 'line-color': '#ced4da', 'target-arrow-color': '#ced4da', 'target-arrow-shape': 'triangle' } },
                    { selector: '.completed', style: { 'background-color': '#198754', 'border-color': '#157347', 'border-width': 2 } },
                    { selector: '[type="trail_center"]', style: { 'shape': 'star', 'background-color': '#ffc107', 'font-size': '14px', 'color': '#000' } }
                ],
                layout: { name: 'concentric', concentric: (node) => node.is('[type="trail_center"]') ? 2 : 1, minNodeSpacing: 100 }
            });

        } catch (error) {
            console.error(error);
            trailTitleEl.textContent = "Erro ao carregar trilha";
        }
    }

    // ---- MANIPULADORES DE EVENTOS ----
    
    // Evento para criar trilha
    document.getElementById('createTrailForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        const trailName = document.getElementById('newTrailName').value;
        
        const response = await fetch(`/api/trails?token=${apiToken}`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ trail_name: trailName })
        });

        if (response.ok) {
            const result = await response.json();
            createTrailModal.hide();
            document.getElementById('createTrailForm').reset();
            state.trails.push(result.new_trail);
            loadTrailData(result.new_trail.id);
        } else {
            alert('Erro ao criar a trilha.');
        }
    });

    // Delegação de eventos para a lista de trilhas (clicar, editar, deletar)
    trailsListEl.addEventListener('click', async (e) => {
        const trailLink = e.target.closest('.trail-link');
        if (!trailLink) return;

        const trailId = trailLink.dataset.trailId;

        if (e.target.closest('.btn-edit')) {
            openEditModal(trailId);
        } else if (e.target.closest('.btn-delete')) {
            if (confirm(`Tem certeza que deseja deletar a trilha "${trailLink.querySelector('span').textContent}"?`)) {
                await handleDeleteTrail(trailId);
            }
        } else {
            loadTrailData(trailId);
        }
    });

    /** Abre e prepara o modal de edição */
    async function openEditModal(trailId) {
        // Busca os dados da trilha e a lista de todos os módulos em paralelo
        const [trailRes, allModulesRes] = await Promise.all([
            fetch(`/api/trail-data/${trailId}?token=${apiToken}`),
            fetch(`/api/all-modules?token=${apiToken}`)
        ]);

        if (!trailRes.ok || !allModulesRes.ok) {
            alert("Erro ao carregar dados para edição.");
            return;
        }

        const trailData = await trailRes.json();
        state.allModules = await allModulesRes.json();
        
        // Popula o formulário de edição
        const editModalEl = document.getElementById('editTrailModal');
        editModalEl.dataset.trailId = trailId;
        document.getElementById('editTrailName').value = trailData.trail_name;

        // Renderiza a lista de módulos arrastáveis
        const moduleListEl = document.getElementById('edit-modules-list');
        moduleListEl.innerHTML = '';
        const currentModuleIds = new Set();

        trailData.module_ids.forEach(moduleId => {
            const module = state.allModules.find(m => m.id === moduleId);
            if (module) {
                addModuleToEditList(module);
                currentModuleIds.add(module.id);
            }
        });
        
        // Renderiza a lista de módulos para adicionar
        const allModulesListEl = document.getElementById('all-modules-list');
        allModulesListEl.innerHTML = '';
        state.allModules.forEach(module => {
            // Só mostra módulos que ainda não estão na trilha
            if (!currentModuleIds.has(module.id)) {
                 const li = document.createElement('li');
                 li.className = 'list-group-item list-group-item-action';
                 li.textContent = module.module_name;
                 li.dataset.moduleId = module.id;
                 li.style.cursor = 'pointer';
                 li.addEventListener('click', () => {
                    addModuleToEditList(module);
                    li.remove(); // Remove da lista de "disponíveis"
                 });
                 allModulesListEl.appendChild(li);
            }
        });

        // Inicializa o SortableJS
        if (state.sortableInstance) state.sortableInstance.destroy();
        state.sortableInstance = new Sortable(moduleListEl, {
            animation: 150,
            ghostClass: 'bg-primary-subtle'
        });

        editTrailModal.show();
    }
    
    /** Adiciona um item de módulo à lista do modal de edição */
    function addModuleToEditList(module) {
        const moduleListEl = document.getElementById('edit-modules-list');
        const li = document.createElement('li');
        li.className = 'module-item';
        li.dataset.moduleId = module.id;
        li.innerHTML = `
            <span><i class="bi bi-grip-vertical me-2"></i>${module.module_name}</span>
            <button type="button" class="btn-close" aria-label="Remover"></button>
        `;
        li.querySelector('.btn-close').addEventListener('click', () => {
            li.remove();
            // Lógica para devolver o módulo à lista de "adicionar" (opcional, mas melhora a UX)
        });
        moduleListEl.appendChild(li);
    }
    
    // Filtro para o modal de "Adicionar Módulo"
    document.getElementById('filterModulesInput').addEventListener('input', (e) => {
        const filterText = e.target.value.toLowerCase();
        document.querySelectorAll('#all-modules-list li').forEach(li => {
            const moduleName = li.textContent.toLowerCase();
            li.style.display = moduleName.includes(filterText) ? '' : 'none';
        });
    });
    
    // Salvar alterações da edição
    document.getElementById('saveTrailChangesBtn').addEventListener('click', async () => {
        const trailId = document.getElementById('editTrailModal').dataset.trailId;
        const newName = document.getElementById('editTrailName').value;
        
        const moduleItems = document.querySelectorAll('#edit-modules-list li');
        const moduleIds = Array.from(moduleItems).map(li => parseInt(li.dataset.moduleId));

        const response = await fetch(`/api/trails/${trailId}?token=${apiToken}`, {
            method: 'PUT',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ trail_name: newName, modules: moduleIds })
        });

        if (response.ok) {
            editTrailModal.hide();
            await init(); // Recarrega tudo para refletir as mudanças
            loadTrailData(trailId); // Foca na trilha que acabamos de editar
        } else {
            alert('Erro ao salvar as alterações.');
        }
    });

    /** Deleta uma trilha */
    async function handleDeleteTrail(trailId) {
        const response = await fetch(`/api/trails/${trailId}?token=${apiToken}`, {
            method: 'DELETE'
        });

        if(response.ok) {
            await init(); // Recarrega tudo
        } else {
            alert('Erro ao deletar a trilha.');
        }
    }


    // ---- INICIALIZAÇÃO ----
    async function init() {
        try {
            const response = await fetch(`/api/navigator-data?token=${apiToken}`);
            if (!response.ok) throw new Error('Falha ao buscar dados do navegador.');
            
            const data = await response.json();
            state.trails = data.trails;
            
            // Carrega a trilha recomendada por padrão ou a primeira trilha, se houver
            const initialTrailId = state.trails.length > 0 ? state.trails[0].id : null;
            if (initialTrailId) {
                await loadTrailData(initialTrailId);
            } else {
                trailTitleEl.textContent = "Nenhuma trilha encontrada. Crie uma!";
                renderNavigator();
            }
        } catch (error) {
            console.error(error);
            trailTitleEl.textContent = 'Erro ao carregar o dashboard.';
        }
    }

    init();
});
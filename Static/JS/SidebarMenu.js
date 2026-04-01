(function () {
    class SidebarModulesTree {
        constructor(root) {
            this.root = root;
            this.searchInput = root.querySelector('[data-modules-search]');
            this.stateElement = root.querySelector('[data-modules-state]');
            this.groupsElement = root.querySelector('[data-modules-groups]');
            this.countElement = root.querySelector('[data-modules-count]');
            this.summaryElement = root.querySelector('[data-modules-summary]');
            this.clearButton = root.querySelector('[data-modules-clear]');
            this.expandAllButton = root.querySelector('[data-modules-expand-all]');
            this.quickSearchButton = root.querySelector('[data-modules-quick-search]');
            this.viewButtons = Array.from(root.querySelectorAll('[data-modules-view-trigger]'));
            this.modulesUrl = root.dataset.modulesUrl || '';
            this.moduleBaseUrl = root.dataset.moduleBaseUrl || '';
            this.activeModuleId = root.dataset.activeModuleId || '';
            this.openOnLoad = root.dataset.openOnLoad === 'true';
            this.navWrapper = root.closest('.luft-nav-wrapper');
            this.toggleButton = this.navWrapper?.querySelector('.luft-nav-link');
            this.submenuElement = this.navWrapper?.querySelector('.luft-nav-submenu');
            this.modules = [];
            this.isLoaded = false;
            this.isLoading = false;
            this.stateKey = 'luftdocs.sidebar.explorer.state';
            this.recentKey = 'luftdocs.sidebar.explorer.recent';
            this.state = this.loadState();
            this.pendingScrollTop = this.state.scrollTop || 0;

            if (this.searchInput && this.state.searchTerm) {
                this.searchInput.value = this.state.searchTerm;
            }

            this.bindEvents();
            this.restoreMenuState();
        }

        bindEvents() {
            if (this.toggleButton) {
                this.toggleButton.addEventListener('click', () => {
                    window.setTimeout(() => {
                        this.saveState({ submenuOpen: this.isSubmenuOpen() });
                        if (this.isSubmenuOpen() && !this.isLoaded) {
                            this.loadModules();
                        }
                    }, 180);
                });
            }

            if (this.searchInput) {
                this.searchInput.addEventListener('input', () => {
                    this.pendingScrollTop = 0;
                    this.saveState({ searchTerm: this.searchInput.value, scrollTop: 0 });
                    this.render();
                });
            }

            this.viewButtons.forEach((button) => {
                button.addEventListener('click', () => {
                    const view = button.dataset.modulesViewTrigger || 'all';
                    if (view === this.state.selectedView) {
                        return;
                    }

                    this.pendingScrollTop = 0;
                    this.saveState({ selectedView: view, scrollTop: 0, openGroups: [] });
                    this.render();
                });
            });

            if (this.clearButton) {
                this.clearButton.addEventListener('click', () => {
                    if (!this.searchInput) {
                        return;
                    }

                    this.searchInput.value = '';
                    this.pendingScrollTop = 0;
                    this.saveState({ searchTerm: '', scrollTop: 0 });
                    this.render();
                    this.searchInput.focus();
                });
            }

            if (this.expandAllButton) {
                this.expandAllButton.addEventListener('click', () => this.toggleAllGroups());
            }

            if (this.quickSearchButton) {
                this.quickSearchButton.addEventListener('click', () => this.openQuickSearch());
            }

            if (this.groupsElement) {
                this.groupsElement.addEventListener('scroll', () => {
                    this.saveState({ scrollTop: this.groupsElement.scrollTop });
                });

                this.groupsElement.addEventListener('click', (event) => {
                    const moduleLink = event.target.closest('.luftdocs-sidebar-module-link');
                    if (!moduleLink) {
                        return;
                    }

                    this.rememberModule({
                        id: moduleLink.dataset.moduleId || '',
                        nome: moduleLink.dataset.moduleName || moduleLink.dataset.moduleId || '',
                        icone: moduleLink.dataset.moduleIcon || 'ph-bold ph-cube',
                    });

                    this.saveState({
                        submenuOpen: this.isSubmenuOpen(),
                        scrollTop: this.groupsElement.scrollTop,
                    });
                });
            }
        }

        restoreMenuState() {
            const shouldOpenMenu = this.openOnLoad || this.state.submenuOpen || Boolean(this.state.searchTerm);

            if (shouldOpenMenu && this.toggleButton && !this.isSubmenuOpen()) {
                window.requestAnimationFrame(() => this.toggleButton.click());
            }

            if (shouldOpenMenu) {
                window.setTimeout(() => this.loadModules(), 180);
            }
        }

        async loadModules() {
            if (this.isLoaded || this.isLoading || !this.modulesUrl) {
                return;
            }

            this.isLoading = true;
            this.setState('Carregando módulos...');
            this.updateSummary('Sincronizando a biblioteca da sidebar.');

            try {
                const resposta = await fetch(this.modulesUrl, {
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                    },
                });

                if (!resposta.ok) {
                    throw new Error(`Falha ao carregar sidebar: ${resposta.status}`);
                }

                const payload = await resposta.json();
                this.modules = Array.isArray(payload.modules) ? payload.modules : [];
                if (this.activeModuleId) {
                    const activeModule = this.modules.find((module) => module.id === this.activeModuleId);
                    if (activeModule) {
                        this.rememberModule(activeModule);
                    }
                }
                this.isLoaded = true;
                this.render();
            } catch (erro) {
                console.error('Erro ao carregar árvore de módulos da sidebar:', erro);
                this.setState('Não foi possível carregar os módulos agora.');
                this.updateCount('--');
                this.updateSummary('Tente novamente em alguns instantes.');
            } finally {
                this.isLoading = false;
            }
        }

        render() {
            if (!this.isLoaded) {
                return;
            }

            const termo = this.normalize(this.searchInput?.value || '');
            const sourceModules = this.getModulesForCurrentView();
            const filteredModules = sourceModules.filter((module) => {
                if (!termo) {
                    return true;
                }

                return this.normalize(`${module.nome || ''} ${module.id || ''}`).includes(termo);
            });

            this.toggleViewButtons();
            this.toggleClearButton();
            this.updateCount(String(filteredModules.length));
            this.updateSummary(this.describeCurrentState(filteredModules.length, sourceModules.length, Boolean(termo)));

            if (!filteredModules.length) {
                this.groupsElement.hidden = true;
                this.setState(this.getEmptyMessage(Boolean(termo)));
                this.updateExpandButtonLabel();
                return;
            }

            const groups = this.state.selectedView === 'recent'
                ? this.groupRecentModules(filteredModules)
                : this.groupModulesAlphabetically(filteredModules);
            const expandAll = Boolean(termo);

            this.groupsElement.innerHTML = groups.map((group) => {
                const isOpen = this.shouldOpenGroup(group, groups.length, expandAll);
                return `
                    <details class="luftdocs-sidebar-group" data-group-key="${this.escapeAttribute(group.key)}" ${isOpen ? 'open' : ''}>
                        <summary>
                            <span class="luftdocs-sidebar-group-title">${this.escapeHtml(group.label)}</span>
                            <span class="luftdocs-sidebar-group-meta">${group.items.length}</span>
                        </summary>
                        <div class="luftdocs-sidebar-group-items">
                            ${group.items.map((item) => this.renderModule(item)).join('')}
                        </div>
                    </details>
                `;
            }).join('');

            this.bindGroupState();
            this.stateElement.hidden = true;
            this.groupsElement.hidden = false;
            this.restoreScrollPosition();
            this.updateExpandButtonLabel();
        }

        renderModule(module) {
            const isActive = module.id === this.activeModuleId;
            const icon = this.formatIcon(module.icone);

            return `
                <a class="luftdocs-sidebar-module-link ${isActive ? 'is-active' : ''}"
                   href="${this.buildModuleUrl(module.id)}"
                   data-module-id="${this.escapeAttribute(module.id || '')}"
                   data-module-name="${this.escapeAttribute(module.nome || module.id || '')}"
                   data-module-icon="${this.escapeAttribute(icon)}">
                    <span class="luftdocs-sidebar-module-main">
                        <i class="${icon}"></i>
                        <span class="luftdocs-sidebar-module-copy">
                            <strong>${this.escapeHtml(module.nome || module.id)}</strong>
                            <small>${this.escapeHtml(module.id || '')}</small>
                        </span>
                    </span>
                    <i class="ph-bold ph-arrow-up-right luftdocs-sidebar-module-arrow"></i>
                </a>
            `;
        }

        bindGroupState() {
            this.groupsElement.querySelectorAll('.luftdocs-sidebar-group').forEach((group) => {
                group.addEventListener('toggle', () => {
                    const openGroups = Array.from(this.groupsElement.querySelectorAll('.luftdocs-sidebar-group[open]'))
                        .map((item) => item.dataset.groupKey || '')
                        .filter(Boolean);

                    this.saveState({ openGroups });
                    this.updateExpandButtonLabel();
                });
            });
        }

        toggleAllGroups() {
            const groups = Array.from(this.groupsElement.querySelectorAll('.luftdocs-sidebar-group'));
            if (!groups.length) {
                return;
            }

            const shouldOpen = groups.some((group) => !group.open);
            groups.forEach((group) => {
                group.open = shouldOpen;
            });

            this.saveState({
                openGroups: shouldOpen ? groups.map((group) => group.dataset.groupKey || '').filter(Boolean) : [],
            });
            this.updateExpandButtonLabel();
        }

        openQuickSearch() {
            if (typeof LuftCore !== 'undefined' && typeof LuftCore.abrirModal === 'function') {
                LuftCore.abrirModal('modalBusca');
                window.setTimeout(() => {
                    document.getElementById('kpModalInput')?.focus();
                }, 120);
            }
        }

        getModulesForCurrentView() {
            if (this.state.selectedView === 'recent') {
                return this.getRecentModules();
            }

            return this.modules.slice();
        }

        getRecentModules() {
            const recentModules = this.readJson(localStorage, this.recentKey, []);
            if (!Array.isArray(recentModules) || !recentModules.length) {
                return [];
            }

            const byId = new Map(this.modules.map((module) => [module.id, module]));
            return recentModules
                .map((recent) => byId.get(recent.id) || recent)
                .filter((module) => module && module.id);
        }

        rememberModule(module) {
            if (!module.id) {
                return;
            }

            const recentModules = this.readJson(localStorage, this.recentKey, []);
            const sanitizedModule = {
                id: module.id,
                nome: module.nome || module.id,
                icone: this.formatIcon(module.icone),
            };
            const nextModules = [sanitizedModule].concat(
                recentModules.filter((item) => item.id !== sanitizedModule.id)
            ).slice(0, 8);

            this.writeJson(localStorage, this.recentKey, nextModules);
        }

        groupRecentModules(modules) {
            return [{
                key: 'recent',
                label: 'Últimos acessos',
                items: modules,
            }];
        }

        groupModulesAlphabetically(modules) {
            const groups = new Map();

            modules.forEach((module) => {
                const baseName = (module.nome || module.id || '').trim();
                const firstLetter = baseName.charAt(0).toUpperCase();
                const letter = /[A-Z0-9]/.test(firstLetter) ? firstLetter : '#';

                if (!groups.has(letter)) {
                    groups.set(letter, []);
                }

                groups.get(letter).push(module);
            });

            return Array.from(groups.entries())
                .sort(([letterA], [letterB]) => letterA.localeCompare(letterB, 'pt-BR'))
                .map(([letter, items]) => ({
                    key: letter,
                    label: letter,
                    items: items.sort((moduleA, moduleB) => {
                        const nameA = moduleA.nome || moduleA.id || '';
                        const nameB = moduleB.nome || moduleB.id || '';
                        return nameA.localeCompare(nameB, 'pt-BR', { sensitivity: 'base' });
                    }),
                }));
        }

        shouldOpenGroup(group, totalGroups, expandAll) {
            if (expandAll) {
                return true;
            }

            const openGroups = Array.isArray(this.state.openGroups) ? this.state.openGroups : [];
            if (openGroups.length) {
                return openGroups.includes(group.key);
            }

            return group.items.some((item) => item.id === this.activeModuleId) || totalGroups <= 3;
        }

        restoreScrollPosition() {
            const targetScrollTop = Number.isFinite(this.pendingScrollTop) ? this.pendingScrollTop : 0;
            window.requestAnimationFrame(() => {
                this.groupsElement.scrollTop = targetScrollTop;
                this.pendingScrollTop = targetScrollTop;
            });
        }

        toggleViewButtons() {
            this.viewButtons.forEach((button) => {
                const isActive = (button.dataset.modulesViewTrigger || 'all') === this.state.selectedView;
                button.classList.toggle('is-active', isActive);
                button.setAttribute('aria-selected', isActive ? 'true' : 'false');
            });
        }

        toggleClearButton() {
            if (this.clearButton) {
                this.clearButton.hidden = !(this.searchInput && this.searchInput.value.trim());
            }
        }

        updateExpandButtonLabel() {
            if (!this.expandAllButton) {
                return;
            }

            if (this.groupsElement.hidden) {
                this.expandAllButton.textContent = 'Expandir';
                return;
            }

            const groups = Array.from(this.groupsElement.querySelectorAll('.luftdocs-sidebar-group'));
            const allOpen = groups.length > 0 && groups.every((group) => group.open);
            this.expandAllButton.textContent = allOpen ? 'Recolher' : 'Expandir';
        }

        describeCurrentState(visibleCount, sourceCount, isFiltering) {
            if (this.state.selectedView === 'recent') {
                if (isFiltering) {
                    return `${visibleCount} de ${sourceCount} recente${sourceCount === 1 ? '' : 's'} visíveis.`;
                }

                return visibleCount === 0
                    ? 'Seus últimos módulos acessados aparecerão aqui.'
                    : `${visibleCount} acesso${visibleCount === 1 ? '' : 's'} recente${visibleCount === 1 ? '' : 's'} disponível${visibleCount === 1 ? '' : 'eis'}.`;
            }

            if (isFiltering) {
                return `${visibleCount} de ${sourceCount} módulos correspondem ao filtro atual.`;
            }

            return `${sourceCount} módulos prontos para acesso rápido.`;
        }

        getEmptyMessage(isFiltering) {
            if (this.state.selectedView === 'recent' && !isFiltering) {
                return 'Abra algum módulo e os últimos acessos vão aparecer aqui.';
            }

            if (this.state.selectedView === 'recent') {
                return 'Nenhum módulo recente combina com esse filtro.';
            }

            return 'Nenhum módulo encontrado para esse filtro.';
        }

        buildModuleUrl(moduleId) {
            const url = new URL(this.moduleBaseUrl, window.location.origin);
            url.searchParams.set('modulo', moduleId);
            return `${url.pathname}${url.search}`;
        }

        formatIcon(iconClass) {
            if (!iconClass) {
                return 'ph-bold ph-cube';
            }

            if (iconClass.includes('ph-')) {
                return iconClass;
            }

            return iconClass.replace('bi bi-', 'ph-bold ph-').replace('bi-', 'ph-bold ph-');
        }

        setState(message) {
            this.stateElement.textContent = message;
            this.stateElement.hidden = false;
        }

        updateCount(text) {
            if (this.countElement) {
                this.countElement.textContent = text;
            }
        }

        updateSummary(text) {
            if (this.summaryElement) {
                this.summaryElement.textContent = text;
            }
        }

        isSubmenuOpen() {
            return Boolean(this.submenuElement && this.submenuElement.classList.contains('aberto'));
        }

        loadState() {
            const state = this.readJson(sessionStorage, this.stateKey, {});
            return {
                searchTerm: typeof state.searchTerm === 'string' ? state.searchTerm : '',
                selectedView: state.selectedView === 'recent' ? 'recent' : 'all',
                openGroups: Array.isArray(state.openGroups) ? state.openGroups : [],
                scrollTop: Number.isFinite(state.scrollTop) ? state.scrollTop : 0,
                submenuOpen: Boolean(state.submenuOpen),
            };
        }

        saveState(patch) {
            this.state = {
                ...this.state,
                ...patch,
            };
            this.writeJson(sessionStorage, this.stateKey, this.state);
        }

        readJson(storage, key, fallback) {
            try {
                const raw = storage.getItem(key);
                return raw ? JSON.parse(raw) : fallback;
            } catch (_error) {
                return fallback;
            }
        }

        writeJson(storage, key, value) {
            try {
                storage.setItem(key, JSON.stringify(value));
            } catch (_error) {
                return;
            }
        }

        normalize(value) {
            return String(value)
                .normalize('NFD')
                .replace(/[\u0300-\u036f]/g, '')
                .toLowerCase()
                .trim();
        }

        escapeHtml(value) {
            return String(value).replace(/[&<>"']/g, (character) => {
                const entities = {
                    '&': '&amp;',
                    '<': '&lt;',
                    '>': '&gt;',
                    '"': '&quot;',
                    "'": '&#39;',
                };
                return entities[character] || character;
            });
        }

        escapeAttribute(value) {
            return this.escapeHtml(value).replace(/`/g, '&#96;');
        }
    }

    document.addEventListener('DOMContentLoaded', () => {
        document.querySelectorAll('[data-sidebar-modules-root]').forEach((root) => {
            new SidebarModulesTree(root);
        });
    });
})();
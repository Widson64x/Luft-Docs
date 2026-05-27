(function inicializarMarkdownEditor(global) {
    const cacheSubmodulos = new Map();

    function resolverElemento(referencia) {
        if (!referencia) {
            return null;
        }

        if (referencia instanceof Element) {
            return referencia;
        }

        return document.querySelector(referencia);
    }

    function normalizarBusca(valor) {
        return String(valor || '')
            .normalize('NFD')
            .replace(/[\u0300-\u036f]/g, '')
            .toLowerCase()
            .trim();
    }

    function ordenarSubmodulos(submodulos) {
        return [...submodulos].sort((submoduloA, submoduloB) => {
            const labelA = String(submoduloA.label || submoduloA.name || '');
            const labelB = String(submoduloB.label || submoduloB.name || '');
            const comparacaoLabels = labelA.localeCompare(labelB, 'pt-BR', { sensitivity: 'base' });
            if (comparacaoLabels !== 0) {
                return comparacaoLabels;
            }

            return String(submoduloA.path || '').localeCompare(String(submoduloB.path || ''), 'pt-BR', { sensitivity: 'base' });
        });
    }

    async function carregarSubmodulos(listEndpoint, token) {
        if (!listEndpoint) {
            throw new Error('A rota de listagem de submodulos nao foi configurada.');
        }

        if (!global.LuftDocs?.requestJson) {
            throw new Error('O helper global de requisicoes nao esta disponivel.');
        }

        const chaveCache = `${listEndpoint}::${token || ''}`;
        if (cacheSubmodulos.has(chaveCache)) {
            return cacheSubmodulos.get(chaveCache);
        }

        const promessa = global.LuftDocs.requestJson(listEndpoint, {
            token,
            query: { formato: 'json' },
        })
            .then(({ response, data }) => {
                if (!response.ok) {
                    throw new Error(data?.error || 'Nao foi possivel carregar os submodulos.');
                }

                const submodulos = Array.isArray(data?.submodules) ? data.submodules : [];
                return ordenarSubmodulos(
                    submodulos
                        .map(submodulo => ({
                            name: String(submodulo?.name || '').trim(),
                            label: String(submodulo?.label || submodulo?.name || '').trim(),
                            path: String(submodulo?.path || '').trim(),
                        }))
                        .filter(submodulo => submodulo.name && submodulo.path)
                );
            })
            .catch(erro => {
                cacheSubmodulos.delete(chaveCache);
                throw erro;
            });

        cacheSubmodulos.set(chaveCache, promessa);
        return promessa;
    }

    function abrirSeletorSubmodulo({ submodulos, termoInicial }) {
        return new Promise(resolve => {
            const doc = global.document;
            const elementoAtivo = doc.activeElement;
            const fundo = doc.createElement('div');
            fundo.className = 'luft-editor-combobox-backdrop';
            fundo.innerHTML = `
                <div class="luft-editor-combobox-dialog" role="dialog" aria-modal="true" aria-labelledby="luftEditorComboboxTitle">
                    <div class="luft-editor-combobox-header">
                        <div>
                            <h3 class="luft-editor-combobox-title" id="luftEditorComboboxTitle">Citar submodulo</h3>
                            <p class="luft-editor-combobox-subtitle">Selecione o submodulo global para inserir a referencia em formato wikilink.</p>
                        </div>
                        <button type="button" class="luft-btn luft-btn-outline luft-btn-sm luft-editor-combobox-close" data-action="cancelar" aria-label="Fechar seletor">Fechar</button>
                    </div>
                    <div class="luft-editor-combobox-body">
                        <label class="luft-editor-combobox-label" for="luftEditorComboboxSearch">Buscar submodulo</label>
                        <input type="search" id="luftEditorComboboxSearch" class="luft-editor-combobox-search" placeholder="Digite parte do nome ou do caminho">
                        <label class="luft-editor-combobox-label" for="luftEditorComboboxSelect">Submodulos disponiveis</label>
                        <select id="luftEditorComboboxSelect" class="luft-editor-combobox-select" size="9"></select>
                        <p class="luft-editor-combobox-helper" id="luftEditorComboboxHelper"></p>
                    </div>
                    <div class="luft-editor-combobox-footer">
                        <button type="button" class="luft-btn luft-btn-outline" data-action="cancelar">Cancelar</button>
                        <button type="button" class="luft-btn luft-btn-primary" data-action="confirmar">Inserir referencia</button>
                    </div>
                </div>
            `;

            const inputBusca = fundo.querySelector('#luftEditorComboboxSearch');
            const selectSubmodulos = fundo.querySelector('#luftEditorComboboxSelect');
            const textoAjuda = fundo.querySelector('#luftEditorComboboxHelper');
            const botaoConfirmar = fundo.querySelector('[data-action="confirmar"]');
            const botoesCancelar = fundo.querySelectorAll('[data-action="cancelar"]');
            let submodulosFiltrados = [];

            function obterSelecionado() {
                return submodulosFiltrados.find(submodulo => submodulo.path === selectSubmodulos.value) || submodulosFiltrados[0] || null;
            }

            function atualizarBotaoConfirmar() {
                const selecionado = obterSelecionado();
                botaoConfirmar.disabled = !selecionado;
                botaoConfirmar.textContent = selecionado
                    ? `Inserir [[${selecionado.name}]]`
                    : 'Inserir referencia';
            }

            function renderizarOpcoes(filtro) {
                const termo = normalizarBusca(filtro);
                submodulosFiltrados = submodulos.filter(submodulo => {
                    if (!termo) {
                        return true;
                    }

                    return [submodulo.name, submodulo.label, submodulo.path]
                        .some(valor => normalizarBusca(valor).includes(termo));
                });

                selectSubmodulos.innerHTML = '';

                if (!submodulosFiltrados.length) {
                    const opcaoVazia = doc.createElement('option');
                    opcaoVazia.textContent = 'Nenhum submodulo encontrado para esse filtro.';
                    opcaoVazia.disabled = true;
                    opcaoVazia.selected = true;
                    selectSubmodulos.appendChild(opcaoVazia);
                    textoAjuda.textContent = 'Ajuste a busca para localizar outro submodulo.';
                    atualizarBotaoConfirmar();
                    return;
                }

                submodulosFiltrados.forEach(submodulo => {
                    const opcao = doc.createElement('option');
                    opcao.value = submodulo.path;
                    opcao.textContent = submodulo.label;
                    opcao.title = submodulo.path;
                    selectSubmodulos.appendChild(opcao);
                });

                const termoNormalizado = normalizarBusca(filtro);
                const correspondenciaExata = termoNormalizado
                    ? submodulosFiltrados.find(submodulo => normalizarBusca(submodulo.name) === termoNormalizado)
                    : null;

                selectSubmodulos.value = correspondenciaExata?.path || submodulosFiltrados[0].path;
                textoAjuda.textContent = `${submodulosFiltrados.length} submodulo${submodulosFiltrados.length > 1 ? 's' : ''} disponivel${submodulosFiltrados.length > 1 ? 'eis' : ''}.`;
                atualizarBotaoConfirmar();
            }

            function fechar(resultado) {
                doc.removeEventListener('keydown', aoPressionarTecla, true);
                fundo.remove();
                if (elementoAtivo?.focus) {
                    elementoAtivo.focus();
                }
                resolve(resultado);
            }

            function confirmar() {
                const selecionado = obterSelecionado();
                if (selecionado) {
                    fechar(selecionado);
                }
            }

            function aoPressionarTecla(evento) {
                if (evento.key === 'Escape') {
                    evento.preventDefault();
                    fechar(null);
                    return;
                }

                if (evento.key === 'Enter' && doc.activeElement !== selectSubmodulos) {
                    const selecionado = obterSelecionado();
                    if (selecionado) {
                        evento.preventDefault();
                        confirmar();
                    }
                }
            }

            inputBusca.value = String(termoInicial || '').trim();
            inputBusca.addEventListener('input', () => renderizarOpcoes(inputBusca.value));
            selectSubmodulos.addEventListener('change', atualizarBotaoConfirmar);
            selectSubmodulos.addEventListener('dblclick', confirmar);
            botaoConfirmar.addEventListener('click', confirmar);
            botoesCancelar.forEach(botao => botao.addEventListener('click', () => fechar(null)));
            fundo.addEventListener('click', evento => {
                if (evento.target === fundo) {
                    fechar(null);
                }
            });

            doc.addEventListener('keydown', aoPressionarTecla, true);
            doc.body.appendChild(fundo);
            renderizarOpcoes(inputBusca.value);
            window.requestAnimationFrame(() => inputBusca.focus());
        });
    }

    class LuftMarkdownEditor {
        constructor(configuracao) {
            this.textarea = resolverElemento(configuracao.textarea);
            this.previewElement = resolverElemento(configuracao.previewElement);
            this.statusElement = resolverElemento(configuracao.statusElement);
            this.previewEndpoint = configuracao.previewEndpoint;
            this.token = configuracao.token || '';
            this.previewDelay = Number(configuracao.previewDelay) || 250;
            this.placeholder = configuracao.placeholder || '';
            this.minHeight = configuracao.minHeight || '700px';
            this.lineLimit = Number(configuracao.lineLimit) || 100;
            this.minVisibleLines = Number(configuracao.minVisibleLines) || 12;
            this.emptyStateHtml = configuracao.emptyStateHtml || '<p class="luft-markdown-placeholder">Comece a editar para ver o preview final.</p>';
            this.renderTimer = null;
            this.abortController = null;
            this.lastRenderedMarkdown = null;
            this.scrollSyncEnabled = false;
            this.handleEditorScroll = null;
            this.handlePreviewWheel = null;
            this.heightUpdateFrame = null;

            if (!this.textarea) {
                throw new Error('Elemento textarea nao encontrado para o editor markdown.');
            }

            if (!global.EasyMDE) {
                throw new Error('EasyMDE nao foi carregado.');
            }

            this.textarea.value = configuracao.initialValue || '';
            this.editor = new global.EasyMDE({
                element: this.textarea,
                initialValue: configuracao.initialValue || '',
                autofocus: false,
                autoDownloadFontAwesome: false,
                forceSync: true,
                indentWithTabs: false,
                lineNumbers: true,
                lineWrapping: true,
                minHeight: this.minHeight,
                placeholder: this.placeholder,
                spellChecker: false,
                status: false,
                toolbar: false,
            });
            this.editorContainer = this.editor.codemirror.getWrapperElement().closest('.EasyMDEContainer');
            this.editorPane = this.editor.codemirror.getWrapperElement().closest('.luft-markdown-pane');
            this.previewPane = this.previewElement?.closest('.luft-markdown-pane') || null;

            this.editor.codemirror.on('change', () => {
                this.atualizarAlturaSuperficies();
                this.agendarPreview();
            });

            this.vincularScrollSincronizado();

            if (this.previewElement) {
                this.previewElement.innerHTML = this.emptyStateHtml;
            }

            this.atualizarStatus('Preview final');
            this.atualizarAlturaSuperficies();
            this.agendarPreview(0);
        }

        getValue() {
            return this.editor.value();
        }

        setValue(valor) {
            this.editor.value(valor || '');
            this.lastRenderedMarkdown = null;
            this.atualizarAlturaSuperficies();
            this.agendarPreview(0);
        }

        focus() {
            this.editor.codemirror.focus();
        }

        refresh() {
            this.editor.codemirror.refresh();
            this.atualizarAlturaSuperficies();
        }

        getSelectedText() {
            return this.editor.codemirror.getSelection();
        }

        insertText(texto) {
            this.editor.codemirror.replaceSelection(texto);
            this.focus();
        }

        wrapSelection(prefixo, sufixo, textoPadrao) {
            const cm = this.editor.codemirror;
            const doc = cm.getDoc();
            const selecao = doc.getSelection();
            const conteudo = selecao || textoPadrao || '';
            doc.replaceSelection(`${prefixo}${conteudo}${sufixo}`);
            this.focus();
        }

        prefixarLinhas(prefixo, textoPadrao) {
            const cm = this.editor.codemirror;
            const doc = cm.getDoc();
            const selecao = doc.getSelection() || textoPadrao || '';
            const linhas = selecao.split('\n');
            const conteudo = linhas.map((linha, indice) => {
                const valorPrefixo = typeof prefixo === 'function' ? prefixo(indice) : prefixo;
                return `${valorPrefixo}${linha}`;
            }).join('\n');
            doc.replaceSelection(conteudo);
            this.focus();
        }

        toggleHeading() {
            this.prefixarLinhas('## ', 'Titulo');
        }

        toggleBold() {
            this.wrapSelection('**', '**', 'texto em destaque');
        }

        toggleItalic() {
            this.wrapSelection('*', '*', 'texto em italico');
        }

        toggleQuote() {
            this.prefixarLinhas('> ', 'Cite um trecho importante');
        }

        toggleBulletList() {
            this.prefixarLinhas('- ', 'Novo item');
        }

        toggleOrderedList() {
            this.prefixarLinhas(indice => `${indice + 1}. `, 'Novo item');
        }

        toggleCodeBlock() {
            const selecao = this.getSelectedText();
            const conteudo = selecao || 'seu_codigo_aqui';
            this.insertText(`\n\`\`\`\n${conteudo}\n\`\`\`\n`);
        }

        insertLink() {
            const textoSelecionado = this.getSelectedText() || prompt('Texto do link:');
            if (!textoSelecionado) {
                return;
            }

            const url = prompt('URL do link:');
            if (!url) {
                return;
            }

            this.insertText(`[${textoSelecionado}](${url})`);
        }

        insertTable() {
            this.insertText('\n| Coluna | Valor |\n| --- | --- |\n| Texto | Texto |\n');
        }

        async insertSubmoduleCitation(configuracao = {}) {
            try {
                const submodulos = await carregarSubmodulos(
                    configuracao.listEndpoint,
                    configuracao.token || this.token
                );

                if (!submodulos.length) {
                    global.alert('Nenhum submodulo global disponivel para citacao.');
                    return;
                }

                const selecionado = await abrirSeletorSubmodulo({
                    submodulos,
                    termoInicial: this.getSelectedText(),
                });

                if (selecionado?.name) {
                    this.insertText(`[[${selecionado.name}]]`);
                }
            } catch (erro) {
                global.alert(erro?.message || 'Falha ao carregar a lista de submodulos.');
            }
        }

        destroy() {
            if (this.renderTimer) {
                window.clearTimeout(this.renderTimer);
                this.renderTimer = null;
            }

            if (this.abortController) {
                this.abortController.abort();
                this.abortController = null;
            }

            if (this.heightUpdateFrame) {
                window.cancelAnimationFrame(this.heightUpdateFrame);
                this.heightUpdateFrame = null;
            }

            if (this.handleEditorScroll) {
                this.editor.codemirror.off('scroll', this.handleEditorScroll);
                this.handleEditorScroll = null;
            }

            if (this.handlePreviewWheel && this.previewElement) {
                this.previewElement.removeEventListener('wheel', this.handlePreviewWheel);
                this.handlePreviewWheel = null;
            }

            if (this.editor) {
                this.editor.toTextArea();
            }
        }

        atualizarStatus(texto, carregando, erro) {
            if (!this.statusElement) {
                return;
            }

            this.statusElement.textContent = texto;
            this.statusElement.classList.toggle('is-loading', Boolean(carregando));
            this.statusElement.classList.toggle('is-error', Boolean(erro));
        }

        agendarPreview(delay) {
            if (!this.previewElement || !this.previewEndpoint || !global.LuftDocs?.requestJson) {
                return;
            }

            if (this.renderTimer) {
                window.clearTimeout(this.renderTimer);
            }

            this.renderTimer = window.setTimeout(() => {
                this.atualizarPreview();
            }, typeof delay === 'number' ? delay : this.previewDelay);
        }

        async atualizarPreview() {
            const markdown = this.getValue();

            if (markdown === this.lastRenderedMarkdown) {
                return;
            }

            if (!markdown.trim()) {
                this.lastRenderedMarkdown = markdown;
                this.previewElement.innerHTML = this.emptyStateHtml;
                this.atualizarStatus('Preview final');
                return;
            }

            if (this.abortController) {
                this.abortController.abort();
            }

            const controller = new AbortController();
            this.abortController = controller;
            this.atualizarStatus('Sincronizando preview...', true, false);

            try {
                const { response, data } = await global.LuftDocs.requestJson(this.previewEndpoint, {
                    method: 'POST',
                    json: { markdown },
                    signal: controller.signal,
                    token: this.token,
                });

                if (!response.ok) {
                    throw new Error(data?.error || 'Falha ao renderizar o preview.');
                }

                this.previewElement.innerHTML = data?.html || this.emptyStateHtml;
                this.lastRenderedMarkdown = markdown;
                this.atualizarAlturaSuperficies(() => {
                    this.sincronizarEditorParaPreview();
                });
                this.atualizarStatus('Preview final');
            } catch (erro) {
                if (erro?.name === 'AbortError') {
                    return;
                }

                this.previewElement.innerHTML = '<p class="luft-markdown-placeholder is-error">Nao foi possivel atualizar o preview final.</p>';
                this.atualizarStatus('Falha ao atualizar preview', false, true);
            } finally {
                if (this.abortController === controller) {
                    this.abortController = null;
                }
            }
        }

        vincularScrollSincronizado() {
            const cm = this.editor?.codemirror;
            const scroller = cm?.getScrollerElement?.();
            if (!cm || !this.previewElement || !scroller) {
                return;
            }

            this.handleEditorScroll = () => {
                if (!this.scrollSyncEnabled) {
                    return;
                }

                this.sincronizarEditorParaPreview();
            };

            this.handlePreviewWheel = evento => {
                if (!this.scrollSyncEnabled) {
                    return;
                }

                const deltaVertical = this.normalizarDeltaWheel(
                    evento.deltaY,
                    evento.deltaMode,
                    scroller.clientHeight,
                    cm.defaultTextHeight()
                );

                if (!deltaVertical) {
                    return;
                }

                const info = cm.getScrollInfo();
                const maxScroll = Math.max(0, info.height - info.clientHeight);
                if (maxScroll <= 0) {
                    return;
                }

                const proximoTop = Math.min(maxScroll, Math.max(0, info.top + deltaVertical));
                if (proximoTop === info.top) {
                    return;
                }

                evento.preventDefault();
                cm.scrollTo(info.left, proximoTop);
            };

            cm.on('scroll', this.handleEditorScroll);
            this.previewElement.addEventListener('wheel', this.handlePreviewWheel, { passive: false });
        }

        normalizarDeltaWheel(delta, deltaMode, viewportHeight, lineHeight) {
            if (!delta) {
                return 0;
            }

            if (deltaMode === 1) {
                return delta * (lineHeight || 16);
            }

            if (deltaMode === 2) {
                return delta * (viewportHeight || 0);
            }

            return delta;
        }

        obterRazaoScrollEditor() {
            const info = this.editor.codemirror.getScrollInfo();
            const maxScroll = Math.max(0, info.height - info.clientHeight);
            if (maxScroll <= 0) {
                return 0;
            }

            return info.top / maxScroll;
        }

        obterRazaoScrollPreview() {
            if (!this.previewElement) {
                return 0;
            }

            const maxScroll = Math.max(0, this.previewElement.scrollHeight - this.previewElement.clientHeight);
            if (maxScroll <= 0) {
                return 0;
            }

            return this.previewElement.scrollTop / maxScroll;
        }

        sincronizarEditorParaPreview() {
            if (!this.previewElement || !this.scrollSyncEnabled) {
                return;
            }

            const maxScroll = Math.max(0, this.previewElement.scrollHeight - this.previewElement.clientHeight);
            this.previewElement.scrollTop = maxScroll * this.obterRazaoScrollEditor();
        }

        sincronizarPreviewParaEditor() {
            const cm = this.editor?.codemirror;
            if (!cm || !this.scrollSyncEnabled) {
                return;
            }

            const info = cm.getScrollInfo();
            const maxScroll = Math.max(0, info.height - info.clientHeight);
            cm.scrollTo(null, maxScroll * this.obterRazaoScrollPreview());
        }

        atualizarAlturaSuperficies(aposAtualizacao) {
            const cm = this.editor?.codemirror;
            if (!cm) {
                return;
            }

            if (this.heightUpdateFrame) {
                window.cancelAnimationFrame(this.heightUpdateFrame);
            }

            this.heightUpdateFrame = window.requestAnimationFrame(() => {
                const lineHeight = cm.defaultTextHeight() || 22;
                const minHeight = Math.round(this.minVisibleLines * lineHeight + 24);
                const maxHeight = Math.round(this.lineLimit * lineHeight + 24);
                const info = cm.getScrollInfo();
                const editorContentHeight = Math.ceil(info.height || minHeight);
                const previewContentHeight = this.previewElement
                    ? Math.ceil(this.previewElement.scrollHeight || 0)
                    : 0;
                const naturalHeight = Math.max(minHeight, editorContentHeight, previewContentHeight);
                const targetHeight = Math.min(maxHeight, naturalHeight);
                const hasInternalScroll = naturalHeight > maxHeight;
                const scroller = cm.getScrollerElement();
                const editorHeaderHeight = this.editorPane?.querySelector('.luft-markdown-pane-header')?.offsetHeight || 0;
                const previewHeaderHeight = this.previewPane?.querySelector('.luft-markdown-pane-header')?.offsetHeight || 0;
                const sharedPaneHeight = Math.max(targetHeight + editorHeaderHeight, targetHeight + previewHeaderHeight);

                cm.setSize(null, targetHeight);
                scroller.style.overflowY = hasInternalScroll ? 'auto' : 'hidden';

                if (this.editorContainer) {
                    this.editorContainer.style.height = `${targetHeight}px`;
                    this.editorContainer.style.minHeight = `${targetHeight}px`;
                    this.editorContainer.style.maxHeight = `${targetHeight}px`;
                    this.editorContainer.style.overflow = 'hidden';
                }

                if (this.editorPane) {
                    this.editorPane.style.height = `${sharedPaneHeight}px`;
                    this.editorPane.style.minHeight = `${sharedPaneHeight}px`;
                    this.editorPane.style.maxHeight = `${sharedPaneHeight}px`;
                }

                if (this.previewElement) {
                    this.previewElement.style.height = `${targetHeight}px`;
                    this.previewElement.style.minHeight = `${targetHeight}px`;
                    this.previewElement.style.maxHeight = `${targetHeight}px`;
                    this.previewElement.style.overflowY = hasInternalScroll ? 'auto' : 'hidden';
                }

                if (this.previewPane) {
                    this.previewPane.style.height = `${sharedPaneHeight}px`;
                    this.previewPane.style.minHeight = `${sharedPaneHeight}px`;
                    this.previewPane.style.maxHeight = `${sharedPaneHeight}px`;
                }

                this.scrollSyncEnabled = hasInternalScroll;

                if (!hasInternalScroll) {
                    cm.scrollTo(null, 0);
                    if (this.previewElement) {
                        this.previewElement.scrollTop = 0;
                    }
                }

                if (typeof aposAtualizacao === 'function') {
                    aposAtualizacao();
                }

                this.heightUpdateFrame = null;
            });
        }
    }

    function criarBotaoToolbar(item) {
        const botao = document.createElement('button');
        botao.type = 'button';
        botao.className = item.className || 'luft-btn luft-btn-outline luft-btn-sm luft-editor-tool';
        botao.title = item.title || item.label || '';
        botao.innerHTML = `
            ${item.icon ? `<i class="${item.icon}"></i>` : ''}
            ${item.label ? `<span class="luft-editor-tool-label">${item.label}</span>` : ''}
        `;

        botao.addEventListener('click', evento => {
            evento.preventDefault();
            item.onClick?.(evento);
        });

        return botao;
    }

    function montarToolbar(referencia, itens) {
        const container = resolverElemento(referencia);
        if (!container) {
            return null;
        }

        container.innerHTML = '';
        let grupo = document.createElement('div');
        grupo.className = 'luft-editor-toolbar-group';

        (itens || []).forEach(item => {
            if (item?.type === 'separator') {
                if (grupo.childElementCount > 0) {
                    container.appendChild(grupo);
                }

                grupo = document.createElement('div');
                grupo.className = 'luft-editor-toolbar-group';
                return;
            }

            grupo.appendChild(criarBotaoToolbar(item));
        });

        if (grupo.childElementCount > 0) {
            container.appendChild(grupo);
        }

        return container;
    }

    global.LuftMarkdownEditor = {
        create(configuracao) {
            return new LuftMarkdownEditor(configuracao);
        },
        mountToolbar: montarToolbar,
    };
})(window);
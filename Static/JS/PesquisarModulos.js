/**
 * Arquivo: PesquisarModulos.js
 * Descricao: Gerencia a logica de busca, autocompletar e carregamento de 
 * recomendacoes hibridas na interface de pesquisa do LuftDocs.
 */

class GerenciadorBusca {
    /**
     * Inicializa os componentes de busca e configura o estado inicial.
     */
    constructor() {
        this.containerPrincipal = document.querySelector('.luft-search-page-container');
        if (!this.containerPrincipal) return;

        this.token = this.containerPrincipal.dataset.token || '';
        this.prefixoBase = (this.containerPrincipal.dataset.basePrefix || '/luft-docs').replace(/\/+$/, '');
        this.rotas = window.ROUTES || {};
        this.rotasApi = this.rotas.Api || {};
        this.rotaBusca = this.rotas.Busca?.exibir || '';

        this.elementos = {
            inputBusca: document.getElementById('inputBuscaPrincipal'),
            resultadosAutocomplete: document.getElementById('resultadosAutocomplete'),
            formulario: document.getElementById('formularioBusca'),
            containerRecomendacoes: document.getElementById('containerRecomendacoes')
        };

        this.estado = {
            recomendacoes: [],
            buscasPopulares: [],
            paginaAtual: 1,
            itensPorPagina: 5
        };

        this.inicializar();
    }

    /**
     * Executa as rotinas de inicializacao de eventos e carga de dados.
     */
    inicializar() {
        this.configurarAutocomplete();
        
        if (this.elementos.containerRecomendacoes) {
            this.carregarDadosRecomendacao();
        }
    }

    /**
     * Adiciona o prefixo global da aplicacao e o token de seguranca as URLs.
     * @param {string} caminho - O path relativo da API.
     * @returns {string} URL formatada.
     */
    formatarUrl(caminho) {
        if (!caminho) {
            return '';
        }

        if (/^https?:\/\//i.test(caminho)) {
            return caminho;
        }

        if (caminho.startsWith(this.prefixoBase)) {
            let urlFinal = caminho;
            if (this.token && !urlFinal.includes('token=')) {
                const separador = urlFinal.includes('?') ? '&' : '?';
                urlFinal += `${separador}token=${encodeURIComponent(this.token)}`;
            }
            return urlFinal;
        }

        const pathSaneado = caminho.startsWith('/') ? caminho : `/${caminho}`;
        let urlFinal = `${this.prefixoBase}${pathSaneado}`;
        
        if (this.token) {
            const separador = urlFinal.includes('?') ? '&' : '?';
            urlFinal += `${separador}token=${encodeURIComponent(this.token)}`;
        }
        return urlFinal;
    }

    /**
     * Configura o comportamento de sugestoes em tempo real conforme digitacao.
     */
    configurarAutocomplete() {
        let timerDebounce;

        this.elementos.inputBusca.addEventListener('input', (evento) => {
            const termo = evento.target.value;
            clearTimeout(timerDebounce);

            if (termo.length < 2) {
                this.elementos.resultadosAutocomplete.style.display = 'none';
                return;
            }

            timerDebounce = setTimeout(async () => {
                try {
                    const url = this.formatarUrl(`${this.rotasApi.listarAutocomplete}?q=${encodeURIComponent(termo)}`);
                    const resposta = await fetch(url);
                    const sugestoes = await resposta.json();

                    if (Array.isArray(sugestoes) && sugestoes.length > 0) {
                        this.renderizarAutocomplete(sugestoes);
                    } else {
                        this.elementos.resultadosAutocomplete.style.display = 'none';
                    }
                } catch (erro) {
                    console.error("Erro ao processar autocompletar:", erro);
                }
            }, 250);
        });

        // Fechamento ao clicar fora
        document.addEventListener('click', (evento) => {
            if (!this.elementos.inputBusca.contains(evento.target)) {
                this.elementos.resultadosAutocomplete.style.display = 'none';
            }
        });
    }

    /**
     * Renderiza o dropdown de sugestoes.
     * @param {Array} sugestoes - Lista de strings sugeridas.
     */
    renderizarAutocomplete(sugestoes) {
        this.elementos.resultadosAutocomplete.innerHTML = sugestoes.map(s => `
            <div class="luft-autocomplete-item" data-valor="${s}">
                <i class="ph ph-magnifying-glass"></i>
                <span>${s}</span>
            </div>
        `).join('');

        this.elementos.resultadosAutocomplete.style.display = 'block';

        this.elementos.resultadosAutocomplete.querySelectorAll('.luft-autocomplete-item').forEach(item => {
            item.addEventListener('click', () => {
                this.elementos.inputBusca.value = item.dataset.valor;
                this.elementos.formulario.submit();
            });
        });
    }

    /**
     * Obtem recomendacoes personalizadas para o usuario logado.
     */
    async carregarDadosRecomendacao() {
        try {
            const url = this.formatarUrl(this.rotasApi.listarRecomendacoes);
            const resposta = await fetch(url);
            
            if (!resposta.ok) throw new Error();

            const dados = await resposta.json();
            this.estado.recomendacoes = dados.hybrid_recommendations || [];
            this.estado.buscasPopulares = (dados.popular_searches || []).slice(0, 10);
            
            this.renderizarPainelInicial();
        } catch (erro) {
            this.elementos.containerRecomendacoes.innerHTML = `
                <div class="luft-alert luft-alert-danger">
                    Não foi possível carregar as recomendações no momento.
                </div>`;
        }
    }

    /**
     * Constroi a interface inicial com recomendacoes e buscas populares.
     */
    renderizarPainelInicial() {
        if (this.estado.recomendacoes.length === 0 && this.estado.buscasPopulares.length === 0) {
            this.elementos.containerRecomendacoes.innerHTML = `
                <div class="text-center py-5">
                    <p class="text-muted">Nenhuma recomendação disponível. Comece a explorar o sistema para gerarmos sugestões.</p>
                </div>`;
            return;
        }

        let html = '';

        // Secao de Recomendados
        if (this.estado.recomendacoes.length > 0) {
            html += `<h4 class="text-muted text-sm font-semibold mb-4 text-uppercase">Recomendado para você</h4>`;
            html += `<div class="luft-results-grid mb-5">`;
            
            const inicio = (this.estado.paginaAtual - 1) * this.estado.itensPorPagina;
            const fim = inicio + this.estado.itensPorPagina;
            const itensPagina = this.estado.recomendacoes.slice(inicio, fim);

            itensPagina.forEach((item, i) => {
                html += this.construirHtmlCard(item, i * 50);
            });
            html += `</div>`;
            html += this.construirPaginacao();
        }

        // Secao de Populares
        if (this.estado.buscasPopulares.length > 0) {
            html += `
                <div class="luft-popular-section mt-5">
                    <h5 class="text-main font-bold mb-3 d-flex align-items-center gap-2">
                        <i class="ph-bold ph-chart-line-up text-success"></i>
                        Buscas Populares
                    </h5>
                    <div class="luft-tag-cloud">
                        ${this.estado.buscasPopulares.map(b => {
                            const urlBusca = this.formatarUrl(`${this.rotaBusca}?q=${encodeURIComponent(b.query_term)}`);
                            return `<a href="${urlBusca}" class="luft-tag"><i class="ph ph-magnifying-glass me-1"></i>${b.query_term}</a>`;
                        }).join('')}
                    </div>
                </div>`;
        }

        this.elementos.containerRecomendacoes.innerHTML = html;
        this.vincularEventosPaginacao();
    }

    /**
     * Constroi o HTML de um card de resultado.
     * @param {Object} dado - Objeto do resultado.
     * @param {number} delay - Tempo de atraso para animacao.
     * @returns {string} HTML gerado.
     */
    construirHtmlCard(dado, delay) {
        let mediaHtml = '';
        if (dado.preview && dado.preview.path) {
            const src = dado.preview.path;
            mediaHtml = `<div class="luft-result-media">
                ${dado.preview.type === 'image' ? `<img src="${src}">` : `<video src="${src}" muted autoplay loop></video>`}
            </div>`;
        }

        const iconeNo = (dado.module_icon || 'ph-bold ph-file-text').replace('fas fa-', 'ph-bold ph-').replace('bi bi-', 'ph-bold ph-');

        return `
            <a href="${this.prefixoBase}${dado.url}" class="luft-result-card-link">
                <div class="luft-result-card" style="animation-delay: ${delay}ms">
                    ${mediaHtml}
                    <div class="luft-result-body">
                        <div class="luft-result-meta">
                            <i class="${iconeNo} text-primary"></i>
                            <span class="font-bold">${dado.module_nome}</span>
                            <span class="luft-badge">${dado.doc_type}</span>
                        </div>
                        <div class="luft-result-snippet">${dado.snippet || ''}</div>
                    </div>
                </div>
            </a>`;
    }

    construirPaginacao() {
        const total = Math.ceil(this.estado.recomendacoes.length / this.estado.itensPorPagina);
        if (total <= 1) return '';

        let html = `<nav class="d-flex justify-content-center mt-4"><ul class="luft-pagination">`;
        html += `<li class="${this.estado.paginaAtual === 1 ? 'disabled' : ''}"><a href="#" data-pg="${this.estado.paginaAtual - 1}">Anterior</a></li>`;
        
        for (let i = 1; i <= total; i++) {
            html += `<li class="${this.estado.paginaAtual === i ? 'active' : ''}"><a href="#" data-pg="${i}">${i}</a></li>`;
        }

        html += `<li class="${this.estado.paginaAtual === total ? 'disabled' : ''}"><a href="#" data-pg="${this.estado.paginaAtual + 1}">Próxima</a></li>`;
        return html + `</ul></nav>`;
    }

    vincularEventosPaginacao() {
        const links = this.elementos.containerRecomendacoes.querySelectorAll('.luft-pagination a');
        links.forEach(link => {
            link.addEventListener('click', (e) => {
                e.preventDefault();
                const novaPg = parseInt(e.target.dataset.pg);
                if (novaPg > 0 && novaPg !== this.estado.paginaAtual) {
                    this.estado.paginaAtual = novaPg;
                    this.renderizarPainelInicial();
                    window.scrollTo({ top: 0, behavior: 'smooth' });
                }
            });
        });
    }
}

document.addEventListener('DOMContentLoaded', () => {
    new GerenciadorBusca();
});
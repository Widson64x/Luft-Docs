/**
 * Arquivo: GerenciadorMapaModulos.js
 * Descricao: Responsavel pela renderizacao, interatividade e fisica do Grafo 
 * de Conhecimento (Mapa de Modulos) utilizando a biblioteca D3.js.
 */

class GerenciadorMapaModulos {
    /**
     * Inicializa a classe e prepara os dados brutos e configuracoes visuais.
     */
    constructor() {
        this.raioNo = 40;
        this.duracaoTransicao = 700;
        
        this.containerGrafo = document.getElementById('containerGrafoD3');
        this.inputFiltro = document.getElementById('inputFiltroMapa');
        this.mensagemSemResultados = document.getElementById('mensagemSemResultadosMapa');
        
        if (!this.containerGrafo) return;

        this.largura = this.containerGrafo.clientWidth;
        this.altura = this.containerGrafo.clientHeight;

        this.parametrosUrl = new URLSearchParams(window.location.search);
        this.tokenUsuario = this.parametrosUrl.get('token');

        this.carregarDadosIniciais();
        if (this.dadosBrutos.length === 0) return;

        this.prepararDadosGrafo();
        this.aplicarFundoEstrelado();
        this.renderizarGrafo();
        this.inicializarInteratividade();
    }

    /**
     * Extrai os dados JSON injetados no HTML pelo servidor Flask.
     */
    carregarDadosIniciais() {
        try {
            const scriptModulos = document.getElementById('dados-modulos').textContent;
            this.dadosBrutos = JSON.parse(scriptModulos);
            
            const scriptPermissoes = document.getElementById('dados-permissoes').textContent;
            const permissoes = JSON.parse(scriptPermissoes);
            this.podeAcessarTecnico = permissoes.can_view_tecnico;

            this.nosVisitados = JSON.parse(localStorage.getItem('visitedNodes')) || [];
        } catch (erro) {
            console.error("Falha ao analisar dados iniciais do mapa:", erro);
            this.dadosBrutos = [];
        }
    }

    /**
     * Constroi as relacoes (edges/links) entre os modulos baseando-se nos arrays de visibilidade.
     */
    prepararDadosGrafo() {
        this.nos = this.dadosBrutos.map(modulo => ({ ...modulo }));
        this.conexoes = [];
        this.mapaRelacoes = new Map();
        
        this.nos.forEach(no => this.mapaRelacoes.set(no.id, []));
        
        this.dadosBrutos.forEach(modulo => {
            if (modulo.relacionados_visiveis) {
                modulo.relacionados_visiveis.forEach(idRelacionado => {
                    const noDestino = this.nos.find(n => n.id === idRelacionado);
                    if (noDestino) {
                        this.conexoes.push({ source: modulo.id, target: idRelacionado });
                        this.mapaRelacoes.get(modulo.id).push(noDestino);
                        this.mapaRelacoes.get(idRelacionado).push(this.nos.find(n => n.id === modulo.id));
                    }
                });
            }
        });
    }

    /**
     * Gera particulas estaticas manipulando variaveis CSS do container para criar
     * profundidade espacial visual no fundo.
     */
    aplicarFundoEstrelado() {
        const gerarEstrelas = (quantidade, cor) => {
            let valor = `${Math.random() * this.largura}px ${Math.random() * this.altura}px ${cor}`;
            for (let i = 2; i <= quantidade; i++) {
                valor += `, ${Math.random() * this.largura}px ${Math.random() * this.altura}px ${cor}`;
            }
            return valor;
        };

        const wrapper = document.getElementById('wrapperCanvasMapa');
        if (wrapper) {
            // Compatibilidade dinâmica com temas
            const corPoeira = 'color-mix(in srgb, var(--luft-text-muted) 30%, transparent)';
            wrapper.style.setProperty('--stars-small', gerarEstrelas(100, corPoeira));
            wrapper.style.setProperty('--stars-medium', gerarEstrelas(40, 'var(--luft-primary-400)'));
        }
    }

    /**
     * Inicia a simulacao fisica e desenha os elementos SVG no DOM.
     */
    renderizarGrafo() {
        this.simulacaoForca = d3.forceSimulation(this.nos)
            .force("link", d3.forceLink(this.conexoes).id(d => d.id).distance(100).strength(0.5))
            .force("charge", d3.forceManyBody().strength(-180))
            .force("center", d3.forceCenter(this.largura / 2, this.altura / 2).strength(0.15))
            .force("collide", d3.forceCollide().radius(50));

        this.svg = d3.create("svg")
            .attr("viewBox", [0, 0, this.largura, this.altura])
            .attr("width", "100%")
            .attr("height", "100%")
            .style("position", "relative")
            .style("z-index", "1");

        this.grupoPrincipal = this.svg.append("g");
        this.grupoConexoes = this.grupoPrincipal.append("g").attr("class", "links");
        this.grupoNos = this.grupoPrincipal.append("g").attr("class", "nodes");
        
        this.tooltip = d3.select("body").append("div").attr("class", "luft-mapa-tooltip");

        this.elementosConexao = this.grupoConexoes.selectAll("line")
            .data(this.conexoes)
            .join("line")
            .attr("class", "link");
        
        this.elementosNo = this.grupoNos.selectAll("g")
            .data(this.nos, d => d.id)
            .join("g")
            .attr("class", "node")
            .classed("visited", d => this.nosVisitados.includes(d.id));
        
        this.elementosNo.append("circle")
            .attr("class", "node-background")
            .attr("r", 0)
            .transition()
            .duration(1000)
            .ease(d3.easeElasticOut.amplitude(0.8).period(0.5))
            .attr("r", this.raioNo);
            
        this.elementosNo.append("foreignObject")
            .attr('width', this.raioNo * 2)
            .attr('height', this.raioNo * 2)
            .attr('x', -this.raioNo)
            .attr('y', -this.raioNo)
            // Substituicao automatica de icones legados Bootstrap por Phosphor
            .html(d => {
                const iconeOriginal = d.icone || 'bi-box';
                const iconeFormatado = iconeOriginal.replace('bi bi-', 'ph-bold ph-');
                return `<div class="foreign-icon-wrapper"><i class="${iconeFormatado}"></i></div>`;
            });
            
        this.elementosNo.append("text")
            .attr("class", "node-label")
            .text(d => d.nome)
            .attr("y", this.raioNo + 24);

        this.containerGrafo.appendChild(this.svg.node());
    }

    /**
     * Aplica manipuladores de eventos para arrastar nos, dar zoom e usar filtros.
     */
    inicializarInteratividade() {
        // --- Comportamento de Arraste (Drag) ---
        const eventoArraste = d3.drag()
            .on("start", (evento, d) => { 
                if (!evento.active) this.simulacaoForca.alphaTarget(0.3).restart(); 
                d.fx = d.x; d.fy = d.y; 
                this.containerGrafo.style.cursor = 'grabbing'; 
                this.tooltip.classed("visible", false); 
            })
            .on("drag", (evento, d) => { 
                d.fx = evento.x; d.fy = evento.y; 
            })
            .on("end", (evento, d) => { 
                if (!evento.active) this.simulacaoForca.alphaTarget(0); 
                d.fx = null; d.fy = null; 
                this.containerGrafo.style.cursor = 'grab'; 
            });
            
        this.elementosNo.call(eventoArraste);

        // --- Eventos de Mouse nos Nós ---
        this.elementosNo.on("click", (evento, d) => {
            evento.stopPropagation();
            this.tooltip.classed("visible", false);
            this.exibirMenuContexto(evento, d);
        });
        
        this.elementosNo.on('mouseover', (evento, d) => {
            if (d.descricao && d.descricao.trim() !== '') {
                this.tooltip.html(d.descricao)
                    .style("left", (evento.pageX + 15) + "px")
                    .style("top", (evento.pageY + 15) + "px")
                    .classed("visible", true);
            }
            
            if (this.inputFiltro.value.trim() !== '') return;
            
            this.elementosNo.classed('faded', n => n.id !== d.id);
            d3.select(evento.currentTarget).classed('faded', false).classed('hovered', true);
            
            const idsConectados = new Set(this.mapaRelacoes.get(d.id).map(n => n.id));
            this.elementosNo.filter(n => idsConectados.has(n.id)).classed('faded', false).classed('related', true);
            
            this.elementosConexao
                .classed('faded', l => l.source.id !== d.id && l.target.id !== d.id)
                .classed('active', l => l.source.id === d.id || l.target.id === d.id);
        });

        this.elementosNo.on('mouseout', () => {
            this.tooltip.classed("visible", false);
            if (this.inputFiltro.value.trim() === '') {
                this.elementosNo.classed("faded", false).classed("hovered", false).classed("related", false);
                this.elementosConexao.classed("faded", false).classed("active", false);
            }
        });
        
        d3.select('body').on('mousemove', (evento) => {
            this.tooltip.style('left', (evento.pageX + 15) + 'px').style('top', (evento.pageY + 15) + 'px');
        });
        
        // --- Comportamento de Zoom ---
        this.controleZoom = d3.zoom()
            .scaleExtent([0.2, 4])
            .on("zoom", (evento) => this.grupoPrincipal.attr("transform", evento.transform));
            
        this.svg.call(this.controleZoom).on("dblclick.zoom", null);
        this.svg.on('click', () => d3.select('.luft-mapa-context-menu').remove());

        // --- Filtro Dinamico de Pesquisa ---
        if (this.inputFiltro) {
            this.inputFiltro.addEventListener('input', () => this.processarFiltro());
        }
        
        // --- Atualizacao Fisica a cada Frame (Tick) ---
        this.simulacaoForca.on("tick", () => {
            this.elementosConexao
                .attr("x1", d => d.source.x).attr("y1", d => d.source.y)
                .attr("x2", d => d.target.x).attr("y2", d => d.target.y);
            this.elementosNo.attr("transform", d => `translate(${d.x},${d.y})`);
        });

        // Efeito basico de pseudo-3d ao mover o mouse fora do canvas
        const wrapper = document.getElementById('wrapperCanvasMapa');
        if (wrapper) {
            wrapper.addEventListener('mousemove', (evento) => {
                if (d3.select('.luft-mapa-context-menu').node()) return;
                const retangulo = wrapper.getBoundingClientRect();
                const x = evento.clientX - retangulo.left - retangulo.width / 2;
                const y = evento.clientY - retangulo.top - retangulo.height / 2;
                wrapper.style.transform = `rotateX(${-y / (retangulo.height / 2) * 3}deg) rotateY(${x / (retangulo.width / 2) * 3}deg) scale(1.01)`;
            });
            wrapper.addEventListener('mouseleave', () => {
                wrapper.style.transform = 'rotateX(0deg) rotateY(0deg) scale(1)';
            });
        }
    }

    /**
     * Constroi o menu suspenso ao clicar em um no.
     */
    exibirMenuContexto(evento, dadosNo) {
        d3.select('.luft-mapa-context-menu').remove();
        
        const menuD3 = d3.select('body').append('div')
            .attr('class', 'luft-mapa-context-menu')
            .style('left', `${evento.pageX + 10}px`)
            .style('top', `${evento.pageY}px`);
            
        const listaHtml = menuD3.append('ul');
        const prefixoGlobal = window.__BASE_PREFIX__ || "/luft-docs";
        
        const itensMenu = [
            { href: `${prefixoGlobal}/modulo/?modulo=${dadosNo.id}&token=${this.tokenUsuario}`, html: `<i class="ph-bold ph-book-open"></i> Acessar Módulo`, exibir: true },
            { href: `${prefixoGlobal}/modulo/?modulo_tecnico=${dadosNo.id}&token=${this.tokenUsuario}`, html: `<i class="ph-bold ph-wrench"></i> Especificações Técnicas`, exibir: dadosNo.show_tecnico_button }
        ];

        itensMenu.forEach(item => {
            if (item.exibir) {
                const li = listaHtml.append('li');
                li.append('a')
                    .attr('href', item.href)
                    .attr('class', 'luft-mapa-context-action')
                    .html(item.html)
                    .on('click', function(eventoClique) {
                        eventoClique.preventDefault();
                        
                        let visitados = JSON.parse(localStorage.getItem('visitedNodes')) || [];
                        visitados = visitados.filter(id => id !== dadosNo.id);
                        visitados.unshift(dadosNo.id);
                        localStorage.setItem('visitedNodes', JSON.stringify(visitados.slice(0, 5)));

                        const urlDestino = d3.select(this).attr('href');
                        window.location.href = urlDestino;
                    });
            }
        });
    }

    /**
     * Aplica regras de invisibilidade baseado na busca do usuario.
     */
    processarFiltro() {
        const textoBusca = this.inputFiltro.value.toLowerCase().trim();
        this.elementosNo.classed('hovered', false);
        this.elementosConexao.classed('active', false);

        if (!textoBusca) {
            this.elementosNo.classed("faded", false).classed("filtered", false).classed("related", false)
                .classed("visited", d => this.nosVisitados.includes(d.id));
            this.elementosConexao.classed("faded", false);
            this.mensagemSemResultados.style.display = 'none';
            this.containerGrafo.style.display = 'block';
            this.svg.transition().duration(this.duracaoTransicao).call(this.controleZoom.transform, d3.zoomIdentity);
            return;
        }

        const nosCorrespondentes = new Set();
        this.nos.forEach(n => {
            if (n.nome.toLowerCase().includes(textoBusca) || n.descricao.toLowerCase().includes(textoBusca)) {
                nosCorrespondentes.add(n.id);
            }
        });

        const nosRelacionados = new Set();
        if (nosCorrespondentes.size > 0) {
            this.conexoes.forEach(l => {
                if (nosCorrespondentes.has(l.source.id)) nosRelacionados.add(l.target.id);
                if (nosCorrespondentes.has(l.target.id)) nosRelacionados.add(l.source.id);
            });
        }
        
        const nosVisiveis = new Set([...nosCorrespondentes, ...nosRelacionados]);
        this.elementosNo.classed("faded", d => !nosVisiveis.has(d.id));
        this.elementosNo.classed("filtered", d => nosCorrespondentes.has(d.id));
        this.elementosNo.classed("related", d => nosRelacionados.has(d.id) && !nosCorrespondentes.has(d.id));
        this.elementosConexao.classed("faded", d => !(nosVisiveis.has(d.source.id) && nosVisiveis.has(d.target.id)));

        const possuiVisiveis = nosVisiveis.size > 0;
        this.mensagemSemResultados.style.display = possuiVisiveis ? 'none' : 'block';
        this.containerGrafo.style.display = possuiVisiveis ? 'block' : 'none';

        // Auto-Zoom se apenas 1 modulo corresponder a pesquisa
        if (nosCorrespondentes.size === 1) {
            const idAlvo = nosCorrespondentes.values().next().value;
            const noAlvo = this.nos.find(n => n.id === idAlvo);
            if (noAlvo) {
                const novaEscala = 1.8;
                const novoX = this.largura / 2 - novaEscala * noAlvo.x;
                const novoY = this.altura / 2 - novaEscala * noAlvo.y;
                const transformacao = d3.zoomIdentity.translate(novoX, novoY).scale(novaEscala);
                this.svg.transition().duration(this.duracaoTransicao).call(this.controleZoom.transform, transformacao);
            }
        }
    }
}

// Inicializador principal engatilhado ao carregar o DOM
document.addEventListener('DOMContentLoaded', () => {
    new GerenciadorMapaModulos();
});
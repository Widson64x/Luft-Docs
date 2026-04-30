/**
 * Arquivo: GerenciadorRoteiros.js
 * Descricao: Controla a exibicao, criacao e exclusao de roteiros, bem como
 * a reproducao de videos em modais utilizando a API do LuftCore.
 */

class GerenciadorRoteiros {
    /**
     * Inicializa a configuracao dos roteiros carregando os dados do DOM.
     */
    constructor() {
        this.dadosEmbutidos = document.getElementById('roteiros-data');
        if (!this.dadosEmbutidos) return;

        try {
            const configuracao = JSON.parse(this.dadosEmbutidos.textContent);
            this.roteiros = configuracao.roteiros || [];
            this.podeEditar = configuracao.podeEditar || false;
            this.moduloId = document.querySelector('.module-container').dataset.moduleId;
        } catch (erro) {
            this.roteiros = [];
            this.podeEditar = false;
        }

        this.elementos = {
            lista: document.getElementById('roteiros-list'),
            botaoCriar: document.getElementById('btn-criar-roteiro'),
            formulario: document.getElementById('roteiroForm'),
            inputTitulo: document.getElementById('roteiroTitulo'),
            inputTipo: document.getElementById('roteiroTipo'),
            inputConteudo: document.getElementById('roteiroConteudo'),
            inputIcone: document.getElementById('roteiroIcone'),
            inputOrdem: document.getElementById('roteiroOrdem'),
            inputId: document.getElementById('roteiroId'),
            playerVideo: document.getElementById('videoPlayer'),
            nomeRoteiroExclusao: document.getElementById('roteiroNameToDelete'),
            botaoConfirmarExclusao: document.getElementById('btnConfirmDelete')
        };

        this.roteiroParaExcluir = null;
        this.tokenApi = document.querySelector('input[name="token"]')?.value || '';

        this.inicializarInterface();
        this.monitorarFechamentoVideo();
    }

    /**
     * Renderiza a interface e amarra os eventos aos botoes de acao.
     */
    inicializarInterface() {
        this.renderizarLista();

        if (this.podeEditar && this.elementos.botaoCriar) {
            this.elementos.botaoCriar.addEventListener('click', () => this.abrirModalCriacao());
            this.elementos.formulario.addEventListener('submit', (e) => this.salvarRoteiro(e));
            this.elementos.botaoConfirmarExclusao.addEventListener('click', () => this.executarExclusao());
        }
    }

    /**
     * Observa o modal de video para parar a reproducao quando o usuario o fechar.
     */
    monitorarFechamentoVideo() {
        const modalVideo = document.getElementById('videoModal');
        if (!modalVideo) return;

        const observador = new MutationObserver((mutacoes) => {
            mutacoes.forEach((mutacao) => {
                if (mutacao.attributeName === 'class' && !modalVideo.classList.contains('show')) {
                    this.elementos.playerVideo.src = '';
                }
            });
        });

        observador.observe(modalVideo, { attributes: true });
    }

    /**
     * Renderiza a lista de roteiros vinculados ao modulo atual no DOM.
     */
    renderizarLista() {
        this.elementos.lista.innerHTML = '';

        if (this.roteiros.length === 0) {
            this.elementos.lista.innerHTML = '<li class="text-muted text-sm text-center py-3">Nenhum roteiro disponível.</li>';
            return;
        }

        this.roteiros.sort((a, b) => a.ordem - b.ordem).forEach(roteiro => {
            const item = document.createElement('li');
            item.className = 'roteiro-item d-flex justify-content-between align-items-center mb-2 p-2 border rounded';
            
            const iconePadrao = roteiro.tipo === 'modal' ? 'bi-play-circle' : 'bi-box-arrow-up-right';
            const iconeClasse = roteiro.icone || iconePadrao;

            let acaoClique = '';
            if (roteiro.tipo === 'modal') {
                acaoClique = `onclick="window.ReproduzirVideoRoteiro('${roteiro.conteudo}')"`;
            } else {
                acaoClique = `onclick="window.open('${roteiro.conteudo}', '_blank')"`;
            }

            let acoesEdicaoHtml = '';
            if (this.podeEditar) {
                acoesEdicaoHtml = `
                    <div class="roteiro-actions d-flex gap-2">
                        <button class="btn btn-sm btn-light text-primary" onclick="window.EditarRoteiro(${roteiro.id})"><i class="bi bi-pencil"></i></button>
                        <button class="btn btn-sm btn-light text-danger" onclick="window.ConfirmarExclusaoRoteiro(${roteiro.id}, '${roteiro.titulo.replace(/'/g, "\\'")}')"><i class="bi bi-trash"></i></button>
                    </div>
                `;
            }

            item.innerHTML = `
                <div class="roteiro-info d-flex align-items-center gap-2" style="cursor:pointer; color:var(--luft-text-main);" ${acaoClique}>
                    <i class="bi ${iconeClasse} text-primary"></i>
                    <span class="font-semibold text-sm">${roteiro.titulo}</span>
                </div>
                ${acoesEdicaoHtml}
            `;

            this.elementos.lista.appendChild(item);
        });
    }

    /**
     * Limpa o formulario e exibe o modal para criacao de um novo roteiro.
     */
    abrirModalCriacao() {
        this.elementos.formulario.reset();
        this.elementos.inputId.value = '';
        LuftCore.abrirModal('roteiroModal');
    }

    /**
     * Salva o roteiro (criacao ou atualizacao) enviando os dados para a API.
     * @param {Event} evento - O evento de submissao do formulario.
     */
    async salvarRoteiro(evento) {
        evento.preventDefault();
        
        const payload = {
            titulo: this.elementos.inputTitulo.value.trim(),
            tipo: this.elementos.inputTipo.value,
            conteudo: this.elementos.inputConteudo.value.trim(),
            icone: this.elementos.inputIcone.value.trim(),
            ordem: parseInt(this.elementos.inputOrdem.value) || 0
        };

        const isEdicao = !!this.elementos.inputId.value;
        const endpoint = isEdicao 
            ? `/api/roteiros/${this.elementos.inputId.value}?token=${this.tokenApi}`
            : `/api/roteiros?token=${this.tokenApi}`;

        try {
            const resposta = await fetch(endpoint, {
                method: isEdicao ? 'PUT' : 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            const resultado = await resposta.json();

            if (resposta.ok) {
                if (!isEdicao) {
                    await this.vincularRoteiroAoModuloAtual(resultado.roteiro.id);
                    this.roteiros.push(resultado.roteiro);
                } else {
                    const index = this.roteiros.findIndex(r => r.id === parseInt(this.elementos.inputId.value));
                    if (index > -1) this.roteiros[index] = resultado.roteiro;
                }
                this.renderizarLista();
                LuftCore.fecharModal('roteiroModal');
            } else {
                alert(resultado.message || 'Erro ao salvar roteiro.');
            }
        } catch (erro) {
            alert('Falha na comunicação com o servidor.');
        }
    }

    /**
     * Vincula recem criado roteiro ao modulo atual (se for criacao).
     * @param {number} roteiroId - Identificador do roteiro gerado.
     */
    async vincularRoteiroAoModuloAtual(roteiroId) {
        await fetch(`/api/roteiros/vincular?token=${this.tokenApi}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ roteiro_id: roteiroId, modulo_ids: [this.moduloId] })
        });
    }

    /**
     * Preenche os dados no formulario e abre o modal para edicao.
     * @param {number} id - Identificador do roteiro a ser editado.
     */
    editar(id) {
        const roteiro = this.roteiros.find(r => r.id === id);
        if (!roteiro) return;

        this.elementos.inputId.value = roteiro.id;
        this.elementos.inputTitulo.value = roteiro.titulo;
        this.elementos.inputTipo.value = roteiro.tipo;
        this.elementos.inputConteudo.value = roteiro.conteudo;
        this.elementos.inputIcone.value = roteiro.icone || '';
        this.elementos.inputOrdem.value = roteiro.ordem || 0;

        LuftCore.abrirModal('roteiroModal');
    }

    /**
     * Abre o modal de confirmacao de exclusao para o roteiro selecionado.
     * @param {number} id - Identificador do roteiro.
     * @param {string} titulo - Titulo do roteiro para exibicao no alerta.
     */
    confirmarExclusao(id, titulo) {
        this.roteiroParaExcluir = id;
        this.elementos.nomeRoteiroExclusao.textContent = titulo;
        LuftCore.abrirModal('confirmDeleteModal');
    }

    /**
     * Executa a chamada a API para excluir o roteiro e atualiza a interface.
     */
    async executarExclusao() {
        if (!this.roteiroParaExcluir) return;

        try {
            const resposta = await fetch(`/api/roteiros/${this.roteiroParaExcluir}?token=${this.tokenApi}`, {
                method: 'DELETE'
            });

            if (resposta.ok) {
                this.roteiros = this.roteiros.filter(r => r.id !== this.roteiroParaExcluir);
                this.renderizarLista();
            } else {
                const erro = await resposta.json();
                alert(erro.message || 'Erro ao excluir roteiro.');
            }
        } catch (erro) {
            alert('Falha na comunicação com o servidor.');
        } finally {
            this.roteiroParaExcluir = null;
        }
    }
}

document.addEventListener('DOMContentLoaded', () => {
    const gerenciador = new GerenciadorRoteiros();

    // Exporta funcoes isoladas para o escopo global do HTML (Padrao PascalCase)
    window.ReproduzirVideoRoteiro = function(urlVideo) {
        const player = document.getElementById('videoPlayer');
        if (player) {
            player.src = urlVideo;
            LuftCore.abrirModal('videoModal');
        }
    };

    window.EditarRoteiro = function(id) {
        gerenciador.editar(id);
    };

    window.ConfirmarExclusaoRoteiro = function(id, titulo) {
        gerenciador.confirmarExclusao(id, titulo);
    };
});
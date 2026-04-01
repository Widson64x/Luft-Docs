class GerenciadorPermissoes {
    constructor() {
        this.PODE_EDITAR = configPermissoes.podeEditar;
        this.MODO = 'grupo';
        this.ID_ATUAL = null;
        this.DADOS_ATUAIS = null;
    }

    mudarAba(novaAba, event) {
        document.querySelectorAll('.luft-tab-btn').forEach(b => b.classList.remove('ativo'));
        if (event?.currentTarget) {
            event.currentTarget.classList.add('ativo');
        }

        document.getElementById('listaGrupos').classList.toggle('d-none', novaAba !== 'grupo');
        document.getElementById('listaGrupos').classList.toggle('d-block', novaAba === 'grupo');
        document.getElementById('listaUsuarios').classList.toggle('d-none', novaAba !== 'usuario');
        document.getElementById('listaUsuarios').classList.toggle('d-block', novaAba === 'usuario');
        
        document.getElementById('painelPermissoes').classList.remove('d-flex');
        document.getElementById('painelPermissoes').classList.add('d-none');
        document.getElementById('estadoVazio').classList.remove('d-none');
        
        document.getElementById('msgVazio').innerText = (novaAba === 'grupo') ? 'Selecione um grupo ao lado' : 'Selecione um usuário ao lado';
        
        this.MODO = novaAba;
        this.ID_ATUAL = null;
        this.DADOS_ATUAIS = null;
        document.querySelectorAll('.luft-list-item').forEach(i => i.classList.remove('ativo'));
    }

    async carregarGrupo(el, id, nome) {
        if (this.MODO !== 'grupo') return;
        this.ID_ATUAL = id;
        this.ativarItemLista(el);
        this.prepararPainel(nome, 'Editando permissões gerais do grupo');

        try {
            const resp = await fetch(`${configPermissoes.urls.buscarAcessosGrupo}?idGrupo=${id}`, {
                headers: { 'X-Requested-With': 'XMLHttpRequest' }
            });
            if (!resp.ok) {
                throw new Error('Falha ao carregar permissões do grupo.');
            }
            const dados = await resp.json();
            const ativos = new Set(dados.ids_ativos || []);
            
            document.querySelectorAll('.check-perm').forEach(chk => {
                const idPerm = parseInt(chk.dataset.id);
                chk.checked = ativos.has(idPerm);
                chk.disabled = !this.PODE_EDITAR;
                this.configurarVisualUsuario(idPerm, null, null, null); 
            });
        } catch (e) { alert('Erro ao carregar grupo.'); console.error(e); }
    }

    async carregarUsuario(el, id, nome) {
        if (this.MODO !== 'usuario') return;
        this.ID_ATUAL = id;
        this.ativarItemLista(el);
        this.prepararPainel(nome, 'Editando exceções e heranças');

        try {
            const resp = await fetch(`${configPermissoes.urls.buscarAcessosUsuario}?idUsuario=${id}`, {
                headers: { 'X-Requested-With': 'XMLHttpRequest' }
            });
            if (!resp.ok) {
                throw new Error('Falha ao carregar permissões do usuário.');
            }
            this.DADOS_ATUAIS = await resp.json();

            const heranca = new Set(this.DADOS_ATUAIS.ids_heranca || []);
            const overrides = this.DADOS_ATUAIS.overrides || {};

            document.querySelectorAll('.check-perm').forEach(chk => {
                const idPerm = parseInt(chk.dataset.id);
                let isChecked = false;
                let tipoStatus = 'herdado';

                if (Object.prototype.hasOwnProperty.call(overrides, idPerm)) {
                    isChecked = Boolean(overrides[idPerm]);
                    tipoStatus = isChecked ? 'forcado' : 'bloqueado';
                } else {
                    isChecked = heranca.has(idPerm);
                    tipoStatus = 'herdado';
                }

                chk.checked = isChecked;
                chk.disabled = !this.PODE_EDITAR;
                this.configurarVisualUsuario(idPerm, tipoStatus, isChecked, heranca.has(idPerm));
            });
        } catch (e) { alert('Erro ao carregar usuário.'); console.error(e); }
    }

    async processarClick(chk) {
        if (!this.PODE_EDITAR) {
            chk.checked = !chk.checked;
            alert('Você não tem permissão para editar.');
            return;
        }

        if (!this.ID_ATUAL) return;
        const idPerm = chk.dataset.id;
        const novoEstado = chk.checked;

        if (this.MODO === 'grupo') {
            await this.enviarAPI('grupo', this.ID_ATUAL, idPerm, novoEstado);
            return;
        }

        if (this.MODO === 'usuario') {
            await this.enviarAPI('usuario', this.ID_ATUAL, idPerm, novoEstado);
            this.DADOS_ATUAIS = this.DADOS_ATUAIS || { ids_heranca: [], overrides: {} };
            this.DADOS_ATUAIS.overrides[idPerm] = novoEstado;
            this.configurarVisualUsuario(idPerm, novoEstado ? 'forcado' : 'bloqueado', novoEstado, null);
        }
    }

    async resetarPermissao(idPerm) {
        if (!confirm('Voltar a herdar do grupo?')) return;
        await this.enviarAPI('usuario', this.ID_ATUAL, idPerm, null);
        this.DADOS_ATUAIS = this.DADOS_ATUAIS || { ids_heranca: [], overrides: {} };
        delete this.DADOS_ATUAIS.overrides[idPerm];
        const heranca = new Set(this.DADOS_ATUAIS.ids_heranca || []);
        const herdaAtivo = heranca.has(parseInt(idPerm));
        
        const chk = document.getElementById('chk-' + idPerm);
        chk.checked = herdaAtivo;
        this.configurarVisualUsuario(idPerm, 'herdado', herdaAtivo, null);
    }

    configurarVisualUsuario(idPerm, tipoStatus, isChecked, herancaValor) {
        const badgeInherit = document.getElementById(`badge-inherit-${idPerm}`);
        const badgeAllow = document.getElementById(`badge-allow-${idPerm}`);
        const badgeDeny = document.getElementById(`badge-deny-${idPerm}`);
        const btnReset = document.getElementById(`btn-reset-${idPerm}`);

        if(badgeInherit) badgeInherit.style.display = 'none';
        if(badgeAllow) badgeAllow.style.display = 'none';
        if(badgeDeny) badgeDeny.style.display = 'none';
        if(btnReset) btnReset.style.display = 'none';

        if (this.MODO === 'grupo') return;

        if (tipoStatus === 'herdado' && badgeInherit) {
            badgeInherit.style.display = 'inline-block';
        } else if (tipoStatus === 'forcado') {
            if (badgeAllow) badgeAllow.style.display = 'inline-block';
            if (btnReset) btnReset.style.display = 'inline-block';
        } else if (tipoStatus === 'bloqueado') {
            if (badgeDeny) badgeDeny.style.display = 'inline-block';
            if (btnReset) btnReset.style.display = 'inline-block';
        }
    }

    async enviarAPI(tipo, alvo, perm, conceder) {
        try {
            const resp = await fetch(configPermissoes.urls.salvarVinculo, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-Requested-With': 'XMLHttpRequest'
                },
                body: JSON.stringify({
                    Tipo: tipo,
                    IdAlvo: Number(alvo),
                    IdPermissao: Number(perm),
                    Conceder: conceder,
                })
            });
            const d = await resp.json();
            if (!resp.ok || !d.ok) {
                throw new Error(d.erro || 'Falha ao salvar vínculo de permissão.');
            }
        } catch(e) { console.error(e); alert(e.message || 'Erro de conexão'); }
    }

    ativarItemLista(el) {
        document.querySelectorAll('.luft-list-item').forEach(i => i.classList.remove('ativo'));
        el.classList.add('ativo');
    }
    
    prepararPainel(titulo, subtitulo) {
        document.getElementById('estadoVazio').classList.add('d-none');
        document.getElementById('painelPermissoes').classList.remove('d-none');
        document.getElementById('painelPermissoes').classList.add('d-flex');
        
        document.getElementById('tituloSelecionado').innerText = titulo;
        document.getElementById('subtituloSelecionado').innerText = subtitulo;
        document.querySelector('.luft-panel-scroll').scrollTop = 0;
    }

    filtrarLateral(val) {
        val = val.toLowerCase();
        const listaId = this.MODO === 'grupo' ? 'listaGrupos' : 'listaUsuarios';
        document.querySelectorAll(`#${listaId} .luft-list-item`).forEach(el => {
            el.style.display = el.innerText.toLowerCase().includes(val) ? 'flex' : 'none';
        });
    }

    filtrarPermissoes(val) {
        val = val.toLowerCase();
        document.querySelectorAll('.luft-perm-item').forEach(el => {
            el.style.display = el.innerText.toLowerCase().includes(val) ? 'flex' : 'none';
        });
        document.querySelectorAll('.luft-category-block').forEach(cat => {
            const visible = cat.querySelectorAll('.luft-perm-item[style="display: flex;"], .luft-perm-item:not([style*="display: none"])').length > 0;
            cat.style.display = visible ? 'block' : 'none';
        });
    }

    preverChave() {
        const mod = document.querySelector('input[name="modulo"]').value.toUpperCase().trim().replace(/ /g, '_') || 'MODULO';
        const acao = document.querySelector('select[name="acao"]').value.toUpperCase().trim() || 'ACAO';
        const exc = document.getElementById('inputExcecao').value.toUpperCase().trim().replace(/ /g, '_');
        
        let preview = `${mod}`;
        if(exc) preview += `.${exc}`;
        preview += `.${acao}`;
        
        document.getElementById('chavePreview').innerText = preview;
    }
}

const gerenciadorPermissoes = new GerenciadorPermissoes();

window.MudarAba = (novaAba, event) => gerenciadorPermissoes.mudarAba(novaAba, event);
window.CarregarGrupo = (el, id, nome) => gerenciadorPermissoes.carregarGrupo(el, id, nome);
window.CarregarUsuario = (el, id, nome) => gerenciadorPermissoes.carregarUsuario(el, id, nome);
window.ProcessarClick = (chk) => gerenciadorPermissoes.processarClick(chk);
window.ResetarPermissao = (idPerm) => gerenciadorPermissoes.resetarPermissao(idPerm);
window.FiltrarLateral = (val) => gerenciadorPermissoes.filtrarLateral(val);
window.FiltrarPermissoes = (val) => gerenciadorPermissoes.filtrarPermissoes(val);
window.PreverChave = () => gerenciadorPermissoes.preverChave();
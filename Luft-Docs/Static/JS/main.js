(function inicializarLuftDocs(window, document) {
    'use strict';

    const configuracaoGlobal = window.__LUFTDOCS_CONFIG__ || {};
    const tabelaRotas = configuracaoGlobal.routes || window.ROUTES || {};

    function normalizarPrefixo(prefixo) {
        const valor = String(prefixo || '/').trim();
        if (!valor || valor === '/') {
            return '/';
        }

        const prefixoNormalizado = valor.startsWith('/') ? valor : `/${valor}`;
        return prefixoNormalizado.replace(/\/+$/, '') || '/';
    }

    function obterPrefixoBase() {
        return normalizarPrefixo(
            configuracaoGlobal.basePrefix
                || window.__BASE_PREFIX__
                || document.body?.dataset?.basePrefix
                || document.documentElement?.dataset?.basePrefix
                || '/'
        );
    }

    function obterToken() {
        const tokenConfigurado = typeof configuracaoGlobal.token === 'string'
            ? configuracaoGlobal.token.trim()
            : '';

        if (tokenConfigurado) {
            return tokenConfigurado;
        }

        const tokenDataset = document.body?.dataset?.token?.trim()
            || document.documentElement?.dataset?.token?.trim()
            || '';

        if (tokenDataset) {
            return tokenDataset;
        }

        return new URLSearchParams(window.location.search).get('token') || '';
    }

    function ehUrlAbsoluta(valor) {
        return /^[a-z][a-z\d+.-]*:\/\//i.test(valor) || String(valor || '').startsWith('//');
    }

    function resolverRota(nomeOuCaminho = '') {
        if (typeof nomeOuCaminho !== 'string') {
            return '';
        }

        const valor = nomeOuCaminho.trim();
        if (!valor) {
            return '';
        }

        if (!/^[A-Za-z0-9_]+(?:\.[A-Za-z0-9_]+)+$/.test(valor)) {
            return valor;
        }

        const rotaEncontrada = valor.split('.').reduce((acumulador, chave) => {
            if (acumulador && typeof acumulador === 'object' && chave in acumulador) {
                return acumulador[chave];
            }
            return undefined;
        }, tabelaRotas);

        return typeof rotaEncontrada === 'string' ? rotaEncontrada : valor;
    }

    function aplicarPrefixo(caminho) {
        if (!caminho || ehUrlAbsoluta(caminho)) {
            return caminho;
        }

        const url = new URL(caminho, window.location.origin);
        const prefixoBase = obterPrefixoBase();

        if (
            prefixoBase !== '/'
            && url.pathname !== prefixoBase
            && !url.pathname.startsWith(`${prefixoBase}/`)
        ) {
            const pathname = url.pathname.startsWith('/') ? url.pathname : `/${url.pathname}`;
            url.pathname = `${prefixoBase}${pathname}`.replace(/\/+/g, '/');
        }

        return `${url.pathname}${url.search}${url.hash}`;
    }

    function aplicarQuery(url, query) {
        if (!query || typeof query !== 'object') {
            return;
        }

        Object.entries(query).forEach(([chave, valor]) => {
            if (valor === undefined || valor === null) {
                return;
            }

            url.searchParams.delete(chave);

            if (Array.isArray(valor)) {
                valor.forEach((item) => {
                    if (item !== undefined && item !== null) {
                        url.searchParams.append(chave, String(item));
                    }
                });
                return;
            }

            url.searchParams.set(chave, String(valor));
        });
    }

    function montarUrl(nomeOuCaminho, opcoes = {}) {
        const rotaResolvida = resolverRota(nomeOuCaminho);
        if (!rotaResolvida) {
            return '';
        }

        const url = ehUrlAbsoluta(rotaResolvida)
            ? new URL(rotaResolvida)
            : new URL(aplicarPrefixo(rotaResolvida), window.location.origin);

        aplicarQuery(url, opcoes.query);

        const tokenInformado = typeof opcoes.token === 'string'
            ? opcoes.token.trim()
            : '';
        const deveIncluirToken = opcoes.includeToken === true || tokenInformado.length > 0;

        if (deveIncluirToken && !url.searchParams.has('token')) {
            const tokenAtual = tokenInformado || obterToken();
            if (tokenAtual) {
                url.searchParams.set('token', tokenAtual);
            }
        }

        if (typeof opcoes.hash === 'string' && opcoes.hash.trim()) {
            url.hash = opcoes.hash.startsWith('#') ? opcoes.hash : `#${opcoes.hash}`;
        }

        return ehUrlAbsoluta(rotaResolvida)
            ? url.toString()
            : `${url.pathname}${url.search}${url.hash}`;
    }

    function montarCorpoRequisicao({ body, json, formData }) {
        if (formData instanceof FormData) {
            return formData;
        }

        if (json !== undefined) {
            return JSON.stringify(json);
        }

        return body;
    }

    async function requisitar(nomeOuCaminho, opcoes = {}) {
        const cabecalhos = new Headers(opcoes.headers || {});

        if (opcoes.ajax !== false) {
            cabecalhos.set('X-Requested-With', 'XMLHttpRequest');
        }

        if (opcoes.json !== undefined && !cabecalhos.has('Content-Type')) {
            cabecalhos.set('Content-Type', 'application/json');
        }

        if (opcoes.responseType === 'json' && !cabecalhos.has('Accept')) {
            cabecalhos.set('Accept', 'application/json');
        }

        return window.fetch(
            montarUrl(nomeOuCaminho, {
                query: opcoes.query,
                includeToken: opcoes.includeToken !== false,
                token: opcoes.token,
                hash: opcoes.hash,
            }),
            {
                method: opcoes.method || 'GET',
                headers: cabecalhos,
                body: montarCorpoRequisicao(opcoes),
                credentials: opcoes.credentials || 'same-origin',
                signal: opcoes.signal,
            }
        );
    }

    async function requisitarJson(nomeOuCaminho, opcoes = {}) {
        const response = await requisitar(nomeOuCaminho, {
            ...opcoes,
            responseType: 'json',
        });

        let data = null;
        const tipoConteudo = response.headers.get('content-type') || '';

        if (tipoConteudo.includes('application/json')) {
            try {
                data = await response.json();
            } catch (_erro) {
                data = null;
            }
        } else {
            try {
                const texto = await response.text();
                data = texto ? JSON.parse(texto) : null;
            } catch (_erro) {
                data = null;
            }
        }

        return { response, data };
    }

    const cliente = {
        get routes() {
            return tabelaRotas;
        },
        get basePrefix() {
            return obterPrefixoBase();
        },
        get token() {
            return obterToken();
        },
        getToken: obterToken,
        resolveRoute: resolverRota,
        buildUrl: montarUrl,
        route(nomeOuCaminho, opcoes = {}) {
            return montarUrl(nomeOuCaminho, {
                ...opcoes,
                includeToken: opcoes.includeToken !== false,
            });
        },
        request: requisitar,
        requestJson: requisitarJson,
        navigate(nomeOuCaminho, opcoes = {}) {
            const destino = montarUrl(nomeOuCaminho, {
                ...opcoes,
                includeToken: opcoes.includeToken !== false,
            });
            window.location.href = destino;
            return destino;
        },
    };

    window.__BASE_PREFIX__ = cliente.basePrefix;
    window.ROUTES = tabelaRotas;
    window.LuftDocs = cliente;
})(window, document);
(function () {
    const viewers = new WeakMap();
    const observadores = new WeakMap();

    function criarConfiguracaoViewer(filtroImagem) {
        return {
            url: 'src',
            toolbar: {
                zoomIn: 1,
                zoomOut: 1,
                oneToOne: 1,
                reset: 1,
                prev: 0,
                play: { show: 0, size: 'large' },
                next: 0,
                rotateLeft: 1,
                rotateRight: 1,
                flipHorizontal: 1,
                flipVertical: 1,
            },
            title: true,
            navbar: false,
            tooltip: true,
            movable: true,
            zoomable: true,
            transition: true,
            filter(imagem) {
                return typeof filtroImagem === 'function' ? filtroImagem(imagem) : true;
            },
        };
    }

    function inicializarViewer(container, filtroImagem) {
        if (!container || typeof Viewer === 'undefined') {
            return null;
        }

        const viewerExistente = viewers.get(container);
        if (viewerExistente) {
            viewerExistente.update();
            return viewerExistente;
        }

        const viewer = new Viewer(container, criarConfiguracaoViewer(filtroImagem));
        viewers.set(container, viewer);
        return viewer;
    }

    function observarAlteracoes(container, filtroImagem) {
        if (!container || observadores.has(container) || typeof MutationObserver === 'undefined') {
            return;
        }

        const observador = new MutationObserver(() => {
            const viewer = viewers.get(container);
            if (viewer) {
                viewer.update();
                return;
            }
            inicializarViewer(container, filtroImagem);
        });

        observador.observe(container, { childList: true, subtree: true });
        observadores.set(container, observador);
    }

    function inicializarGaleriasMarkdown() {
        document.querySelectorAll('.markdown-body').forEach((container) => {
            inicializarViewer(container, (imagem) => Boolean(imagem.closest('.modulo-conteudo, .submodulo-conteudo')));
        });
    }

    function inicializarGaleriasLia() {
        document.querySelectorAll('.luft-lia-chat-history').forEach((container) => {
            const filtroLia = (imagem) => Boolean(imagem.closest('.luft-lia-message.ai-message'));
            inicializarViewer(container, filtroLia);
            observarAlteracoes(container, filtroLia);
        });
    }

    function inicializar() {
        inicializarGaleriasMarkdown();
        inicializarGaleriasLia();
    }

    document.addEventListener('DOMContentLoaded', inicializar);

    window.LuftAmpliadorImagem = {
        inicializar,
        atualizar(container) {
            if (!container) {
                return;
            }

            if (container.matches('.luft-lia-chat-history')) {
                const filtroLia = (imagem) => Boolean(imagem.closest('.luft-lia-message.ai-message'));
                inicializarViewer(container, filtroLia);
                observarAlteracoes(container, filtroLia);
                return;
            }

            if (container.matches('.markdown-body')) {
                inicializarViewer(container, (imagem) => Boolean(imagem.closest('.modulo-conteudo, .submodulo-conteudo')));
            }
        },
    };
})();

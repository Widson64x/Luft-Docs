document.addEventListener('DOMContentLoaded', () => {
    // --- 1. SELETORES E VARIÁVEIS ---
    const contentArea = document.querySelector('.modulo-conteudo');
    const tocSidebar = document.getElementById('toc-sidebar');
    const tocList = document.getElementById('toc-list');
    const tocProgressBar = document.getElementById('toc-progress-bar');
    const tooltipTriggerList = document.querySelectorAll('[data-bs-toggle="tooltip"]');

    // Inicializa tooltips do Bootstrap
    [...tooltipTriggerList].map(tooltipTriggerEl => new bootstrap.Tooltip(tooltipTriggerEl));

    // Validação inicial
    if (!contentArea || !tocSidebar || !tocList || !tocProgressBar) {
        console.warn('Elementos essenciais para o TOC não foram encontrados.');
        return;
    }

    const headings = Array.from(contentArea.querySelectorAll('h1, h2, h3, h4'));

    if (headings.length < 2) { // Não mostrar TOC para menos de 2 tópicos
        tocSidebar.style.display = 'none';
        return;
    }

    tocSidebar.style.display = 'flex'; // Usar 'flex' por conta do layout CSS

    // --- 2. GERAÇÃO DINÂMICA DO TOC ---
    const slugify = (text) => text.toString().toLowerCase()
        .replace(/\s+/g, '-')
        .replace(/[^\w\-]+/g, '')
        .replace(/\-\-+/g, '-')
        .replace(/^-+/, '').replace(/-+$/, '');

    const createTocItem = (heading, index) => {
        const level = parseInt(heading.tagName.substring(1));
        const text = heading.textContent.trim();
        const id = heading.id || `${slugify(text)}-${index}`;
        heading.id = id;

        const li = document.createElement('li');
        li.classList.add('toc-level-' + level);

        const itemWrapper = document.createElement('div');
        itemWrapper.className = 'toc-item';

        const link = document.createElement('a');
        link.href = `#${id}`;
        link.textContent = text;
        link.addEventListener('click', (e) => {
            e.preventDefault();
            heading.scrollIntoView({ behavior: 'smooth', block: 'start' });
            history.pushState(null, null, `#${id}`);
        });

        itemWrapper.appendChild(link);
        li.appendChild(itemWrapper);
        return li;
    };

    const fragment = document.createDocumentFragment();
    let parentStack = [{ el: fragment, level: 0 }];

    headings.forEach((heading, index) => {
        const li = createTocItem(heading, index);
        const level = parseInt(heading.tagName.substring(1));

        while (level <= parentStack[parentStack.length - 1].level) {
            parentStack.pop();
        }

        let parent = parentStack[parentStack.length - 1].el;

        if (parent.tagName === 'LI') {
            let ul = parent.querySelector('ul');
            if (!ul) {
                ul = document.createElement('ul');
                ul.classList.add('hidden');
                parent.appendChild(ul);

                const toggleBtn = document.createElement('button');
                toggleBtn.className = 'toc-toggle';
                toggleBtn.setAttribute('aria-expanded', 'false');
                toggleBtn.innerHTML = `<i class="bi bi-chevron-down icon-chevron"></i>`;
                parent.querySelector('.toc-item').insertBefore(toggleBtn, parent.querySelector('a'));
            }
            parent = ul;
        }

        parent.appendChild(li);
        parentStack.push({ el: li, level });
    });

    tocList.appendChild(fragment);

    // --- 3. FUNCIONALIDADE DE RECOLHER/EXPANDIR (ACCORDION) ---
    tocList.addEventListener('click', (e) => {
        const toggleBtn = e.target.closest('.toc-toggle');
        if (toggleBtn) {
            const isExpanded = toggleBtn.getAttribute('aria-expanded') === 'true';
            toggleBtn.setAttribute('aria-expanded', !isExpanded);
            const sublist = toggleBtn.closest('.toc-item').nextElementSibling;
            if (sublist && sublist.tagName === 'UL') {
                sublist.classList.toggle('hidden', isExpanded);
            }
        }
    });

    // --- 4. DESTAQUE DE SEÇÃO ATIVA (INTERSECTION OBSERVER) ---
    const observer = new IntersectionObserver(entries => {
        entries.forEach(entry => {
            const id = entry.target.getAttribute('id');
            const tocLink = tocList.querySelector(`a[href="#${id}"]`);
            if (tocLink) {
                const tocItem = tocLink.closest('.toc-item');
                if (entry.isIntersecting && entry.intersectionRatio > 0) {
                    tocItem.classList.add('is-active');
                    let parentLi = tocItem.closest('ul')?.parentElement;
                    while (parentLi && parentLi.tagName === 'LI') {
                        parentLi.querySelector('.toc-toggle')?.setAttribute('aria-expanded', 'true');
                        parentLi.querySelector('ul')?.classList.remove('hidden');
                        parentLi = parentLi.closest('ul')?.parentElement;
                    }
                } else {
                    tocItem.classList.remove('is-active');
                }
            }
        });
    }, {
        rootMargin: '0px 0px -80% 0px',
        threshold: 0.1
    });

    headings.forEach(heading => observer.observe(heading));

    // --- 5. BARRA DE PROGRESSO DE LEITURA ---
    const updateProgressBar = () => {
        const contentRect = contentArea.getBoundingClientRect();
        const scrollableHeight = contentArea.scrollHeight - window.innerHeight;
        const scrolled = window.scrollY - contentArea.offsetTop;
        const progress = Math.max(0, Math.min(100, (scrolled / scrollableHeight) * 100));

        tocProgressBar.style.width = `${progress}%`;
        requestAnimationFrame(updateProgressBar);
    };

    requestAnimationFrame(updateProgressBar);
});
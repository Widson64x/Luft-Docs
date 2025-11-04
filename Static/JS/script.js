document.addEventListener('DOMContentLoaded', () => {

    // =======================================================
    // === MÓDULO DE ANIMAÇÃO DE FUNDO (CANVAS) ==============
    // =======================================================
    const backgroundAnimation = (() => {
        const canvas = document.getElementById('background-animation-canvas');
        if (!canvas) return null;

        const ctx = canvas.getContext('2d');
        let particles = [];
        let animationFrameId;

        let config = {
            quantity: 50,
            speed: 1.0,
            color: 'rgba(13, 110, 253, 0.5)'
        };

        const resizeCanvas = () => {
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
        };

        class Particle {
            constructor() {
                this.x = Math.random() * canvas.width;
                this.y = Math.random() * canvas.height;
                this.radius = Math.random() * 2 + 1;
                this.vx = (Math.random() - 0.5) * config.speed;
                this.vy = (Math.random() - 0.5) * config.speed;
            }

            draw() {
                ctx.beginPath();
                ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
                ctx.fillStyle = config.color;
                ctx.fill();
            }

            update() {
                this.x += this.vx;
                this.y += this.vy;

                if (this.x < 0 || this.x > canvas.width) this.vx *= -1;
                if (this.y < 0 || this.y > canvas.height) this.vy *= -1;
            }
        }

        const createParticles = () => {
            particles = [];
            for (let i = 0; i < config.quantity; i++) {
                particles.push(new Particle());
            }
        };

        const animate = () => {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            particles.forEach(p => {
                p.update();
                p.draw();
            });
            animationFrameId = requestAnimationFrame(animate);
        };

        const stop = () => {
            cancelAnimationFrame(animationFrameId);
        };
        
        const start = () => {
            stop();
            resizeCanvas();
            createParticles();
            animate();
        };

        window.addEventListener('resize', () => {
             resizeCanvas();
             createParticles();
        });

        return {
            start,
            stop,
            setQuantity: (newQuantity) => {
                config.quantity = parseInt(newQuantity, 10);
                createParticles();
            },
            setSpeed: (newSpeed) => {
                config.speed = parseFloat(newSpeed);
                particles.forEach(p => {
                    p.vx = (Math.random() - 0.5) * config.speed;
                    p.vy = (Math.random() - 0.5) * config.speed;
                });
            },
            setColor: (isDark) => {
                config.color = isDark ? 'rgba(51, 157, 255, 0.4)' : 'rgba(13, 110, 253, 0.5)';
            },
            setVisibility: (visible) => {
                canvas.style.display = visible ? 'block' : 'none';
                if (visible) start();
                else stop();
            }
        };
    })();


    // =======================================================
    // === LÓGICA DO MODAL DE CONFIGURAÇÕES ===================
    // =======================================================
    const devModalEl = document.getElementById('modalDev');
    const devModal = devModalEl ? new bootstrap.Modal(devModalEl) : null;
    const configToastEl = document.getElementById('configToast');
    const configToast = configToastEl ? bootstrap.Toast.getOrCreateInstance(configToastEl) : null;
    const highlightStyle = document.getElementById('highlight-theme-style');
    const body = document.body;

    const ui = {
        selectTema: document.getElementById('selectTema'),
        fontSize: document.getElementById('fontSize'),
        selectAnimacao: document.getElementById('selectAnimacao'),
        selectLiaMode: document.getElementById('selectLiaMode'), // <<< NOVO
        rangeQuantidade: document.getElementById('rangeQuantidade'),
        labelQuantidade: document.getElementById('labelQuantidade'),
        rangeVelocidade: document.getElementById('rangeVelocidade'),
        labelVelocidade: document.getElementById('labelVelocidade'),
        btnSalvarConfigs: document.getElementById('btnSalvarConfigs')
    };

    // --- FUNÇÕES DE APLICAÇÃO DE ESTILOS ---
    
    const applyTheme = (theme) => {
        // Primeiro, remove todas as classes de tema para garantir um estado limpo
        body.classList.remove('theme-light', 'theme-dark', 'theme-luft', 'theme-sunset', 'theme-emerald');
    
        let finalTheme = theme;
    
        // Se o tema for 'automático', decide qual tema usar com base no sistema operacional
        if (theme === 'auto') {
            const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
            finalTheme = prefersDark ? 'dark' : 'light';
        }
    
        // Adiciona a classe de tema correta (ex: 'theme-light', 'theme-dark', 'theme-luft')
        body.classList.add(`theme-${finalTheme || 'light'}`); // Fallback para light
    
        // Define o tema do highlight.js. O tema 'luft' é claro, então usará o tema 'github'.
        const isDark = (finalTheme === 'dark');
        if (highlightStyle) {
            highlightStyle.href = `https://cdnjs.cloudflare.com/ajax/libs/highlight.js/11.9.0/styles/github${isDark ? '-dark' : ''}.min.css`;
        }
        
        // Atualiza a cor da animação de fundo, se existir
        if (backgroundAnimation) {
            backgroundAnimation.setColor(isDark);
        }
    };

    const applyFontSize = (size) => {
        body.style.setProperty('--font-size-base', size);
    };

    const applyBgAnimationType = (type) => {
        if (backgroundAnimation) {
            // Assumindo que 'colisao' é o padrão (visível) e 'original' é o outro
            // A lógica original parecia invertida, ajustando:
            // 'original' (clássica) é a que usa CSS, então canvas 'block' = false
            // 'colisao' (nova) é a que usa canvas, então canvas 'block' = true
            const isCanvasAnimation = (type === 'colisao');
            backgroundAnimation.setVisibility(isCanvasAnimation);
        }
    };

    /**
     * NOVO: Aplica o modo da LIA no body
     */
    const applyLiaMode = (mode) => {
        body.setAttribute('data-lia-mode', mode || 'sidebar');
    };
    
    const applyBgQuantity = (quantity) => {
        if(ui.labelQuantidade) ui.labelQuantidade.textContent = quantity;
        if (backgroundAnimation) {
            backgroundAnimation.setQuantity(quantity);
        }
    };
    
    const applyBgSpeed = (speed) => {
        if(ui.labelVelocidade) ui.labelVelocidade.textContent = `${parseFloat(speed).toFixed(1)}x`;
        if (backgroundAnimation) {
            backgroundAnimation.setSpeed(speed);
        }
    };

    // --- CARREGAMENTO E SALVAMENTO NO LOCALSTORAGE ---
    const loadSettings = () => {
        const settings = {
            theme: localStorage.getItem('ld_theme') || 'light',
            fontSize: localStorage.getItem('ld_fontSize') || '1rem',
            bgAnimation: localStorage.getItem('ld_bgAnimation') || 'colisao',
            liaMode: localStorage.getItem('ld_lia_mode') || 'sidebar', // <<< NOVO
            bgQuantity: localStorage.getItem('ld_bg_quantity') || '50',
            bgSpeed: localStorage.getItem('ld_bg_speed') || '1.0'
        };

        // Aplica os valores carregados aos seletores do UI
        if (ui.selectTema) ui.selectTema.value = settings.theme;
        if (ui.fontSize) ui.fontSize.value = settings.fontSize;
        if (ui.selectAnimacao) ui.selectAnimacao.value = settings.bgAnimation;
        if (ui.selectLiaMode) ui.selectLiaMode.value = settings.liaMode; // <<< NOVO
        if (ui.rangeQuantidade) ui.rangeQuantidade.value = settings.bgQuantity;
        if (ui.rangeVelocidade) ui.rangeVelocidade.value = settings.bgSpeed;
        
        // Chama as funções para aplicar os estilos
        applyTheme(settings.theme);
        applyFontSize(settings.fontSize);
        applyBgAnimationType(settings.bgAnimation);
        applyLiaMode(settings.liaMode); // <<< NOVO
        applyBgQuantity(settings.bgQuantity);
        applyBgSpeed(settings.bgSpeed);
        
        // Inicializa o highlight.js se ele existir
        if (typeof hljs !== 'undefined') {
            hljs.highlightAll();
        }

        // Inicializa o Viewer.js se ele existir
        const viewerEl = document.getElementById('main-content');
        if (viewerEl && typeof Viewer !== 'undefined') {
            new Viewer(viewerEl, {
                filter(image) { return image.parentElement.classList.contains('modulo-conteudo'); },
                toolbar: true, navbar: false, title: false, movable: true, zoomable: true,
                rotatable: false, scalable: false, transition: true, fullscreen: true,
            });
        }
    };
    
    const saveSettings = () => {
        if (!ui.btnSalvarConfigs) return;

        localStorage.setItem('ld_theme', ui.selectTema.value);
        localStorage.setItem('ld_fontSize', ui.fontSize.value);
        localStorage.setItem('ld_bgAnimation', ui.selectAnimacao.value);
        localStorage.setItem('ld_lia_mode', ui.selectLiaMode.value); // <<< NOVO
        localStorage.setItem('ld_bg_quantity', ui.rangeQuantidade.value);
        localStorage.setItem('ld_bg_speed', ui.rangeVelocidade.value);
        
        if (configToast) configToast.show();
        
        const configModalEl = document.getElementById('modalConfiguracoes');
        if (configModalEl) {
            const configModal = bootstrap.Modal.getInstance(configModalEl);
            if (configModal) configModal.hide();
        }
    };

    // --- EVENT LISTENERS PARA ATUALIZAÇÃO EM TEMPO REAL E SALVAMENTO ---
    if(ui.btnSalvarConfigs) {
        if (ui.selectTema) ui.selectTema.addEventListener('change', (e) => applyTheme(e.target.value));
        if (ui.fontSize) ui.fontSize.addEventListener('change', (e) => applyFontSize(e.target.value));
        if (ui.selectAnimacao) ui.selectAnimacao.addEventListener('change', (e) => applyBgAnimationType(e.target.value));
        if (ui.selectLiaMode) ui.selectLiaMode.addEventListener('change', (e) => applyLiaMode(e.target.value)); // <<< NOVO
        if (ui.rangeQuantidade) ui.rangeQuantidade.addEventListener('input', (e) => applyBgQuantity(e.target.value));
        if (ui.rangeVelocidade) ui.rangeVelocidade.addEventListener('input', (e) => applyBgSpeed(e.target.value));
        
        ui.btnSalvarConfigs.addEventListener('click', saveSettings);
    }

    // --- LÓGICA ANTIGA (DEV FEATURES, BUG REPORT) ---
    // Esta parte foi mantida como estava
    document.querySelectorAll('.dev-feature').forEach(el => {
        const eventType = el.type === 'checkbox' ? 'change' : 'click';
        el.addEventListener(eventType, (e) => {
            if ((el.type === 'checkbox' && e.target.checked) || (el.type !== 'checkbox')) {
                e.preventDefault();
                e.stopPropagation();
                if (devModal) devModal.show();
                if (el.type === 'checkbox') e.target.checked = false;
                if(el.hasAttribute('data-bs-toggle')) {
                    const previousTab = document.querySelector('.nav-tabs .nav-link.active');
                    if(previousTab) bootstrap.Tab.getOrCreateInstance(previousTab).show();
                }
            }
        });
    });

    const bugReportForm = document.getElementById('bugReportForm');
    if (bugReportForm) {
        const reportTypeSelect = document.getElementById('reportType');
        const targetEntityWrapper = document.getElementById('targetEntityWrapper');
        const errorCategoryWrapper = document.getElementById('errorCategoryWrapper');
        const reportStatus = document.getElementById('reportStatus');
        const errorCategories = {
            'visual': 'Erro visual / Quebra de layout',
            'funcionalidade': 'Botão ou funcionalidade não funciona',
            'dados': 'Informação errada ou faltando',
            'performance': 'Lentidão ou travamento',
            'outro': 'Outro tipo de problema'
        };

        reportTypeSelect.addEventListener('change', function() {
            const selectedType = this.value;
            targetEntityWrapper.innerHTML = '';
            targetEntityWrapper.style.display = 'none';
            errorCategoryWrapper.innerHTML = '';
            errorCategoryWrapper.style.display = 'none';

            if (selectedType === 'tela' || selectedType === 'modulo') {
                let categoryOptions = Object.entries(errorCategories).map(([value, text]) => `<option value="${value}">${text}</option>`).join('');
                errorCategoryWrapper.innerHTML = `<label for="errorCategory" class="form-label">Qual a categoria do problema?</label><select class="form-select" id="errorCategory" required><option value="" selected disabled>Selecione...</option>${categoryOptions}</select>`;
                errorCategoryWrapper.style.display = 'block';
            }

            if (selectedType === 'tela') {
                targetEntityWrapper.style.display = 'block';
                targetEntityWrapper.innerHTML = `<label for="targetEntity" class="form-label">Em qual tela?</label><input type="text" class="form-control" id="targetEntity" required>`;
            } else if (selectedType === 'modulo' && typeof allModulesForReport !== 'undefined') {
                targetEntityWrapper.style.display = 'block';
                let moduleOptions = allModulesForReport.map(mod => `<option value="${mod.id}">${mod.nome}</option>`).join('');
                targetEntityWrapper.innerHTML = `<label for="targetEntity" class="form-label">Qual módulo?</label><select class="form-select" id="targetEntity" required><option value="" selected disabled>Selecione...</option>${moduleOptions}</select>`;
            }
        });

        bugReportForm.addEventListener('submit', function(event) {
            event.preventDefault();
            const submitButton = this.querySelector('button[type="submit"]');
            const reportData = {
                report_type: reportTypeSelect.value,
                target_entity: document.getElementById('targetEntity')?.value || null,
                error_category: document.getElementById('errorCategory')?.value || null,
                description: document.getElementById('bugDescription').value
            };
            submitButton.disabled = true;
            submitButton.innerHTML = '<span class="spinner-border spinner-border-sm"></span> Enviando...';
            reportStatus.innerHTML = '';

            // A variável bugReportURL deve ser definida em 'base.html'
            if (typeof bugReportURL === 'undefined') {
                reportStatus.innerHTML = `<div class="alert alert-danger"><b>Falha:</b> URL de report não definida.</div>`;
                submitButton.disabled = false;
                submitButton.innerHTML = '<i class="bi bi-bug-fill me-2"></i>Enviar Feedback';
                return;
            }

            fetch(bugReportURL, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(reportData)
                })
                .then(response => response.ok ? response.json() : response.json().then(err => { throw new Error(err.message) }))
                .then(data => {
                    reportStatus.innerHTML = `<div class="alert alert-success">${data.message}</div>`;
                    bugReportForm.reset();
                    reportTypeSelect.dispatchEvent(new Event('change'));
                })
                .catch(error => {
                    reportStatus.innerHTML = `<div class="alert alert-danger"><b>Falha:</b> ${error.message}</div>`;
                })
                .finally(() => {
                    submitButton.disabled = false;
                    submitButton.innerHTML = '<i class="bi bi-bug-fill me-2"></i>Enviar Feedback';
                });
        });
    }

    // Carrega as configurações na inicialização da página
    loadSettings();
});
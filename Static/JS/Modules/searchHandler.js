document.addEventListener('DOMContentLoaded', function() {
    // --- Lógica de Autocomplete ---
    const buscaInput = document.getElementById('busca-input');
    const autocompleteList = document.getElementById('autocomplete-list');
    let currentFocus = -1;

    if (buscaInput) {
        buscaInput.addEventListener('input', function() {
            const val = this.value;
            if (val.length < 2) {
                autocompleteList.style.display = 'none';
                return;
            }
            fetch(`/api/autocomplete?q=${encodeURIComponent(val)}`)
                .then(response => response.json())
                .then(sugestoes => {
                    autocompleteList.innerHTML = '';
                    if (sugestoes.length === 0) {
                        autocompleteList.style.display = 'none';
                        return;
                    }
                    sugestoes.forEach((s) => {
                        const li = document.createElement('li');
                        li.textContent = s;
                        li.onclick = () => {
                            buscaInput.value = s;
                            autocompleteList.style.display = 'none';
                            buscaInput.form.submit();
                        };
                        autocompleteList.appendChild(li);
                    });
                    autocompleteList.style.display = 'block';
                    currentFocus = -1;
                }).catch(() => {
                    autocompleteList.style.display = 'none';
                });
        });

        buscaInput.addEventListener('keydown', function(e) {
            let items = autocompleteList.getElementsByTagName('li');
            if (!items.length) return;
            if (e.key === 'ArrowDown') {
                currentFocus++;
                addActive(items);
            } else if (e.key === 'ArrowUp') {
                currentFocus--;
                addActive(items);
            } else if (e.key === 'Enter') {
                if (currentFocus > -1) {
                    e.preventDefault();
                    items[currentFocus].click();
                }
            }
        });
    }

    function addActive(items) {
        if (!items) return;
        removeActive(items);
        if (currentFocus >= items.length) currentFocus = 0;
        if (currentFocus < 0) currentFocus = items.length - 1;
        items[currentFocus].classList.add('active');
    }

    function removeActive(items) {
        for (let item of items) {
            item.classList.remove('active');
        }
    }

    document.addEventListener('click', function(e) {
        if (autocompleteList && !autocompleteList.contains(e.target) && e.target !== buscaInput) {
            autocompleteList.style.display = 'none';
        }
    });

    // --- LÓGICA DE ROLAGEM E NAVEGAÇÃO ENTRE DESTAQUES ---
    const marks = document.querySelectorAll('.markdown-body mark');
    let currentMarkIndex = 0;

    if (marks.length > 0) {
        function scrollToMark(index) {
            marks.forEach(mark => mark.classList.remove('current-mark'));
            const currentMark = marks[index];
            currentMark.classList.add('current-mark');
            currentMark.scrollIntoView({
                behavior: 'smooth',
                block: 'center'
            });
        }
        scrollToMark(currentMarkIndex);

        document.addEventListener('keydown', function(e) {
            if (e.key === 'Enter' && document.activeElement !== buscaInput) {
                e.preventDefault();
                currentMarkIndex = (currentMarkIndex + 1) % marks.length;
                scrollToMark(currentMarkIndex);
            }
            if (e.key === 'Escape') {
                e.preventDefault();
                const url = new URL(window.location.href);
                url.searchParams.delete('q');
                window.location.href = url.toString();
            }
        });
    }
});
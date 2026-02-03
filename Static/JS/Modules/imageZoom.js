document.addEventListener('DOMContentLoaded', () => {
    // Seleciona o container que contém as imagens do markdown
    const gallery = document.querySelector('.markdown-body');
    
    if (gallery) {
        // Inicializa o Viewer.js
        const viewer = new Viewer(gallery, {
            url: 'src', // Usa o atributo src da imagem
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
            title: true, // Mostra o nome/alt da imagem
            navbar: false, // Esconde a barra de navegação inferior se for apenas uma imagem
            tooltip: true, // Mostra a porcentagem do zoom
            movable: true, // Permite arrastar a imagem
            zoomable: true, // Permite zoom com o scroll do mouse
            transition: true,
        });
    }
});
document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('.markdown-body img').forEach(img => {
        img.style.cursor = 'pointer';
        img.addEventListener('click', () => {
            const imageModalElement = document.getElementById('imagemModal');
            if (imageModalElement) {
                document.getElementById('imagemExpandida').src = img.src;
                const modal = new bootstrap.Modal(imageModalElement);
                modal.show();
            }
        });
    });
});
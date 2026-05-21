document.addEventListener('DOMContentLoaded', function() {
    const marqueSelect = document.getElementById('id_marque');
    const autreMarqueRow = document.querySelector('.field-autre_marque');

    if (marqueSelect && autreMarqueRow) {
        function toggleAutreMarque() {
            if (marqueSelect.value === 'Autre') {
                autreMarqueRow.style.display = 'block';
            } else {
                autreMarqueRow.style.display = 'none';
            }
        }

        // État initial
        toggleAutreMarque();

        // Au changement
        marqueSelect.addEventListener('change', toggleAutreMarque);
    }
});

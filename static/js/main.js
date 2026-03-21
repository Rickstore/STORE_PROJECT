// ── Gestion du Thème (Clair / Sombre) ──────────────────────────────────────────
const darkModeToggle = document.getElementById('dark-mode-toggle');
const mapFrame = document.getElementById('store-map');
const htmlElement = document.documentElement;

function setTheme(isDark) {
    if (isDark) {
        htmlElement.classList.add('dark');
        if (mapFrame) mapFrame.style.filter = 'grayscale(1) invert(0.9) contrast(1.2)';
        localStorage.setItem('theme', 'dark');
    } else {
        htmlElement.classList.remove('dark');
        if (mapFrame) mapFrame.style.filter = 'grayscale(1) contrast(1.2)';
        localStorage.setItem('theme', 'light');
    }
}

// Initialisation du thème au chargement
const savedTheme = localStorage.getItem('theme');
const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
setTheme(savedTheme === 'dark' || (!savedTheme && prefersDark));

if (darkModeToggle) {
    darkModeToggle.addEventListener('click', () => {
        setTheme(!htmlElement.classList.contains('dark'));
    });
}

// Synchroniser l'état de l'icône si le thème du système change
window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
    if (!localStorage.getItem('theme')) setTheme(e.matches);
});


// ── Logique du Menu Mobile ───────────────────────────────────────────────────
const menuOpenBtn = document.getElementById('mobile-menu-open');
const menuCloseBtn = document.getElementById('mobile-menu-close');
const menuWrapper = document.getElementById('mobile-menu-wrapper');
const menuBackdrop = document.getElementById('mobile-menu-backdrop');
const menuOverlay = document.getElementById('mobile-menu-overlay');

function openMenu() {
    if (!menuWrapper) return;
    menuWrapper.classList.remove('hidden');
    // Forcer le reflow pour les transitions
    menuWrapper.offsetHeight;
    menuBackdrop.classList.add('opacity-100');
    menuOverlay.classList.remove('translate-x-[120%]');
    document.body.style.overflow = 'hidden';
}

function closeMenu() {
    if (!menuBackdrop || !menuOverlay) return;
    menuBackdrop.classList.remove('opacity-100');
    menuOverlay.classList.add('translate-x-[120%]');
    document.body.style.overflow = '';
    
    // Attendre la fin de la transition avant de masquer le conteneur
    setTimeout(() => {
        if (menuOverlay.classList.contains('translate-x-[120%]')) {
            menuWrapper.classList.add('hidden');
        }
    }, 500);
}

if (menuOpenBtn) menuOpenBtn.addEventListener('click', openMenu);
if (menuCloseBtn) menuCloseBtn.addEventListener('click', closeMenu);
if (menuBackdrop) menuBackdrop.addEventListener('click', closeMenu);

// Fermer le menu lors du clic sur un lien du menu
document.querySelectorAll('#mobile-menu-overlay a').forEach(link => {
    link.addEventListener('click', closeMenu);
});


// ── Notifications (Toast) ────────────────────────────────────────────────────
function showToast(message, type = 'success') {
    const container = document.getElementById('toast-container');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = 'toast';
    if (type === 'error') toast.style.borderLeftColor = '#EF4444';

    const icon = type === 'success' 
        ? '<i class="fa-solid fa-circle-check text-brand-green"></i>' 
        : '<i class="fa-solid fa-circle-exclamation text-red-500"></i>';

    toast.innerHTML = `${icon} <span>${message}</span>`;
    container.appendChild(toast);

    setTimeout(() => toast.classList.add('show'), 100);
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 400);
    }, 3000);
}


// ── AJAX : Ajouter au panier sans rechargement ──────────────────────────────
function getCsrfToken() {
    // Lit le cookie csrftoken
    const name = 'csrftoken';
    const cookies = document.cookie.split(';');
    for (let c of cookies) {
        c = c.trim();
        if (c.startsWith(name + '=')) return decodeURIComponent(c.slice(name.length + 1));
    }
    return '';
}

document.addEventListener('click', function (e) {
    const btn = e.target.closest('.ajax-add-to-cart');
    if (!btn) return;

    e.preventDefault();
    const url = btn.dataset.url;
    if (!url) return;

    // Retour visuel immédiat
    btn.disabled = true;
    const originalHTML = btn.innerHTML;
    btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin text-xs"></i>';

    fetch(url, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCsrfToken(),
            'X-Requested-With': 'XMLHttpRequest',
        },
        body: new URLSearchParams({ quantity: 1 }),
    })
    .then(r => r.json())
    .then(data => {
        // Mettre à jour tous les badges du panier
        document.querySelectorAll('.cart-count').forEach(el => {
            el.textContent = data.count;
            // Petite animation de rebond
            el.style.transform = 'scale(1.4)';
            setTimeout(() => el.style.transform = '', 250);
        });
        showToast(data.message, data.success ? 'success' : 'error');

        // Animation du bouton : coche verte puis retour au statut initial
        btn.innerHTML = '<i class="fa-solid fa-check text-xs"></i>';
        btn.style.background = '#16A34A';
        setTimeout(() => {
            btn.innerHTML = originalHTML;
            btn.style.background = '';
            btn.disabled = false;
        }, 1200);
    })
    .catch(() => {
        showToast('Erreur réseau, veuillez réessayer.', 'error');
        btn.innerHTML = originalHTML;
        btn.disabled = false;
    });
});

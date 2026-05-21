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


// ── AJAX : Gestion du panier sans rechargement ──────────────────────────────
function getCsrfToken() {
    const name = 'csrftoken';
    const cookies = document.cookie.split(';');
    for (let c of cookies) {
        c = c.trim();
        if (c.startsWith(name + '=')) return decodeURIComponent(c.slice(name.length + 1));
    }
    return '';
}

function updateCartBadges(count) {
    document.querySelectorAll('.cart-count').forEach(el => {
        el.textContent = count;
        el.style.transform = 'scale(1.4)';
        setTimeout(() => el.style.transform = '', 250);
    });
}

// 1. Ajout au panier (Formulaire de la page détail)
document.addEventListener('DOMContentLoaded', function() {
    const addToCartForm = document.getElementById('add-to-cart-form');
    if (addToCartForm) {
        addToCartForm.addEventListener('submit', function(e) {
            e.preventDefault();
            const btn = this.querySelector('.ajax-submit-cart');
            const url = this.action;
            const formData = new FormData(this);

            btn.disabled = true;
            const originalHTML = btn.innerHTML;
            btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin text-lg"></i>';

            fetch(url, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCsrfToken(),
                    'X-Requested-With': 'XMLHttpRequest',
                },
                body: formData
            })
            .then(r => r.json())
            .then(data => {
                updateCartBadges(data.count || data.total_items);
                showToast(data.message, data.success ? 'success' : 'error');
                
                btn.innerHTML = '<i class="fa-solid fa-check text-lg"></i>';
                btn.style.background = '#16A34A';
                setTimeout(() => {
                    btn.innerHTML = originalHTML;
                    btn.style.background = '';
                    btn.disabled = false;
                }, 1500);
            })
            .catch(() => {
                showToast('Erreur lors de l\'ajout au panier', 'error');
                btn.innerHTML = originalHTML;
                btn.disabled = false;
            });
        });
    }
});

// 2. Mise à jour des quantités et Suppression (Page Panier)
document.addEventListener('click', function(e) {
    // Boutons +/-
    const qBtn = e.target.closest('.q-minus, .q-plus');
    if (qBtn) {
        const wrap = qBtn.closest('.cart-item-form');
        const input = wrap.querySelector('.q-input');
        const url = wrap.dataset.url;
        
        if (qBtn.classList.contains('q-minus')) input.stepDown();
        else input.stepUp();
        
        updateCartItem(url, input.value, wrap);
    }

    // Suppression
    const removeBtn = e.target.closest('.ajax-remove-from-cart');
    if (removeBtn) {
        const url = removeBtn.dataset.url;
        const itemKey = removeBtn.dataset.itemKey;
        removeCartItem(url, itemKey, removeBtn.closest('.bg-white'));
    }

    // Ajout direct (Cards)
    const addBtn = e.target.closest('.ajax-add-to-cart');
    if (addBtn) {
        e.preventDefault();
        const url = addBtn.dataset.url;
        const originalHTML = addBtn.innerHTML;
        
        addBtn.disabled = true;
        addBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin text-[10px]"></i>';

        fetch(url, {
            method: 'POST',
            headers: {
                'X-CSRFToken': getCsrfToken(),
                'X-Requested-With': 'XMLHttpRequest',
            }
        })
        .then(r => r.json())
        .then(data => {
            updateCartBadges(data.total_items || data.count);
            showToast(data.message, data.success ? 'success' : 'error');
            
            addBtn.innerHTML = '<i class="fa-solid fa-check text-[10px]"></i>';
            setTimeout(() => {
                addBtn.innerHTML = originalHTML;
                addBtn.disabled = false;
            }, 1000);
        })
        .catch(() => {
            showToast('Erreur lors de l\'ajout', 'error');
            addBtn.innerHTML = originalHTML;
            addBtn.disabled = false;
        });
    }
});

function updateCartItem(url, quantity, container) {
    fetch(url, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCsrfToken(),
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: `quantity=${quantity}`
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            updateCartBadges(data.count);
            
            if (data.removed) {
                container.closest('.bg-white').remove();
            } else {
                // Mettre à jour le total de l'article
                const itemTotal = container.closest('.flex-row').querySelector('.item-total');
                if (itemTotal) itemTotal.textContent = data.item_total.toLocaleString() + ' FCFA';
            }
            
            // Mettre à jour le total général
            document.querySelectorAll('.cart-total-price').forEach(el => {
                el.textContent = data.total_price.toLocaleString() + ' FCFA';
            });
            
            if (data.count === 0) location.reload();
        } else {
            showToast(data.message, 'error');
        }
    });
}

function removeCartItem(url, itemKey, element) {
    fetch(url, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCsrfToken(),
            'X-Requested-With': 'XMLHttpRequest',
        }
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            updateCartBadges(data.count);
            document.querySelectorAll('.cart-total-price').forEach(el => {
                el.textContent = data.total_price.toLocaleString() + ' FCFA';
            });
            
            // Animation de sortie
            element.style.transition = 'all 0.5s ease';
            element.style.opacity = '0';
            element.style.transform = 'translateX(20px)';
            setTimeout(() => {
                element.remove();
                if (data.count === 0) location.reload();
            }, 500);
            
            showToast(data.message);
        }
    });
}

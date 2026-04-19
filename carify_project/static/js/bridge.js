/* 
    CARIFY - ELITE MONOLITH BRIDGE (STATE ENGINE)
    Powered by Fetch Architecture | Optimized for Luxury UX
*/

const CarifyBridge = {
    state: null,
    initialized: false,

    init() {
        if (this.initialized) return;
        this.initialized = true;
        
        console.log('--- CARIFY ELITE BRIDGE ACTIVE ---');
        this.applyAnimations();
        this.handleScroll();
        this.syncState();
        
        // Signal readiness
        document.dispatchEvent(new CustomEvent('bridge:ready'));
    },

    applyAnimations() {
        // Elite page reveals
        if (!document.body.classList.contains('revealed')) {
            document.body.style.animation = 'pageReveal 1.0s cubic-bezier(0.25, 1, 0.5, 1) forwards';
            document.body.classList.add('revealed');
        }

        // Auto-inject intersection observers into all layout containers universally
        const newElements = document.querySelectorAll('section, footer, .glass-panel, .shop-card');
        
        if (newElements.length === 0) return;

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    entry.target.classList.add('visible');
                    // Once visible, we can unobserve
                    observer.unobserve(entry.target);
                }
            });
        }, { threshold: 0.1 });

        newElements.forEach(el => {
            if (!el.hasAttribute('data-appear') && !el.closest('.no-appear')) {
                el.setAttribute('data-appear', '');
                observer.observe(el);
            }
        });
    },

    handleScroll() {
        const header = document.querySelector('.site-header');
        if (!header) return;

        const scrollHandler = () => {
            if (window.scrollY > 50) {
                header.classList.add('scrolled');
            } else {
                header.classList.remove('scrolled');
            }
        };

        window.addEventListener('scroll', scrollHandler, { passive: true });
        scrollHandler(); // Initial check
    },

    // --- Core Sync Engine ---
    async syncState() {
        try {
            const data = await this.request('/api/carts/my_cart/');
            this.state = data;
            this.updateUI();
            
            // Dispatch event for other listeners
            document.dispatchEvent(new CustomEvent('cartSynced', { detail: this.state }));
        } catch (err) {
            console.warn('--- PROTOCOL_SYNC_FAILED ---', err);
        }
    },

    updateUI() {
        if (!this.state) return;

        // Update badges
        const badges = document.querySelectorAll('#cartCountBadge, .badge-dot');
        const activeItems = this.state.items ? this.state.items.filter(i => !i.is_saved_for_later) : [];
        const savedItems = this.state.items ? this.state.items.filter(i => i.is_saved_for_later) : [];
        
        const itemCount = activeItems.length;
        
        badges.forEach(badge => {
            badge.textContent = itemCount > 0 ? itemCount : '';
            badge.style.display = itemCount > 0 ? 'flex' : 'none';
        });

        // Update Drawer Content
        const cartItemsContainer = document.getElementById('cartItems');
        const subtotalEl = document.getElementById('cartSubtotal');
        const totalEl = document.getElementById('cartTotal');
        const checkoutBtn = document.getElementById('checkoutBtn');
        const savedItemsSection = document.getElementById('savedItemsSection');
        const savedItemsContainer = document.getElementById('savedItems');

        if (cartItemsContainer) {
            if (activeItems.length === 0) {
                cartItemsContainer.innerHTML = `
                    <div style="text-align: center; padding: 100px 0; opacity: 0.7;">
                        <i class="fas fa-shopping-bag" style="font-size: 2.5rem; margin-bottom: 25px; color: var(--border-elegant);"></i>
                        <p class="font-heading" style="font-size: 0.85rem; letter-spacing: 0.15em; margin-bottom: 15px;">YOUR SELECTION IS EMPTY</p>
                        <p class="font-serif" style="font-size: 0.9rem; color: var(--text-muted); font-style: italic;">Curate your preservation protocol.</p>
                        <a href="/products/" class="btn btn-outline" style="margin-top: 30px; font-size: 0.65rem;">EXPLORE COLLECTION</a>
                    </div>
                `;
            } else {
                cartItemsContainer.innerHTML = activeItems.map(item => {
                    const priceVal = parseFloat(item.get_cost) || 0;
                    const itemImg = (item.product && (item.product.first_image || item.product.image)) || 
                                   (item.service && item.service.image) || 
                                   '/static/img/placeholder.png';
                    const itemName = item.product?.name || item.service?.name || 'Unknown Specimen';
                    
                    return `
                    <div class="cart-item" style="display: flex; gap: 15px; margin-bottom: 25px; padding-bottom: 25px; border-bottom: 1px solid var(--border-subtle);">
                        <div style="width: 80px; height: 100px; background: var(--surface); flex-shrink: 0; overflow: hidden; border-radius: 2px;">
                            <img src="${itemImg}" style="width: 100%; height: 100%; object-fit: cover;">
                        </div>

                        <div style="flex: 1; display: flex; flex-direction: column; justify-content: space-between;">
                            <div>
                                <h4 class="font-heading" style="font-size: 0.85rem; margin-bottom: 5px; color: #fff;">${itemName}</h4>
                                <span style="font-size: 0.65rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.1em;">
                                    ${item.product ? (item.variant ? item.variant.name : 'Standard') : 'RITUAL PROTOCOL'} // QTY: ${item.quantity}
                                </span>
                            </div>
                            <div style="display: flex; justify-content: space-between; align-items: flex-end;">
                                <span class="font-heading copper-text" style="font-size: 1rem;">$${priceVal.toFixed(2)}</span>
                                <div style="display: flex; gap: 10px;">
                                    <button onclick="window.CarifyBridge.toggleSavedItem(${item.id})" style="background: none; border: none; color: var(--text-elegant); font-size: 0.6rem; cursor: pointer; text-decoration: underline; letter-spacing: 0.1em; transition: 0.3s;">SAVE</button>
                                    <button onclick="window.CarifyBridge.removeItem(${item.id})" style="background: none; border: none; color: var(--text-muted); font-size: 0.6rem; cursor: pointer; text-decoration: underline; letter-spacing: 0.1em; transition: 0.3s;">REMOVE</button>
                                </div>
                            </div>
                        </div>
                    </div>
                `}).join('');
            }
        }

        if (savedItemsSection && savedItemsContainer) {
            if (savedItems.length > 0) {
                savedItemsSection.style.display = 'block';
                savedItemsContainer.innerHTML = savedItems.map(item => {
                    const savedImg = (item.product && (item.product.first_image || item.product.image)) || 
                                    (item.service && item.service.image) || 
                                    '/static/img/placeholder.png';
                    const savedName = item.product?.name || item.service?.name || 'Archived Specimen';
                    
                    return `
                    <div class="saved-item" style="display: flex; gap: 10px; margin-bottom: 15px; opacity: 0.6; transition: 0.3s; align-items: center;">
                        <img src="${savedImg}" style="width: 50px; height: 60px; object-fit: cover; border-radius: 2px;">
                        <div style="flex: 1;">
                            <h4 class="font-heading" style="font-size: 0.75rem; color: #fff;">${savedName}</h4>
                            <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 5px;">
                                <button onclick="window.CarifyBridge.toggleSavedItem(${item.id})" class="copper-text" style="background: none; border: none; font-size: 0.6rem; cursor: pointer; letter-spacing: 0.1em; padding: 0;">ACTIVATE</button>
                                <button onclick="window.CarifyBridge.removeItem(${item.id})" style="background: none; border: none; color: var(--text-muted); font-size: 0.6rem; cursor: pointer;">REMOVE</button>
                            </div>
                        </div>
                    </div>
                `}).join('');
            } else {
                savedItemsSection.style.display = 'none';
            }
        }

        const totalValue = parseFloat(this.state.get_total_price || 0);
        if (subtotalEl) subtotalEl.textContent = `$${totalValue.toFixed(2)}`;
        if (totalEl) totalEl.textContent = `$${totalValue.toFixed(2)}`;
        
        if (checkoutBtn) {
            if (activeItems.length === 0) {
                checkoutBtn.disabled = true;
                checkoutBtn.style.opacity = '0.5';
            } else {
                checkoutBtn.disabled = false;
                checkoutBtn.style.opacity = '1';
                checkoutBtn.onclick = () => window.location.href = '/checkout/initialize/';
            }
        }

        this.applyAnimations();
    },

    // --- Action Handlers ---
    async addItemToCart(id, type = 'product', quantity = 1, variantId = null) {
        try {
            const payload = { quantity };
            if (type === 'product') {
                payload.product_id = id;
                if (variantId) payload.variant_id = variantId;
            } else if (type === 'service') {
                payload.service_id = id;
            }

            const data = await this.request('/api/cart-items/', {
                method: 'POST',
                body: JSON.stringify(payload)
            });

            await this.syncState();
            
            // Auto-open drawer
            const drawer = document.getElementById('cartDrawer');
            const overlay = document.getElementById('globalOverlay');
            if (drawer) drawer.classList.add('active');
            if (overlay) overlay.classList.add('active');
            document.body.style.overflow = 'hidden';

            return data;
        } catch (err) {
            console.error('--- ACQUISITION_FAILED ---', err);
            alert('ACQUISITION ERROR: Failed to sync with portfolio.');
        }
    },

    async removeItem(itemId) {
        try {
            await this.request(`/api/cart-items/${itemId}/`, {
                method: 'DELETE'
            });
            await this.syncState();
        } catch (err) {
            console.error('--- REMOVAL_FAILED ---', err);
        }
    },

    async toggleSavedItem(itemId) {
        try {
            await this.request(`/api/cart-items/${itemId}/toggle_saved/`, {
                method: 'POST'
            });
            await this.syncState();
        } catch (err) {
            console.error('--- SAVE_TOGGLE_FAILED ---', err);
        }
    },

    // --- Helpers ---
    async request(url, options = {}) {
        const csrfToken = document.querySelector('[name=csrfmiddlewaretoken]')?.value;
        const defaultHeaders = {
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        };

        const response = await fetch(url, {
            ...options,
            headers: { ...defaultHeaders, ...options.headers }
        });

        if (response.status === 204) return null;
        if (!response.ok) throw new Error(`HTTP Error: ${response.status}`);
        
        const text = await response.text();
        return text ? JSON.parse(text) : {};
    }
};

window.CarifyBridge = CarifyBridge;

// Initialize on DOM ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => CarifyBridge.init());
} else {
    CarifyBridge.init();
}

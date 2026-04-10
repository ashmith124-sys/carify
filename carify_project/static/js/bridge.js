/* 
    CARIFY - ELITE MONOLITH BRIDGE (STATE ENGINE)
    Powered by Fetch Architecture | Optimized for Luxury UX
*/

const CarifyBridge = {
    state: {
        cartCount: 0,
        isAuthed: false
    },

    init() {
        console.log('--- CARIFY ELITE BRIDGE ACTIVE ---');
        this.applyAnimations();
        this.handleScroll();
        this.syncState();
    },

    applyAnimations() {
        // Trigger Universal Page Opening Animation
        document.body.style.animation = 'pageReveal 1.0s cubic-bezier(0.25, 1, 0.5, 1) forwards';

        // Auto-inject intersection observers into all layout containers universally
        document.querySelectorAll('section, footer, .glass-panel, .shop-card').forEach(el => {
            if(!el.hasAttribute('data-appear') && !el.closest('.no-appear')) {
                el.setAttribute('data-appear', '');
            }
        });

        const observer = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if(entry.isIntersecting) {
                    entry.target.classList.add('visible');
                    
                    // Advanced Staggering for Child Elements
                    if(entry.target.dataset.stagger) {
                        const children = entry.target.querySelectorAll('.stagger-item');
                        children.forEach((c, idx) => {
                            setTimeout(() => {
                                c.classList.add('visible');
                            }, idx * 100);
                        });
                    }
                }
            });
        }, { threshold: 0.05 });

        document.querySelectorAll('[data-appear]').forEach(el => observer.observe(el));
    },

    handleScroll() {
        const header = document.querySelector('.site-header');
        if(!header) return;
        window.addEventListener('scroll', () => {
            if(window.scrollY > 40) header.classList.add('scrolled');
            else header.classList.remove('scrolled');
        }, { passive: true });
    },

    async syncState() {
        try {
            const data = await this.request('/api/carts/my_cart/');
            if(data && data.items) {
                this.state.cartCount = data.items.length;
                this.state.items = data.items;
                this.state.total = data.get_total_price;
                this.updateUI();
            }
        } catch (err) {
            console.warn('--- PROTOCOL_SYNC_FAILED ---', err);
        }
    },

    updateUI() {
        const badge = document.getElementById('cartCountBadge') || document.getElementById('cartBadge');
        if(badge) {
            badge.innerText = this.state.cartCount;
            badge.style.display = this.state.cartCount > 0 ? 'flex' : 'none';
        }

        // DYNAMIC CART RENDERING
        const cartItemsContainer = document.getElementById('cartItems');
        const cartSubtotal = document.getElementById('cartSubtotal');
        const cartTotal = document.getElementById('cartTotal');
        const checkoutBtn = document.getElementById('checkoutBtn');

        const savedItemsContainer = document.getElementById('savedItems');
        const savedItemsSection = document.getElementById('savedItemsSection');

        if(cartItemsContainer && this.state.items) {
            const activeItems = this.state.items.filter(i => !i.is_saved_for_later);
            const savedItems = this.state.items.filter(i => i.is_saved_for_later);
            
            // Render Active
            if(activeItems.length === 0) {
                cartItemsContainer.innerHTML = `
        <div style="text-align: center; padding: 100px 0; opacity: 0.7;">
            <i class="fas fa-shopping-bag" style="font-size: 2.5rem; margin-bottom: 25px; color: var(--border-elegant);"></i>
            <p class="font-heading" style="font-size: 0.85rem; letter-spacing: 0.15em; margin-bottom: 15px;">YOUR SELECTION IS EMPTY</p>
            <p class="font-serif" style="font-size: 0.9rem; color: var(--text-muted); font-style: italic;">Curate your preservation protocol.</p>
            <a href="/products/" class="btn btn-outline" style="margin-top: 30px; font-size: 0.65rem;">EXPLORE COLLECTION</a>
        </div>`;
            } else {
                cartItemsContainer.innerHTML = activeItems.map(item => {
                    const priceVal = parseFloat(item.get_cost) || 0;
                    return `
                    <div style="display: flex; gap: 15px; margin-bottom: 25px; padding-bottom: 25px; border-bottom: 1px solid var(--border-subtle);">
                        <div style="width: 80px; height: 100px; background: var(--surface); flex-shrink: 0; overflow: hidden; border-radius: 2px;">
                            <img src="${item.product.first_image || (item.product.image ? item.product.image : 'https://images.unsplash.com/photo-1487754180451-c456f719a1fc?auto=format&fit=crop&q=80&w=200')}" style="width: 100%; height: 100%; object-fit: cover;">
                        </div>
                        <div style="flex: 1; display: flex; flex-direction: column; justify-content: space-between;">
                            <div>
                                <h4 class="font-heading" style="font-size: 0.85rem; margin-bottom: 5px;">${item.product.name}</h4>
                                <span style="font-size: 0.65rem; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.1em;">${item.variant ? item.variant.name : 'Standard'} // QTY: ${item.quantity}</span>
                            </div>
                            <div style="display: flex; justify-content: space-between; align-items: flex-end;">
                                <span class="font-heading copper-text" style="font-size: 1rem;">$${priceVal.toFixed(2)}</span>
                                <div>
                                    <button onclick="window.CarifyBridge.toggleSavedItem(${item.id})" style="background: none; border: none; color: var(--text-elegant); font-size: 0.6rem; cursor: pointer; text-decoration: underline; letter-spacing: 0.1em; transition: 0.3s; margin-right: 10px;" onmouseover="this.style.color='var(--copper)'" onmouseout="this.style.color='var(--text-elegant)'">SAVE FOR LATER</button>
                                    <button onclick="window.CarifyBridge.removeItem(${item.id})" style="background: none; border: none; color: var(--text-muted); font-size: 0.6rem; cursor: pointer; text-decoration: underline; letter-spacing: 0.1em; transition: 0.3s;" onmouseover="this.style.color='var(--bronze)'" onmouseout="this.style.color='var(--text-muted)'">REMOVE</button>
                                </div>
                            </div>
                        </div>
                    </div>
                `}).join('');
            }
            
            // Render Saved
            if (savedItemsSection && savedItemsContainer) {
                if (savedItems.length > 0) {
                    savedItemsSection.style.display = 'block';
                    savedItemsContainer.innerHTML = savedItems.map(item => `
                        <div style="display: flex; gap: 10px; margin-bottom: 15px; opacity: 0.6; transition: 0.3s;" onmouseover="this.style.opacity=1" onmouseout="this.style.opacity=0.6">
                            <img src="${item.product.first_image || (item.product.image ? item.product.image : 'https://images.unsplash.com/photo-1487754180451-c456f719a1fc?auto=format&fit=crop&q=80&w=200')}" style="width: 50px; height: 60px; object-fit: cover; border-radius: 2px;">
                            <div style="flex: 1;">
                                <h4 class="font-heading" style="font-size: 0.75rem;">${item.product.name}</h4>
                                <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 5px;">
                                    <button onclick="window.CarifyBridge.toggleSavedItem(${item.id})" class="copper-text" style="background: none; border: none; font-size: 0.6rem; cursor: pointer; letter-spacing: 0.1em; padding: 0;">MOVE TO CART</button>
                                    <button onclick="window.CarifyBridge.removeItem(${item.id})" style="background: none; border: none; color: var(--text-muted); font-size: 0.6rem; cursor: pointer;">REMOVE</button>
                                </div>
                            </div>
                        </div>
                    `).join('');
                } else {
                    savedItemsSection.style.display = 'none';
                }
            }
        }

        if(cartSubtotal && cartTotal && typeof this.state.total !== 'undefined') {
            const t = parseFloat(this.state.total) || 0;
            cartSubtotal.innerText = '$' + t.toFixed(2);
            cartTotal.innerText = '$' + t.toFixed(2);
        }
        
        if (checkoutBtn) {
            const activeItems = this.state.items ? this.state.items.filter(i => !i.is_saved_for_later) : [];
            if (activeItems.length === 0) {
                checkoutBtn.disabled = true;
                checkoutBtn.style.opacity = '0.5';
            } else {
                checkoutBtn.disabled = false;
                checkoutBtn.style.opacity = '1';
                checkoutBtn.onclick = () => window.location.href = '/checkout/initialize/';
            }
        }
    },

    async removeItem(itemId) {
        try {
            await this.request('/api/cart-items/' + itemId + '/', { method: 'DELETE' });
            this.syncState();
        } catch(err) {
            console.error('Failed to remove item', err);
        }
    },

    async toggleSavedItem(itemId) {
        try {
            await this.request('/api/cart-items/' + itemId + '/toggle_saved/', { method: 'POST' });
            this.syncState();
        } catch(err) {
            console.error('Failed to toggle saved state', err);
        }
    },

    async request(url, options = {}) {
        const defaultHeaders = {
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value,
            'Content-Type': 'application/json'
        };

        const response = await fetch(url, {
            ...options,
            headers: { ...defaultHeaders, ...options.headers }
        });
        if(!response.ok) throw new Error(`Status: ${response.status}`);
        return await response.json();
    }
};

window.CarifyBridge = CarifyBridge;
document.addEventListener('DOMContentLoaded', () => CarifyBridge.init());

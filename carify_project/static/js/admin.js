// Custom admin JavaScript for Carify
document.addEventListener('DOMContentLoaded', function() {
    // Add smooth transitions
    const cards = document.querySelectorAll('.card');
    cards.forEach(card => {
        card.style.transition = 'all 0.3s ease';
    });

    // Add loading animation to buttons
    const buttons = document.querySelectorAll('.btn');
    buttons.forEach(button => {
        button.addEventListener('click', function() {
            if (!this.classList.contains('loading')) {
                this.classList.add('loading');
                this.innerHTML = '<span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>Loading...';

                // Remove loading state after 2 seconds (for demo)
                setTimeout(() => {
                    this.classList.remove('loading');
                    this.innerHTML = this.textContent;
                }, 2000);
            }
        });
    });

    // Add confirmation to delete actions
    const deleteButtons = document.querySelectorAll('a[href*="delete"]');
    deleteButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            if (!confirm('Are you sure you want to delete this item?')) {
                e.preventDefault();
            }
        });
    });
});
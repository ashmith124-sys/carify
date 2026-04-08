// CARIFY Home Page JavaScript

document.addEventListener('DOMContentLoaded', function() {
    // Scroll to Top Button
    const scrollTopBtn = document.getElementById('scrollTopBtn');
    
    // Show/hide scroll to top button
    window.addEventListener('scroll', function() {
        if (window.pageYOffset > 300) {
            scrollTopBtn.classList.add('show');
        } else {
            scrollTopBtn.classList.remove('show');
        }
    });
    
    // Scroll to top functionality
    scrollTopBtn.addEventListener('click', function() {
        window.scrollTo({
            top: 0,
            behavior: 'smooth'
        });
    });
    
    // Smooth scrolling for navigation links
    const navLinks = document.querySelectorAll('.navbar-nav .nav-link[href^="#"]');
    
    navLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            
            const targetId = this.getAttribute('href');
            const targetSection = document.querySelector(targetId);
            
            if (targetSection) {
                const offsetTop = targetSection.offsetTop - 70; // Account for fixed navbar
                
                window.scrollTo({
                    top: offsetTop,
                    behavior: 'smooth'
                });
            }
        });
    });
    
    // Product card hover effects
    const productCards = document.querySelectorAll('.product-card');
    
    productCards.forEach(card => {
        card.addEventListener('mouseenter', function() {
            this.style.transform = 'translateY(-10px) scale(1.02)';
        });
        
        card.addEventListener('mouseleave', function() {
            this.style.transform = 'translateY(0) scale(1)';
        });
    });
    
    // Tool card click effects
    const toolCards = document.querySelectorAll('.tool-card');
    
    toolCards.forEach(card => {
        card.addEventListener('click', function() {
            // Add click animation
            this.style.transform = 'translateY(-5px) scale(0.95)';
            
            setTimeout(() => {
                this.style.transform = 'translateY(0) scale(1)';
            }, 150);
            
            // Here you could add navigation to specific product categories
            console.log('Tool card clicked:', this.querySelector('p').textContent);
        });
    });
    
    // Search functionality
    const searchInput = document.querySelector('.search-box input');
    
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const searchTerm = this.value.toLowerCase();
            const productCards = document.querySelectorAll('.product-card');
            
            productCards.forEach(card => {
                const title = card.querySelector('.product-title').textContent.toLowerCase();
                const description = card.querySelector('.product-description').textContent.toLowerCase();
                
                if (title.includes(searchTerm) || description.includes(searchTerm)) {
                    card.style.display = 'block';
                } else {
                    card.style.display = 'none';
                }
            });
        });
    }
    
    // Add to cart button effects
    const addToCartButtons = document.querySelectorAll('.btn-add-cart');
    
    addToCartButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Add click animation
            this.style.transform = 'scale(0.95)';
            this.textContent = 'Added!';
            this.style.backgroundColor = '#28a745';
            
            setTimeout(() => {
                this.style.transform = 'scale(1)';
                this.textContent = 'ADD CART';
                this.style.backgroundColor = '';
            }, 1000);
            
            // Here you could add actual cart functionality
            console.log('Product added to cart');
        });
    });
    
    // Quick view button functionality
    const quickViewButtons = document.querySelectorAll('.btn-quick-view');
    
    quickViewButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            
            // Here you could open a modal with product details
            console.log('Quick view clicked');
        });
    });
    
    // Pagination dots functionality
    const paginationDots = document.querySelectorAll('.dot');
    
    paginationDots.forEach((dot, index) => {
        dot.addEventListener('click', function() {
            // Remove active class from all dots
            paginationDots.forEach(d => d.classList.remove('active'));
            
            // Add active class to clicked dot
            this.classList.add('active');
            
            // Here you could implement pagination logic
            console.log('Pagination dot clicked:', index + 1);
        });
    });
    
    // View all products button
    const viewAllBtn = document.querySelector('.btn-view-all');
    
    if (viewAllBtn) {
        viewAllBtn.addEventListener('click', function() {
            // Navigate to products page
            window.location.href = '/products/';
        });
    }
    
    // Shop bestsellers button
    const shopBestsellersBtn = document.querySelector('.btn-shop-bestsellers');
    
    if (shopBestsellersBtn) {
        shopBestsellersBtn.addEventListener('click', function() {
            // Navigate to bestsellers section or products page
            window.location.href = '/products/?category=bestsellers';
        });
    }
    
    // Navbar background on scroll
    const navbar = document.querySelector('.navbar');
    
    window.addEventListener('scroll', function() {
        if (window.pageYOffset > 50) {
            navbar.style.background = 'rgba(26, 26, 26, 0.98)';
        } else {
            navbar.style.background = 'rgba(26, 26, 26, 0.95)';
        }
    });
    
    // Animate elements on scroll (simple implementation)
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    
    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = '1';
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);
    
    // Observe elements for animation
    const animateElements = document.querySelectorAll('.tool-card, .product-card, .bestseller-card');
    
    animateElements.forEach(element => {
        element.style.opacity = '0';
        element.style.transform = 'translateY(30px)';
        element.style.transition = 'opacity 0.6s ease, transform 0.6s ease';
        observer.observe(element);
    });
    
    // Form validation for any forms (if added later)
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            // Basic form validation
            const requiredFields = form.querySelectorAll('[required]');
            let isValid = true;
            
            requiredFields.forEach(field => {
                if (!field.value.trim()) {
                    field.style.borderColor = '#dc3545';
                    isValid = false;
                } else {
                    field.style.borderColor = '';
                }
            });
            
            if (!isValid) {
                e.preventDefault();
                alert('Please fill in all required fields.');
            }
        });
    });
    
    // Initialize any Bootstrap components that need JavaScript
    // Bootstrap 5 handles most things automatically, but we can add custom behavior
    
    console.log('CARIFY home page JavaScript loaded successfully!');
});
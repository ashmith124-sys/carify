# Carify: Performance Hardware Marketplace

Carify is a premium, multi-vendor e-commerce platform built for the GCC region, focused on automotive parts and hardware. The platform features a high-performance "Industrial Tech" aesthetic.

## 🚀 Features
- **Modern UI**: Dark mode with high-contrast vibrant orange accents.
- **Storefront**: Glassmorphic search, interactive product grids, and responsive layouts.
- **Seller Dashboard**: "CARIFY COMMAND" terminal for managing inventory and analytics.
- **Payment Integration**: Seamless Stripe checkout integration.
- **Authentication**: Unified sign-in/signup flow using `django-allauth`.

## 🛠️ Setup for Coworkers

### 1. Clone & Environment
```bash
git clone https://github.com/ashmith124-sys/carify.git
cd carify
python -m venv env
source env/bin/activate  # On Windows: env\Scripts\activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Initialize Database
```bash
cd carify_project
python manage.py migrate
python manage.py createsuperuser  # Optional: for admin access
```

### 4. Stripe Configuration
Create a `.env` file (or set these in settings.py) with your Stripe test keys:
```python
STRIPE_PUBLIC_KEY = 'pk_test_...'
STRIPE_SECRET_KEY = 'sk_test_...'
```

### 5. Run Server
```bash
python manage.py runserver
```

## 🎨 Brand Guidelines
- **Background**: `#231F20` (Rich Charcoal)
- **Accents**: `#F3811F` (Electric Orange)
- **Fonts**: Space Grotesk (Headings), Inter (Body)

---
Developed by the Carify Tech Team.

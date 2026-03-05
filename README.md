# 💎 The POPSHOP.KE - Django E-commerce Website

A lightweight, elegant jewellery e-commerce website with WhatsApp checkout integration.

## ✨ Features

- 🎨 Elegant pastel pink theme
- 🧭 Fixed navigation bar with logo
- 📱 Mobile-first responsive design with hamburger menu
- 🛒 Session-based cart system
- 💬 WhatsApp checkout (no payment gateway)
- ⚡ Fast and lightweight
- 🔧 Easy to manage via Django admin
- ✨ Beautiful hero section with animations

## 🚀 Quick Start

### 1. Add Your Logo

Save your logo image as `static/images/logo.png`
- Recommended size: 400-600px width
- Format: PNG with transparent background

### 2. Create Superuser

```bash
python manage.py createsuperuser
```

### 2. Create Superuser

```bash
python manage.py createsuperuser
```

### 3. Run Development Server

```bash
python manage.py runserver
```

### 4. Access the Site

- **Website**: http://127.0.0.1:8000/
- **Admin Panel**: http://127.0.0.1:8000/admin/

## 📋 Admin Setup

1. Login to admin panel
2. Add Categories (e.g., Necklaces, Earrings, Bracelets, Rings)
3. Add Products with:
   - Name
   - Category
   - Short description
   - Full description
   - Price (in Ksh)
   - Image
   - Availability status

## 🛍️ How It Works

1. **Browse**: Customers browse products by category
2. **Add to Cart**: Click "Add to Cart" on any product
3. **View Cart**: Click cart icon (bottom right)
4. **Checkout**: Fill in name, phone, address
5. **WhatsApp**: Order details sent to WhatsApp (0717147007)

## 🎨 Theme Colors

- Pastel Pink: `#F8C8DC`
- White: `#FFFFFF`
- Black: `#000000`

## 📱 WhatsApp Integration

Orders are sent to: **+254 717 147 007**

Message format includes:
- Customer details
- Order items with quantities
- Total amount
- Delivery notes

## 🔧 Tech Stack

- Django 6.0
- SQLite Database
- Django Templates
- Vanilla JavaScript
- CSS3

## 📁 Project Structure

```
jewellery_site/
├── shop/               # Main app
│   ├── models.py      # Category & Product models
│   ├── views.py       # Cart & checkout logic
│   ├── admin.py       # Admin configuration
│   └── templates/     # HTML templates
├── static/            # CSS, JS, images
├── media/             # Uploaded product images
└── manage.py
```

## 🎯 Key Features

- ✅ No payment gateway needed
- ✅ Simple WhatsApp checkout
- ✅ Session-based cart (no login required)
- ✅ Mobile responsive
- ✅ Easy product management
- ✅ Category filtering
- ✅ Product detail modals
- ✅ Quantity controls

## 📝 Notes

- Images are stored in `media/products/`
- Cart data stored in Django sessions
- No order database (orders go to WhatsApp)
- Perfect for small jewellery businesses

## 🌟 Future Enhancements (Optional)

- Order history in admin
- Customer accounts
- Wishlist feature
- Product reviews
- Multiple images per product
- Search functionality

---

Built with ❤️ for The POPSHOP.KE

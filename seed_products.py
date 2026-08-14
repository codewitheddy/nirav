#!/usr/bin/env python
"""
Seed 100 jewelry products distributed across all categories.
Distribute evenly: ~17 products per category
"""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jewellery_site.settings')
django.setup()

from shop.models import Category, Product
from decimal import Decimal
import random

# Sample product data
JEWELRY_PRODUCTS = {
    'Necklaces': [
        {'name': 'Classic Gold Chain', 'desc': 'Elegant 24K gold plated chain necklace'},
        {'name': 'Pearl Pendant', 'desc': 'Beautiful freshwater pearl on delicate chain'},
        {'name': 'Diamond Solitaire', 'desc': 'Stunning solitaire diamond pendant'},
        {'name': 'Rose Gold Locket', 'desc': 'Vintage-inspired rose gold locket'},
        {'name': 'Turquoise Stone Necklace', 'desc': 'Boho turquoise pendant necklace'},
        {'name': 'Silver Snake Chain', 'desc': 'Sleek silver snake chain necklace'},
        {'name': 'Emerald Green Pendant', 'desc': 'Deep emerald gemstone pendant'},
        {'name': 'Minimalist Bar Necklace', 'desc': 'Simple gold bar pendant'},
        {'name': 'Sapphire Halo Necklace', 'desc': 'Blue sapphire with diamond halo'},
        {'name': 'Ruby Heart Pendant', 'desc': 'Red ruby heart-shaped pendant'},
        {'name': 'Amethyst Geode Necklace', 'desc': 'Purple amethyst geode slice pendant'},
        {'name': 'Moonstone Mystique', 'desc': 'Iridescent moonstone pendant'},
        {'name': 'Citrine Sun', 'desc': 'Golden citrine sunburst pendant'},
        {'name': 'Labradorite Flash', 'desc': 'Labradorite with blue flash'},
        {'name': 'Black Onyx Cross', 'desc': 'Cross pendant with black onyx'},
        {'name': 'Garnet Deep Red', 'desc': 'Deep red garnet gemstone pendant'},
        {'name': 'Topaz Ocean Blue', 'desc': 'Bright blue topaz pendant'},
    ],
    'Earrings': [
        {'name': 'Stud Pearl Earrings', 'desc': 'Classic pearl stud earrings'},
        {'name': 'Diamond Drop Earrings', 'desc': 'Elegant diamond drop earrings'},
        {'name': 'Gold Hoop Earrings', 'desc': 'Timeless gold hoop earrings'},
        {'name': 'Crystal Chandelier', 'desc': 'Sparkly crystal chandelier earrings'},
        {'name': 'Turquoise Tribal', 'desc': 'Boho turquoise tribal earrings'},
        {'name': 'Rose Gold Feather', 'desc': 'Rose gold feather-shaped earrings'},
        {'name': 'Sapphire Blue Studs', 'desc': 'Blue sapphire stud earrings'},
        {'name': 'Emerald Leaf', 'desc': 'Green emerald leaf earrings'},
        {'name': 'Ruby Red Drops', 'desc': 'Deep red ruby drop earrings'},
        {'name': 'Amethyst Purple Studs', 'desc': 'Purple amethyst stud earrings'},
        {'name': 'Moonstone Glow', 'desc': 'Glowing moonstone earrings'},
        {'name': 'Citrine Golden Drops', 'desc': 'Golden citrine drop earrings'},
        {'name': 'Onyx Black Studs', 'desc': 'Classic black onyx studs'},
        {'name': 'Garnet Wine Drops', 'desc': 'Wine-red garnet drop earrings'},
        {'name': 'Topaz Blue Dangles', 'desc': 'Blue topaz dangle earrings'},
        {'name': 'Silver Filigree', 'desc': 'Delicate silver filigree earrings'},
        {'name': 'Gold Infinity', 'desc': 'Infinity symbol gold earrings'},
    ],
    'Bracelets': [
        {'name': 'Gold Bangle Bracelet', 'desc': 'Classic gold bangle bracelet'},
        {'name': 'Diamond Tennis Bracelet', 'desc': 'Sparkling diamond tennis bracelet'},
        {'name': 'Pearl Strand Bracelet', 'desc': 'Elegant pearl strand bracelet'},
        {'name': 'Rose Gold Link', 'desc': 'Rose gold link chain bracelet'},
        {'name': 'Turquoise Beaded', 'desc': 'Colorful turquoise beaded bracelet'},
        {'name': 'Silver Charm', 'desc': 'Silver charm bracelet with charms'},
        {'name': 'Sapphire Gemstone', 'desc': 'Blue sapphire gemstone bracelet'},
        {'name': 'Emerald Green Beads', 'desc': 'Emerald green beaded bracelet'},
        {'name': 'Ruby Red Link', 'desc': 'Ruby red link bracelet'},
        {'name': 'Amethyst Healing', 'desc': 'Purple amethyst healing stone bracelet'},
        {'name': 'Moonstone Luminous', 'desc': 'Moonstone bead bracelet'},
        {'name': 'Citrine Abundance', 'desc': 'Golden citrine beaded bracelet'},
        {'name': 'Onyx Protection', 'desc': 'Black onyx protection bracelet'},
        {'name': 'Garnet Energy', 'desc': 'Deep red garnet energy bracelet'},
        {'name': 'Topaz Calm', 'desc': 'Blue topaz calming bracelet'},
        {'name': 'Gold Mesh Band', 'desc': 'Flexible gold mesh band bracelet'},
        {'name': 'Silver Adjustable', 'desc': 'Adjustable silver bracelet'},
    ],
    'Rings': [
        {'name': 'Solitaire Diamond Ring', 'desc': 'Classic diamond solitaire ring'},
        {'name': 'Gold Band Ring', 'desc': 'Simple gold band ring'},
        {'name': 'Pearl Ring', 'desc': 'Elegant pearl ring'},
        {'name': 'Rose Gold Halo', 'desc': 'Rose gold halo engagement ring'},
        {'name': 'Turquoise Boho Ring', 'desc': 'Boho turquoise statement ring'},
        {'name': 'Silver Minimalist', 'desc': 'Minimalist silver ring'},
        {'name': 'Sapphire Blue Ring', 'desc': 'Blue sapphire gemstone ring'},
        {'name': 'Emerald Green Ring', 'desc': 'Emerald green gemstone ring'},
        {'name': 'Ruby Red Ring', 'desc': 'Deep red ruby gemstone ring'},
        {'name': 'Amethyst Purple Ring', 'desc': 'Purple amethyst ring'},
        {'name': 'Moonstone Mystique Ring', 'desc': 'Moonstone mystical ring'},
        {'name': 'Citrine Golden Ring', 'desc': 'Golden citrine ring'},
        {'name': 'Onyx Black Ring', 'desc': 'Classic black onyx ring'},
        {'name': 'Garnet Deep Ring', 'desc': 'Deep red garnet ring'},
        {'name': 'Topaz Ocean Ring', 'desc': 'Blue topaz ocean ring'},
        {'name': 'Silver Filigree Ring', 'desc': 'Delicate silver filigree ring'},
        {'name': 'Gold Twisted Band', 'desc': 'Twisted gold band ring'},
    ],
    'Anklets': [
        {'name': 'Gold Ankle Chain', 'desc': 'Delicate gold ankle chain'},
        {'name': 'Pearl Anklet', 'desc': 'Elegant pearl anklet'},
        {'name': 'Diamond Anklet', 'desc': 'Sparkly diamond anklet'},
        {'name': 'Rose Gold Beaded', 'desc': 'Rose gold beaded anklet'},
        {'name': 'Turquoise Beach', 'desc': 'Turquoise beach anklet'},
        {'name': 'Silver Charm Anklet', 'desc': 'Silver charm anklet'},
        {'name': 'Sapphire Anklet', 'desc': 'Blue sapphire anklet'},
        {'name': 'Emerald Green Anklet', 'desc': 'Green emerald anklet'},
        {'name': 'Ruby Red Anklet', 'desc': 'Red ruby anklet'},
        {'name': 'Amethyst Purple Anklet', 'desc': 'Purple amethyst anklet'},
        {'name': 'Moonstone Glow Anklet', 'desc': 'Glowing moonstone anklet'},
        {'name': 'Citrine Golden Anklet', 'desc': 'Golden citrine anklet'},
        {'name': 'Onyx Black Anklet', 'desc': 'Black onyx anklet'},
        {'name': 'Garnet Deep Anklet', 'desc': 'Deep red garnet anklet'},
        {'name': 'Topaz Blue Anklet', 'desc': 'Blue topaz anklet'},
        {'name': 'Silver Link Anklet', 'desc': 'Silver link chain anklet'},
        {'name': 'Gold Infinity Anklet', 'desc': 'Gold infinity symbol anklet'},
    ],
    'Waist Chains': [
        {'name': 'Gold Body Chain', 'desc': 'Elegant gold body chain'},
        {'name': 'Pearl Waist Chain', 'desc': 'Luxurious pearl waist chain'},
        {'name': 'Diamond Waist Belt', 'desc': 'Sparkling diamond waist belt'},
        {'name': 'Rose Gold Body Jewelry', 'desc': 'Rose gold body jewelry'},
        {'name': 'Turquoise Tribal Chain', 'desc': 'Boho turquoise waist chain'},
        {'name': 'Silver Statement Chain', 'desc': 'Statement silver waist chain'},
        {'name': 'Sapphire Luxury Chain', 'desc': 'Luxury sapphire waist chain'},
        {'name': 'Emerald Green Body', 'desc': 'Emerald green body chain'},
        {'name': 'Ruby Goddess Chain', 'desc': 'Goddess ruby waist chain'},
        {'name': 'Amethyst Mystical Chain', 'desc': 'Mystical amethyst body chain'},
        {'name': 'Moonstone Ethereal', 'desc': 'Ethereal moonstone body chain'},
        {'name': 'Citrine Golden Body', 'desc': 'Golden citrine body chain'},
        {'name': 'Onyx Bold Chain', 'desc': 'Bold black onyx chain'},
        {'name': 'Garnet Passionate', 'desc': 'Passionate garnet waist chain'},
        {'name': 'Topaz Ocean Body', 'desc': 'Ocean blue topaz body chain'},
        {'name': 'Silver Draped Chain', 'desc': 'Draped silver body chain'},
        {'name': 'Gold Luxe Waist', 'desc': 'Luxe gold waist jewelry'},
    ],
}

def seed_products():
    """Seed 100 products across categories"""
    print("🌱 Starting product seeding...")
    
    # Get all valid categories
    categories = Category.objects.exclude(name='Ringss').all()  # Exclude duplicate
    
    total_products_created = 0
    
    for category in categories:
        products_for_category = JEWELRY_PRODUCTS.get(category.name, [])
        
        if not products_for_category:
            print(f"⚠️  No products defined for {category.name}")
            continue
        
        created_count = 0
        for product_data in products_for_category:
            # Skip if product already exists
            if Product.objects.filter(name=product_data['name']).exists():
                print(f"  ⏭️  Skipped (exists): {product_data['name']}")
                continue
            
            # Generate random price between 500 and 5000 KES
            price = Decimal(random.randint(500, 5000))
            
            # 30% chance of being on sale
            sale_price = None
            discount_percent = None
            if random.random() < 0.3:
                discount_percent = random.choice([10, 15, 20, 25, 30])
                sale_price = price * (Decimal(100 - discount_percent) / 100)
            
            product = Product.objects.create(
                name=product_data['name'],
                category=category,
                short_description=product_data['desc'][:150],
                description=product_data['desc'],
                price=price,
                is_available=True,
                is_featured=random.random() < 0.2,  # 20% featured
                stock=random.randint(5, 50)
            )
            
            # Add sale info if applicable
            if sale_price:
                product.sale_info = {
                    'sale_price': str(sale_price),
                    'original_price': str(price),
                    'discount_percent': discount_percent
                }
                product.save()
            
            print(f"  ✓ Created: {product_data['name']} (Ksh {price})")
            created_count += 1
            total_products_created += 1
        
        print(f"📦 {category.name}: {created_count} products added\n")
    
    print(f"✅ Seeding complete! Total products created: {total_products_created}")

if __name__ == '__main__':
    seed_products()

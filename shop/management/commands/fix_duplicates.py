"""
Management command to fix duplicate product and category names before migration
"""
from django.core.management.base import BaseCommand
from django.db.models import Count
from shop.models import Product, Category


class Command(BaseCommand):
    help = 'Fix duplicate product and category names by renaming them'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Checking for duplicate names...'))
        
        # Fix duplicate products
        duplicate_products = Product.objects.values('name').annotate(
            count=Count('id')
        ).filter(count__gt=1)
        
        if duplicate_products:
            self.stdout.write(self.style.WARNING(f'Found {len(duplicate_products)} duplicate product names'))
            
            for dup in duplicate_products:
                name = dup['name']
                products = Product.objects.filter(name=name).order_by('id')
                
                # Keep the first one, rename the rest
                for index, product in enumerate(products):
                    if index > 0:
                        new_name = f"{name} ({index + 1})"
                        old_name = product.name
                        product.name = new_name
                        product.slug = None  # Will be regenerated on save
                        product.save()
                        self.stdout.write(
                            self.style.SUCCESS(f'Renamed product: "{old_name}" → "{new_name}"')
                        )
        else:
            self.stdout.write(self.style.SUCCESS('No duplicate products found'))
        
        # Fix duplicate categories
        duplicate_categories = Category.objects.values('name').annotate(
            count=Count('id')
        ).filter(count__gt=1)
        
        if duplicate_categories:
            self.stdout.write(self.style.WARNING(f'Found {len(duplicate_categories)} duplicate category names'))
            
            for dup in duplicate_categories:
                name = dup['name']
                categories = Category.objects.filter(name=name).order_by('id')
                
                # Keep the first one, rename the rest
                for index, category in enumerate(categories):
                    if index > 0:
                        new_name = f"{name} ({index + 1})"
                        old_name = category.name
                        category.name = new_name
                        category.slug = None  # Will be regenerated on save
                        category.save()
                        self.stdout.write(
                            self.style.SUCCESS(f'Renamed category: "{old_name}" → "{new_name}"')
                        )
        else:
            self.stdout.write(self.style.SUCCESS('No duplicate categories found'))
        
        self.stdout.write(self.style.SUCCESS('\n✓ All duplicates fixed! You can now run migrations.'))

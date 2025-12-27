from django.core.management.base import BaseCommand
from django.db import transaction
from users.models import User
from products.models import Category, Product
from decimal import Decimal
import random


class Command(BaseCommand):
    help = 'Seeds the database with sample data (admin user, categories, and products)'
    
    def handle(self, *args, **kwargs):
        self.stdout.write('Seeding database...')
        
        with transaction.atomic():
            # Create admin user
            self.create_admin_user()
            
            # Create categories
            categories = self.create_categories()
            
            # Create products
            self.create_products(categories)
        
        self.stdout.write(self.style.SUCCESS('Database seeded successfully!'))
    
    def create_admin_user(self):
        self.stdout.write('Creating admin user...')
        
        if User.objects.filter(email='admin@example.com').exists():
            self.stdout.write(self.style.WARNING('Admin user already exists'))
            return
        
        admin = User.objects.create_superuser(
            email='admin@example.com',
            password='admin123',
            first_name='Admin',
            last_name='User'
        )
        admin.is_admin = True
        admin.save()
        
        self.stdout.write(self.style.SUCCESS('Admin user created: admin@example.com / admin123'))
        
        # Create test user
        if not User.objects.filter(email='user@example.com').exists():
            User.objects.create_user(
                email='user@example.com',
                password='user123',
                first_name='Test',
                last_name='User'
            )
            self.stdout.write(self.style.SUCCESS('Test user created: user@example.com / user123'))
    
    def create_categories(self):
        self.stdout.write('Creating categories...')
        
        categories = {}
        
        # Create root categories
        electronics = Category.objects.get_or_create(
            name='Electronics',
            defaults={
                'slug': 'electronics',
                'description': 'Electronic devices and accessories',
                'is_active': True
            }
        )[0]
        categories['electronics'] = electronics
        
        clothing = Category.objects.get_or_create(
            name='Clothing',
            defaults={
                'slug': 'clothing',
                'description': 'Apparel and fashion items',
                'is_active': True
            }
        )[0]
        categories['clothing'] = clothing
        
        books = Category.objects.get_or_create(
            name='Books',
            defaults={
                'slug': 'books',
                'description': 'Books and reading materials',
                'is_active': True
            }
        )[0]
        categories['books'] = books
        
        home = Category.objects.get_or_create(
            name='Home & Garden',
            defaults={
                'slug': 'home-garden',
                'description': 'Home improvement and garden supplies',
                'is_active': True
            }
        )[0]
        categories['home'] = home
        
        # Create subcategories for Electronics
        computers = Category.objects.get_or_create(
            name='Computers',
            defaults={
                'slug': 'computers',
                'parent': electronics,
                'description': 'Computers and computer accessories',
                'is_active': True
            }
        )[0]
        categories['computers'] = computers
        
        phones = Category.objects.get_or_create(
            name='Mobile Phones',
            defaults={
                'slug': 'mobile-phones',
                'parent': electronics,
                'description': 'Smartphones and accessories',
                'is_active': True
            }
        )[0]
        categories['phones'] = phones
        
        # Create subcategories for Computers
        laptops = Category.objects.get_or_create(
            name='Laptops',
            defaults={
                'slug': 'laptops',
                'parent': computers,
                'description': 'Laptop computers',
                'is_active': True
            }
        )[0]
        categories['laptops'] = laptops
        
        accessories = Category.objects.get_or_create(
            name='Computer Accessories',
            defaults={
                'slug': 'computer-accessories',
                'parent': computers,
                'description': 'Mouse, keyboard, and other accessories',
                'is_active': True
            }
        )[0]
        categories['accessories'] = accessories
        
        # Create subcategories for Clothing
        mens = Category.objects.get_or_create(
            name='Men\'s Clothing',
            defaults={
                'slug': 'mens-clothing',
                'parent': clothing,
                'description': 'Clothing for men',
                'is_active': True
            }
        )[0]
        categories['mens'] = mens
        
        womens = Category.objects.get_or_create(
            name='Women\'s Clothing',
            defaults={
                'slug': 'womens-clothing',
                'parent': clothing,
                'description': 'Clothing for women',
                'is_active': True
            }
        )[0]
        categories['womens'] = womens
        
        self.stdout.write(self.style.SUCCESS(f'Created {len(categories)} categories'))
        return categories
    
    def create_products(self, categories):
        self.stdout.write('Creating products...')
        
        products_data = [
            # Electronics - Laptops
            {
                'name': 'MacBook Pro 16"',
                'sku': 'LAPTOP-001',
                'slug': 'macbook-pro-16',
                'description': 'Apple MacBook Pro with M2 chip, 16GB RAM, 512GB SSD',
                'price': Decimal('2499.99'),
                'stock': 15,
                'category': categories['laptops'],
                'image_url': 'https://example.com/macbook.jpg'
            },
            {
                'name': 'Dell XPS 15',
                'sku': 'LAPTOP-002',
                'slug': 'dell-xps-15',
                'description': 'Dell XPS 15 with Intel i7, 16GB RAM, 1TB SSD',
                'price': Decimal('1799.99'),
                'stock': 20,
                'category': categories['laptops'],
                'image_url': 'https://example.com/dell-xps.jpg'
            },
            {
                'name': 'Lenovo ThinkPad X1',
                'sku': 'LAPTOP-003',
                'slug': 'lenovo-thinkpad-x1',
                'description': 'Business laptop with Intel i5, 8GB RAM, 256GB SSD',
                'price': Decimal('1299.99'),
                'stock': 25,
                'category': categories['laptops'],
                'image_url': 'https://example.com/thinkpad.jpg'
            },
            
            # Electronics - Phones
            {
                'name': 'iPhone 15 Pro',
                'sku': 'PHONE-001',
                'slug': 'iphone-15-pro',
                'description': 'Latest iPhone with A17 chip, 256GB storage',
                'price': Decimal('999.99'),
                'stock': 30,
                'category': categories['phones'],
                'image_url': 'https://example.com/iphone.jpg'
            },
            {
                'name': 'Samsung Galaxy S24',
                'sku': 'PHONE-002',
                'slug': 'samsung-galaxy-s24',
                'description': 'Samsung flagship with 128GB storage',
                'price': Decimal('849.99'),
                'stock': 40,
                'category': categories['phones'],
                'image_url': 'https://example.com/galaxy.jpg'
            },
            
            # Computer Accessories
            {
                'name': 'Logitech MX Master 3',
                'sku': 'ACC-001',
                'slug': 'logitech-mx-master-3',
                'description': 'Wireless mouse for productivity',
                'price': Decimal('99.99'),
                'stock': 50,
                'category': categories['accessories'],
                'image_url': 'https://example.com/mouse.jpg'
            },
            {
                'name': 'Mechanical Keyboard RGB',
                'sku': 'ACC-002',
                'slug': 'mechanical-keyboard-rgb',
                'description': 'Gaming mechanical keyboard with RGB lighting',
                'price': Decimal('129.99'),
                'stock': 35,
                'category': categories['accessories'],
                'image_url': 'https://example.com/keyboard.jpg'
            },
            
            # Clothing - Men's
            {
                'name': 'Men\'s Cotton T-Shirt',
                'sku': 'CLOTH-M-001',
                'slug': 'mens-cotton-tshirt',
                'description': 'Comfortable cotton t-shirt',
                'price': Decimal('24.99'),
                'stock': 100,
                'category': categories['mens'],
                'image_url': 'https://example.com/tshirt.jpg'
            },
            {
                'name': 'Men\'s Jeans',
                'sku': 'CLOTH-M-002',
                'slug': 'mens-jeans',
                'description': 'Classic blue jeans',
                'price': Decimal('59.99'),
                'stock': 75,
                'category': categories['mens'],
                'image_url': 'https://example.com/jeans.jpg'
            },
            
            # Clothing - Women's
            {
                'name': 'Women\'s Summer Dress',
                'sku': 'CLOTH-W-001',
                'slug': 'womens-summer-dress',
                'description': 'Floral summer dress',
                'price': Decimal('49.99'),
                'stock': 60,
                'category': categories['womens'],
                'image_url': 'https://example.com/dress.jpg'
            },
            {
                'name': 'Women\'s Cardigan',
                'sku': 'CLOTH-W-002',
                'slug': 'womens-cardigan',
                'description': 'Cozy knit cardigan',
                'price': Decimal('39.99'),
                'stock': 45,
                'category': categories['womens'],
                'image_url': 'https://example.com/cardigan.jpg'
            },
            
            # Books
            {
                'name': 'Python Programming Guide',
                'sku': 'BOOK-001',
                'slug': 'python-programming-guide',
                'description': 'Comprehensive guide to Python programming',
                'price': Decimal('34.99'),
                'stock': 80,
                'category': categories['books'],
                'image_url': 'https://example.com/python-book.jpg'
            },
            {
                'name': 'Clean Code',
                'sku': 'BOOK-002',
                'slug': 'clean-code',
                'description': 'A Handbook of Agile Software Craftsmanship',
                'price': Decimal('42.99'),
                'stock': 65,
                'category': categories['books'],
                'image_url': 'https://example.com/clean-code.jpg'
            },
        ]
        
        created_count = 0
        for product_data in products_data:
            product, created = Product.objects.get_or_create(
                sku=product_data['sku'],
                defaults=product_data
            )
            if created:
                created_count += 1
        
        self.stdout.write(self.style.SUCCESS(f'Created {created_count} products'))

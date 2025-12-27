from django.test import TestCase
from django.contrib.auth import get_user_model
from decimal import Decimal
from products.models import Category, Product
from orders.models import Order, OrderItem
from payments.models import Payment

User = get_user_model()


class UserModelTest(TestCase):
    """Test User model"""
    
    def setUp(self):
        self.user_data = {
            'email': 'test@example.com',
            'password': 'testpass123',
            'first_name': 'Test',
            'last_name': 'User'
        }
    
    def test_create_user(self):
        """Test creating a user"""
        user = User.objects.create_user(**self.user_data)
        self.assertEqual(user.email, self.user_data['email'])
        self.assertTrue(user.check_password(self.user_data['password']))
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)
    
    def test_create_superuser(self):
        """Test creating a superuser"""
        user = User.objects.create_superuser(**self.user_data)
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
    
    def test_email_unique(self):
        """Test email uniqueness"""
        User.objects.create_user(**self.user_data)
        with self.assertRaises(Exception):
            User.objects.create_user(**self.user_data)


class CategoryModelTest(TestCase):
    """Test Category model"""
    
    def setUp(self):
        self.parent = Category.objects.create(
            name='Electronics',
            slug='electronics'
        )
        self.child = Category.objects.create(
            name='Laptops',
            slug='laptops',
            parent=self.parent
        )
    
    def test_category_creation(self):
        """Test category creation"""
        self.assertEqual(self.parent.name, 'Electronics')
        self.assertIsNone(self.parent.parent)
    
    def test_category_hierarchy(self):
        """Test category parent-child relationship"""
        self.assertEqual(self.child.parent, self.parent)
        self.assertIn(self.child, self.parent.children.all())
    
    def test_get_full_path(self):
        """Test getting full category path"""
        path = self.child.get_full_path()
        self.assertEqual(path, 'Electronics > Laptops')
    
    def test_get_descendants_dfs(self):
        """Test DFS traversal for descendants"""
        grandchild = Category.objects.create(
            name='Gaming Laptops',
            slug='gaming-laptops',
            parent=self.child
        )
        descendants = self.parent.get_descendants_dfs()
        self.assertIn(self.child, descendants)
        self.assertIn(grandchild, descendants)


class ProductModelTest(TestCase):
    """Test Product model"""
    
    def setUp(self):
        self.category = Category.objects.create(
            name='Electronics',
            slug='electronics'
        )
        self.product = Product.objects.create(
            name='Test Laptop',
            sku='TEST-001',
            slug='test-laptop',
            price=Decimal('999.99'),
            stock=10,
            category=self.category
        )
    
    def test_product_creation(self):
        """Test product creation"""
        self.assertEqual(self.product.name, 'Test Laptop')
        self.assertEqual(self.product.stock, 10)
    
    def test_is_available(self):
        """Test product availability check"""
        self.assertTrue(self.product.is_available())
        
        self.product.stock = 0
        self.product.save()
        self.assertFalse(self.product.is_available())
    
    def test_reduce_stock(self):
        """Test stock reduction"""
        initial_stock = self.product.stock
        self.product.reduce_stock(5)
        self.assertEqual(self.product.stock, initial_stock - 5)
    
    def test_reduce_stock_insufficient(self):
        """Test stock reduction with insufficient stock"""
        with self.assertRaises(ValueError):
            self.product.reduce_stock(20)
    
    def test_increase_stock(self):
        """Test stock increase"""
        initial_stock = self.product.stock
        self.product.increase_stock(5)
        self.assertEqual(self.product.stock, initial_stock + 5)


class OrderModelTest(TestCase):
    """Test Order model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.product = Product.objects.create(
            name='Test Product',
            sku='TEST-001',
            slug='test-product',
            price=Decimal('50.00'),
            stock=10
        )
        self.order = Order.objects.create(
            user=self.user,
            total_amount=Decimal('100.00')
        )
    
    def test_order_creation(self):
        """Test order creation"""
        self.assertEqual(self.order.user, self.user)
        self.assertEqual(self.order.status, 'pending')
    
    def test_calculate_total(self):
        """Test order total calculation"""
        OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=2,
            price=self.product.price
        )
        calculated_total = self.order.calculate_total()
        self.assertEqual(calculated_total, Decimal('100.00'))
    
    def test_mark_as_paid(self):
        """Test marking order as paid"""
        OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=2,
            price=self.product.price
        )
        initial_stock = self.product.stock
        self.order.mark_as_paid()
        self.product.refresh_from_db()
        self.assertEqual(self.order.status, 'paid')
        self.assertEqual(self.product.stock, initial_stock - 2)
    
    def test_cancel_order(self):
        """Test order cancellation"""
        self.order.cancel()
        self.assertEqual(self.order.status, 'cancelled')


class OrderItemModelTest(TestCase):
    """Test OrderItem model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.product = Product.objects.create(
            name='Test Product',
            sku='TEST-001',
            slug='test-product',
            price=Decimal('50.00'),
            stock=10
        )
        self.order = Order.objects.create(
            user=self.user,
            total_amount=Decimal('0.00')
        )
    
    def test_order_item_creation(self):
        """Test order item creation"""
        item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=2
        )
        self.assertEqual(item.quantity, 2)
        self.assertEqual(item.price, self.product.price)
    
    def test_subtotal_calculation(self):
        """Test subtotal calculation"""
        item = OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=3
        )
        expected_subtotal = Decimal('150.00')  # 3 * 50.00
        self.assertEqual(item.subtotal, expected_subtotal)
    
    def test_order_total_update(self):
        """Test that creating order item updates order total"""
        OrderItem.objects.create(
            order=self.order,
            product=self.product,
            quantity=2
        )
        self.order.refresh_from_db()
        self.assertEqual(self.order.total_amount, Decimal('100.00'))


class PaymentModelTest(TestCase):
    """Test Payment model"""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        self.order = Order.objects.create(
            user=self.user,
            total_amount=Decimal('100.00')
        )
        self.payment = Payment.objects.create(
            order=self.order,
            provider='stripe',
            transaction_id='pi_test_123',
            amount=Decimal('100.00'),
            currency='USD'
        )
    
    def test_payment_creation(self):
        """Test payment creation"""
        self.assertEqual(self.payment.provider, 'stripe')
        self.assertEqual(self.payment.status, 'pending')
    
    def test_mark_as_success(self):
        """Test marking payment as successful"""
        self.payment.mark_as_success()
        self.assertEqual(self.payment.status, 'success')
        self.assertIsNotNone(self.payment.completed_at)
    
    def test_mark_as_failed(self):
        """Test marking payment as failed"""
        error_msg = 'Payment declined'
        self.payment.mark_as_failed(error_message=error_msg)
        self.assertEqual(self.payment.status, 'failed')
        self.assertEqual(self.payment.error_message, error_msg)
    
    def test_can_be_refunded(self):
        """Test refund eligibility check"""
        self.assertFalse(self.payment.can_be_refunded())
        self.payment.mark_as_success()
        self.assertTrue(self.payment.can_be_refunded())


# Run tests with: python manage.py test

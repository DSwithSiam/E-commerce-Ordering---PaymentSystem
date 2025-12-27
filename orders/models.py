from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal
from users.models import User
from products.models import Product


class Order(models.Model):
    """
    Order model representing customer orders
    
    OOP Principle: Encapsulates order data and business logic
    Data Structure: Foreign key relationships for efficient querying
    """
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('processing', 'Processing'),
        ('shipped', 'Shipped'),
        ('delivered', 'Delivered'),
        ('cancelled', 'Cancelled'),
    ]
    
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='orders',
        db_index=True
    )
    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True
    )
    notes = models.TextField(blank=True, help_text='Additional order notes')
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'orders'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['created_at']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"Order #{self.id} - {self.user.email}"
    
    def calculate_total(self):
        """
        Calculate total amount from order items
        
        Algorithm Requirement: Deterministic calculation of order total
        Time Complexity: O(n) where n is the number of order items
        """
        total = Decimal('0.00')
        for item in self.items.all():
            total += item.subtotal
        return total
    
    def recalculate_and_save(self):
        """Recalculate total and save the order"""
        self.total_amount = self.calculate_total()
        self.save(update_fields=['total_amount', 'updated_at'])
    
    def mark_as_paid(self):
        """Mark order as paid after successful payment"""
        if self.status != 'pending':
            raise ValueError(f"Cannot mark order as paid. Current status: {self.status}")
        
        self.status = 'paid'
        self.save(update_fields=['status', 'updated_at'])
        
        # Reduce stock for all items
        for item in self.items.all():
            item.product.reduce_stock(item.quantity)
    
    def cancel(self):
        """Cancel the order and restore stock if already paid"""
        if self.status in ['shipped', 'delivered']:
            raise ValueError(f"Cannot cancel order with status: {self.status}")
        
        # Restore stock if order was paid
        if self.status == 'paid':
            for item in self.items.all():
                item.product.increase_stock(item.quantity)
        
        self.status = 'cancelled'
        self.save(update_fields=['status', 'updated_at'])
    
    def can_be_modified(self):
        """Check if order can still be modified"""
        return self.status == 'pending'


class OrderItem(models.Model):
    """
    OrderItem model representing products in an order
    
    OOP Principle: Encapsulates order item data and calculations
    Data Structure: Junction table for many-to-many relationship between orders and products
    """
    
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items',
        db_index=True
    )
    product = models.ForeignKey(
        Product,
        on_delete=models.PROTECT,
        related_name='order_items'
    )
    quantity = models.IntegerField(
        validators=[MinValueValidator(1)],
        help_text='Quantity ordered'
    )
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text='Price at the time of order'
    )
    subtotal = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))],
        help_text='Calculated as quantity * price'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'order_items'
        ordering = ['id']
        indexes = [
            models.Index(fields=['order']),
            models.Index(fields=['product']),
        ]
        # Prevent duplicate products in the same order
        unique_together = [['order', 'product']]
    
    def __str__(self):
        return f"{self.product.name} x {self.quantity} (Order #{self.order.id})"
    
    def calculate_subtotal(self):
        """
        Calculate subtotal for this item
        
        Algorithm Requirement: Deterministic subtotal calculation
        """
        return Decimal(str(self.quantity)) * self.price
    
    def save(self, *args, **kwargs):
        """Override save to automatically calculate subtotal"""
        # Set price from product if not already set
        if not self.price:
            self.price = self.product.price
        
        # Calculate subtotal
        self.subtotal = self.calculate_subtotal()
        
        super().save(*args, **kwargs)
        
        # Update order total
        if self.order_id:
            self.order.recalculate_and_save()
    
    def delete(self, *args, **kwargs):
        """Override delete to update order total"""
        order = self.order
        super().delete(*args, **kwargs)
        order.recalculate_and_save()

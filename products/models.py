from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal


class Category(models.Model):
    """
    Category model with hierarchical structure (tree/graph)
    
    OOP & Data Structure: Supports parent-child relationships for category hierarchy
    Algorithm: Used for DFS traversal to find related products
    """
    name = models.CharField(max_length=200, unique=True)
    slug = models.SlugField(max_length=200, unique=True)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children'
    )
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'categories'
        verbose_name_plural = 'Categories'
        ordering = ['name']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['parent']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return self.name
    
    def get_ancestors(self):
        """Get all ancestor categories using iterative approach"""
        ancestors = []
        current = self.parent
        while current is not None:
            ancestors.append(current)
            current = current.parent
        return ancestors
    
    def get_descendants_dfs(self):
        """
        Get all descendant categories using DFS (Depth-First Search)
        
        Algorithm Requirement: DFS traversal for category hierarchy
        Time Complexity: O(n) where n is the number of descendants
        """
        descendants = []
        stack = [self]
        
        while stack:
            current = stack.pop()
            if current != self:
                descendants.append(current)
            # Add children to stack in reverse order for consistent traversal
            children = list(current.children.filter(is_active=True))
            stack.extend(reversed(children))
        
        return descendants
    
    def get_full_path(self):
        """Get the full category path (e.g., 'Electronics > Computers > Laptops')"""
        path = [self.name]
        current = self.parent
        while current is not None:
            path.insert(0, current.name)
            current = current.parent
        return ' > '.join(path)


class Product(models.Model):
    """
    Product model with inventory management
    
    OOP Principle: Encapsulates product data and business logic
    Data Structure: Indexed fields for efficient querying
    """
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('inactive', 'Inactive'),
        ('out_of_stock', 'Out of Stock'),
    ]
    
    name = models.CharField(max_length=255, db_index=True)
    sku = models.CharField(max_length=100, unique=True, db_index=True, help_text='Stock Keeping Unit')
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    stock = models.IntegerField(
        default=0,
        validators=[MinValueValidator(0)],
        help_text='Available quantity in stock'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        db_index=True
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='products'
    )
    image_url = models.URLField(max_length=500, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'products'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['sku']),
            models.Index(fields=['status']),
            models.Index(fields=['category']),
            models.Index(fields=['price']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.sku})"
    
    def is_available(self):
        """Check if product is available for purchase"""
        return self.status == 'active' and self.stock > 0
    
    def reduce_stock(self, quantity):
        """
        Reduce stock after successful payment
        
        Algorithm Requirement: Safe stock reduction with validation
        """
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        
        if self.stock < quantity:
            raise ValueError(f"Insufficient stock. Available: {self.stock}, Requested: {quantity}")
        
        self.stock -= quantity
        
        # Update status if out of stock
        if self.stock == 0:
            self.status = 'out_of_stock'
        
        self.save(update_fields=['stock', 'status', 'updated_at'])
    
    def increase_stock(self, quantity):
        """Increase stock (e.g., when order is cancelled or returned)"""
        if quantity <= 0:
            raise ValueError("Quantity must be positive")
        
        self.stock += quantity
        
        # Reactivate if was out of stock
        if self.status == 'out_of_stock':
            self.status = 'active'
        
        self.save(update_fields=['stock', 'status', 'updated_at'])
    
    def get_related_products(self, limit=5):
        """
        Get related products from same category and subcategories using DFS
        
        DFS + Caching Requirement: Traverse category tree to find related products
        """
        if not self.category:
            return Product.objects.none()
        
        # Get all descendant categories using DFS
        categories = [self.category] + self.category.get_descendants_dfs()
        category_ids = [cat.id for cat in categories]
        
        # Find related products, excluding current product
        related_products = Product.objects.filter(
            category_id__in=category_ids,
            status='active'
        ).exclude(id=self.id)[:limit]
        
        return related_products

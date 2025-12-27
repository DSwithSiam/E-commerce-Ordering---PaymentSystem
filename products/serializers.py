from rest_framework import serializers
from products.models import Product, Category


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for Category model"""
    
    children_count = serializers.SerializerMethodField()
    full_path = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'parent', 
                  'is_active', 'children_count', 'full_path', 'created_at']
        read_only_fields = ['id', 'created_at']
    
    def get_children_count(self, obj):
        """Get number of child categories"""
        return obj.children.filter(is_active=True).count()
    
    def get_full_path(self, obj):
        """Get full category path"""
        return obj.get_full_path()


class CategoryTreeSerializer(serializers.ModelSerializer):
    """Serializer for nested category tree"""
    
    children = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = ['id', 'name', 'slug', 'description', 'children']
    
    def get_children(self, obj):
        """Recursively serialize children"""
        children = obj.children.filter(is_active=True)
        return CategoryTreeSerializer(children, many=True).data


class ProductListSerializer(serializers.ModelSerializer):
    """Serializer for product list view (minimal data)"""
    
    category_name = serializers.CharField(source='category.name', read_only=True)
    is_available = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = ['id', 'name', 'slug', 'sku', 'price', 'stock', 'status', 
                  'category', 'category_name', 'image_url', 'is_available']
    
    def get_is_available(self, obj):
        """Check if product is available"""
        return obj.is_available()


class ProductDetailSerializer(serializers.ModelSerializer):
    """Serializer for product detail view (full data)"""
    
    category_name = serializers.CharField(source='category.name', read_only=True)
    category_path = serializers.SerializerMethodField()
    is_available = serializers.SerializerMethodField()
    related_products = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = ['id', 'name', 'slug', 'sku', 'description', 'price', 'stock', 
                  'status', 'category', 'category_name', 'category_path', 
                  'image_url', 'is_available', 'related_products', 
                  'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_is_available(self, obj):
        """Check if product is available"""
        return obj.is_available()
    
    def get_category_path(self, obj):
        """Get full category path"""
        if obj.category:
            return obj.category.get_full_path()
        return None
    
    def get_related_products(self, obj):
        """Get related products using DFS algorithm"""
        related = obj.get_related_products(limit=5)
        return ProductListSerializer(related, many=True).data


class ProductCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating products"""
    
    class Meta:
        model = Product
        fields = ['name', 'slug', 'sku', 'description', 'price', 'stock', 
                  'status', 'category', 'image_url']
    
    def validate_price(self, value):
        """Validate price is positive"""
        if value <= 0:
            raise serializers.ValidationError("Price must be greater than 0")
        return value
    
    def validate_stock(self, value):
        """Validate stock is non-negative"""
        if value < 0:
            raise serializers.ValidationError("Stock cannot be negative")
        return value
    
    def validate_sku(self, value):
        """Validate SKU is unique"""
        instance = self.instance
        if Product.objects.exclude(pk=instance.pk if instance else None).filter(sku=value).exists():
            raise serializers.ValidationError("Product with this SKU already exists")
        return value

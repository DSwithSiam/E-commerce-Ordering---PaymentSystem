from rest_framework import serializers
from orders.models import Order, OrderItem
from products.serializers import ProductListSerializer


class OrderItemSerializer(serializers.ModelSerializer):
    """Serializer for OrderItem model"""
    
    product_name = serializers.CharField(source='product.name', read_only=True)
    product_sku = serializers.CharField(source='product.sku', read_only=True)
    product = ProductListSerializer(read_only=True)
    
    class Meta:
        model = OrderItem
        fields = ['id', 'product', 'product_name', 'product_sku', 
                  'quantity', 'price', 'subtotal']
        read_only_fields = ['id', 'price', 'subtotal']


class OrderItemCreateSerializer(serializers.Serializer):
    """Serializer for creating order items"""
    
    product_id = serializers.IntegerField()
    quantity = serializers.IntegerField(min_value=1)
    
    def validate_quantity(self, value):
        """Validate quantity is positive"""
        if value <= 0:
            raise serializers.ValidationError("Quantity must be positive")
        return value


class OrderListSerializer(serializers.ModelSerializer):
    """Serializer for order list view"""
    
    user_email = serializers.CharField(source='user.email', read_only=True)
    items_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = ['id', 'user_email', 'total_amount', 'status', 
                  'items_count', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_items_count(self, obj):
        """Get number of items in order"""
        return obj.items.count()


class OrderDetailSerializer(serializers.ModelSerializer):
    """Serializer for order detail view"""
    
    user_email = serializers.CharField(source='user.email', read_only=True)
    items = OrderItemSerializer(many=True, read_only=True)
    payments = serializers.SerializerMethodField()
    
    class Meta:
        model = Order
        fields = ['id', 'user_email', 'total_amount', 'status', 'notes',
                  'items', 'payments', 'created_at', 'updated_at']
        read_only_fields = ['id', 'total_amount', 'created_at', 'updated_at']
    
    def get_payments(self, obj):
        """Get payment information"""
        from payments.serializers import PaymentSerializer
        return PaymentSerializer(obj.payments.all(), many=True).data


class OrderCreateSerializer(serializers.Serializer):
    """Serializer for creating orders"""
    
    items = OrderItemCreateSerializer(many=True)
    notes = serializers.CharField(required=False, allow_blank=True, max_length=1000)
    
    def validate_items(self, value):
        """Validate items list is not empty"""
        if not value:
            raise serializers.ValidationError("Order must contain at least one item")
        return value


class CheckoutSerializer(serializers.Serializer):
    """Serializer for checkout (order + payment)"""
    
    items = OrderItemCreateSerializer(many=True)
    payment_provider = serializers.ChoiceField(choices=['stripe', 'bkash'])
    notes = serializers.CharField(required=False, allow_blank=True, max_length=1000)
    
    def validate_items(self, value):
        """Validate items list is not empty"""
        if not value:
            raise serializers.ValidationError("Order must contain at least one item")
        return value

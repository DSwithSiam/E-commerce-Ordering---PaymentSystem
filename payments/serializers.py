from rest_framework import serializers
from payments.models import Payment


class PaymentSerializer(serializers.ModelSerializer):
    """Serializer for Payment model"""
    
    order_id = serializers.IntegerField(source='order.id', read_only=True)
    
    class Meta:
        model = Payment
        fields = ['id', 'order_id', 'provider', 'transaction_id', 'amount', 
                  'currency', 'status', 'error_message', 'created_at', 
                  'updated_at', 'completed_at']
        read_only_fields = ['id', 'created_at', 'updated_at', 'completed_at']


class PaymentDetailSerializer(serializers.ModelSerializer):
    """Serializer for payment detail with full information"""
    
    order_id = serializers.IntegerField(source='order.id', read_only=True)
    
    class Meta:
        model = Payment
        fields = ['id', 'order_id', 'provider', 'transaction_id', 'amount', 
                  'currency', 'status', 'error_message', 'metadata', 
                  'raw_response', 'created_at', 'updated_at', 'completed_at']
        read_only_fields = ['id', 'created_at', 'updated_at', 'completed_at']


class PaymentConfirmSerializer(serializers.Serializer):
    """Serializer for confirming a payment"""
    
    transaction_id = serializers.CharField(required=True)


class PaymentRefundSerializer(serializers.Serializer):
    """Serializer for refunding a payment"""
    
    amount = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    reason = serializers.CharField(required=False, allow_blank=True)

from rest_framework import viewsets, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from django.core.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from orders.models import Order
from orders.serializers import (
    OrderListSerializer,
    OrderDetailSerializer,
    OrderCreateSerializer,
    CheckoutSerializer
)
from orders.services import OrderService, CheckoutService, OrderValidationService


class OrderViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Order operations
    
    Endpoints:
    - GET /api/orders/ - List user's orders
    - POST /api/orders/ - Create order
    - GET /api/orders/{id}/ - Get order details
    - DELETE /api/orders/{id}/cancel/ - Cancel order
    """
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return OrderListSerializer
        elif self.action == 'create':
            return OrderCreateSerializer
        return OrderDetailSerializer
    
    def get_queryset(self):
        user = self.request.user
        
        # Admin can see all orders, users see only their own
        if user.has_admin_privileges():
            queryset = Order.objects.all()
        else:
            queryset = Order.objects.filter(user=user)
        
        # Filter by status
        status_param = self.request.query_params.get('status', None)
        if status_param:
            queryset = queryset.filter(status=status_param)
        
        return queryset.prefetch_related('items__product', 'payments')
    
    def create(self, request, *args, **kwargs):
        """Create a new order"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Validate items
        items = serializer.validated_data['items']
        validation_errors = OrderValidationService.validate_order_items(items)
        
        if validation_errors:
            return Response({
                'errors': validation_errors
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create order using service
        try:
            order = OrderService.create_order(
                user=request.user,
                items=items,
                notes=serializer.validated_data.get('notes', '')
            )
            
            return Response({
                'order': OrderDetailSerializer(order).data,
                'message': 'Order created successfully'
            }, status=status.HTTP_201_CREATED)
        
        except ValidationError as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    def retrieve(self, request, *args, **kwargs):
        """Get order details"""
        order_id = kwargs.get('pk')
        
        try:
            # Use service to get order with validation
            order = OrderService.get_order_details(
                order_id=order_id,
                user=request.user if not request.user.has_admin_privileges() else None
            )
            
            serializer = self.get_serializer(order)
            return Response(serializer.data)
        
        except Order.DoesNotExist:
            return Response({
                'error': 'Order not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        except ValidationError as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_403_FORBIDDEN)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel an order"""
        try:
            order = OrderService.cancel_order(
                order_id=pk,
                user=request.user if not request.user.has_admin_privileges() else None
            )
            
            return Response({
                'order': OrderDetailSerializer(order).data,
                'message': 'Order cancelled successfully'
            })
        
        except Order.DoesNotExist:
            return Response({
                'error': 'Order not found'
            }, status=status.HTTP_404_NOT_FOUND)
        
        except ValidationError as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def checkout_view(request):
    """
    Checkout endpoint - creates order and initiates payment
    
    POST /api/orders/checkout/
    Body: {
        "items": [{"product_id": 1, "quantity": 2}],
        "payment_provider": "stripe",  // or "bkash"
        "notes": "Optional notes"
    }
    """
    serializer = CheckoutSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    try:
        result = CheckoutService.create_order_and_initiate_payment(
            user=request.user,
            items=serializer.validated_data['items'],
            payment_provider=serializer.validated_data['payment_provider'],
            notes=serializer.validated_data.get('notes', '')
        )
        
        return Response(result, status=status.HTTP_201_CREATED)
    
    except ValidationError as e:
        return Response({
            'error': str(e) if isinstance(e.message, str) else e.message
        }, status=status.HTTP_400_BAD_REQUEST)

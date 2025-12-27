"""
Order Service - Business Logic Layer

OOP Principle: Service layer that encapsulates business logic
Separates business logic from views and models
"""

from django.db import transaction
from django.core.exceptions import ValidationError
from orders.models import Order, OrderItem
from products.models import Product
from payments.models import Payment
from decimal import Decimal
from typing import List, Dict, Any
import logging

logger = logging.getLogger('orders')


class OrderService:
    """
    Service class for order operations
    
    OOP Principle: Encapsulates order business logic
    Algorithm: Transaction management and calculation algorithms
    """
    
    @staticmethod
    @transaction.atomic
    def create_order(user, items: List[Dict[str, Any]], notes: str = '') -> Order:
        """
        Create a new order with items
        
        Algorithm: Transactional order creation with validation
        Time Complexity: O(n) where n is number of items
        
        Args:
            user: User object
            items: List of dicts with 'product_id' and 'quantity'
            notes: Optional order notes
        
        Returns:
            Created Order object
        
        Raises:
            ValidationError: If validation fails
        """
        if not items:
            raise ValidationError("Order must contain at least one item")
        
        # Create order with initial total of 0
        order = Order.objects.create(
            user=user,
            total_amount=Decimal('0.00'),
            notes=notes
        )
        
        logger.info(f"Creating order for user {user.email}")
        
        # Add items to order
        for item_data in items:
            try:
                product = Product.objects.get(id=item_data['product_id'])
                quantity = int(item_data['quantity'])
                
                # Validate product availability
                if not product.is_available():
                    raise ValidationError(f"Product {product.name} is not available")
                
                if product.stock < quantity:
                    raise ValidationError(
                        f"Insufficient stock for {product.name}. "
                        f"Available: {product.stock}, Requested: {quantity}"
                    )
                
                # Create order item
                OrderItem.objects.create(
                    order=order,
                    product=product,
                    quantity=quantity,
                    price=product.price
                )
                
                logger.debug(f"Added item: {product.name} x {quantity}")
            
            except Product.DoesNotExist:
                raise ValidationError(f"Product with ID {item_data['product_id']} not found")
        
        # Total is automatically calculated by OrderItem.save()
        order.refresh_from_db()
        
        logger.info(f"Order {order.id} created successfully. Total: {order.total_amount}")
        
        return order
    
    @staticmethod
    def get_user_orders(user, status: str = None):
        """
        Get orders for a user with optional status filter
        
        OOP: Encapsulates query logic
        """
        queryset = Order.objects.filter(user=user).prefetch_related('items__product')
        
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset
    
    @staticmethod
    def get_order_details(order_id: int, user=None) -> Order:
        """
        Get order details with validation
        
        Args:
            order_id: Order ID
            user: If provided, validates order belongs to user
        
        Raises:
            Order.DoesNotExist: If order not found
            ValidationError: If order doesn't belong to user
        """
        order = Order.objects.prefetch_related(
            'items__product',
            'payments'
        ).get(id=order_id)
        
        if user and order.user != user:
            raise ValidationError("Order does not belong to this user")
        
        return order
    
    @staticmethod
    @transaction.atomic
    def cancel_order(order_id: int, user=None) -> Order:
        """
        Cancel an order
        
        Algorithm: Handles stock restoration if order was paid
        """
        order = OrderService.get_order_details(order_id, user)
        
        try:
            order.cancel()
            logger.info(f"Order {order_id} cancelled successfully")
            return order
        
        except ValueError as e:
            logger.error(f"Failed to cancel order {order_id}: {str(e)}")
            raise ValidationError(str(e))
    
    @staticmethod
    def calculate_order_summary(order: Order) -> Dict[str, Any]:
        """
        Calculate order summary with breakdown
        
        Algorithm: Aggregation and calculation
        """
        items = order.items.all()
        
        summary = {
            'subtotal': order.total_amount,
            'tax': Decimal('0.00'),  # Can be calculated based on location
            'shipping': Decimal('0.00'),  # Can be calculated based on method
            'discount': Decimal('0.00'),  # Can be applied from coupons
            'total': order.total_amount,
            'items_count': items.count(),
            'items': [
                {
                    'product_name': item.product.name,
                    'quantity': item.quantity,
                    'price': item.price,
                    'subtotal': item.subtotal,
                }
                for item in items
            ]
        }
        
        return summary


class OrderValidationService:
    """
    Service for order validation logic
    
    OOP Principle: Single Responsibility - dedicated to validation
    """
    
    @staticmethod
    def validate_order_items(items: List[Dict[str, Any]]) -> List[str]:
        """
        Validate order items before creation
        
        Returns:
            List of error messages (empty if valid)
        """
        errors = []
        
        if not items:
            errors.append("Order must contain at least one item")
            return errors
        
        for idx, item in enumerate(items):
            if 'product_id' not in item:
                errors.append(f"Item {idx + 1}: product_id is required")
                continue
            
            if 'quantity' not in item:
                errors.append(f"Item {idx + 1}: quantity is required")
                continue
            
            try:
                quantity = int(item['quantity'])
                if quantity <= 0:
                    errors.append(f"Item {idx + 1}: quantity must be positive")
            except (ValueError, TypeError):
                errors.append(f"Item {idx + 1}: quantity must be a number")
            
            # Check if product exists and is available
            try:
                product = Product.objects.get(id=item['product_id'])
                
                if not product.is_available():
                    errors.append(f"Item {idx + 1}: Product '{product.name}' is not available")
                
                quantity = int(item['quantity'])
                if product.stock < quantity:
                    errors.append(
                        f"Item {idx + 1}: Insufficient stock for '{product.name}'. "
                        f"Available: {product.stock}, Requested: {quantity}"
                    )
            
            except Product.DoesNotExist:
                errors.append(f"Item {idx + 1}: Product not found")
        
        return errors
    
    @staticmethod
    def can_proceed_to_payment(order: Order) -> tuple[bool, str]:
        """
        Check if order can proceed to payment
        
        Returns:
            Tuple of (can_proceed, message)
        """
        if order.status != 'pending':
            return False, f"Order status must be 'pending', current: {order.status}"
        
        if order.total_amount <= 0:
            return False, "Order total must be greater than zero"
        
        # Check if order has items
        if not order.items.exists():
            return False, "Order has no items"
        
        # Check if all items are still available
        for item in order.items.all():
            if not item.product.is_available():
                return False, f"Product '{item.product.name}' is no longer available"
            
            if item.product.stock < item.quantity:
                return False, f"Insufficient stock for '{item.product.name}'"
        
        return True, "Order can proceed to payment"


class CheckoutService:
    """
    Service for checkout operations
    
    OOP Principle: Orchestrates order creation and payment initiation
    """
    
    @staticmethod
    @transaction.atomic
    def create_order_and_initiate_payment(
        user,
        items: List[Dict[str, Any]],
        payment_provider: str,
        notes: str = ''
    ) -> Dict[str, Any]:
        """
        Create order and initiate payment in one transaction
        
        Algorithm: Combines order creation and payment initiation
        Design Pattern: Uses PaymentContext with Strategy pattern
        
        Returns:
            Dict with order and payment information
        """
        from payments.payment_strategies import get_payment_strategy, PaymentContext
        
        # Validate items first
        validation_errors = OrderValidationService.validate_order_items(items)
        if validation_errors:
            raise ValidationError(validation_errors)
        
        # Create order
        order = OrderService.create_order(user, items, notes)
        
        # Validate order can proceed to payment
        can_proceed, message = OrderValidationService.can_proceed_to_payment(order)
        if not can_proceed:
            raise ValidationError(message)
        
        # Initiate payment using strategy pattern
        try:
            strategy = get_payment_strategy(payment_provider)
            payment_context = PaymentContext(strategy)
            
            # Determine currency based on provider
            currency = 'BDT' if payment_provider.lower() == 'bkash' else 'USD'
            
            # Create payment
            result = payment_context.create_payment(order, order.total_amount, currency)
            
            if not result.get('success'):
                raise ValidationError(f"Payment initiation failed: {result.get('error')}")
            
            # Create Payment record
            payment = Payment.objects.create(
                order=order,
                provider=payment_provider.lower(),
                transaction_id=result['transaction_id'],
                amount=order.total_amount,
                currency=currency,
                status='pending',
                raw_response=result.get('raw_response', {}),
            )
            
            logger.info(f"Payment {payment.id} initiated for order {order.id}")
            
            return {
                'success': True,
                'order_id': order.id,
                'payment_id': payment.id,
                'transaction_id': payment.transaction_id,
                'amount': str(order.total_amount),
                'currency': currency,
                'provider': payment_provider,
                'client_secret': result.get('client_secret'),  # For Stripe
                'bkash_url': result.get('bkash_url'),  # For bKash
            }
        
        except Exception as e:
            logger.error(f"Error initiating payment for order {order.id}: {str(e)}")
            # Order is created but payment failed - mark as pending
            raise ValidationError(f"Payment initiation failed: {str(e)}")

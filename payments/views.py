from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from django.shortcuts import get_object_or_404
from payments.models import Payment
from payments.serializers import (
    PaymentSerializer,
    PaymentDetailSerializer,
    PaymentConfirmSerializer,
    PaymentRefundSerializer
)
from payments.payment_strategies import get_payment_strategy, PaymentContext
import logging
import json

logger = logging.getLogger('payments')


class PaymentViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Payment operations (Read-only)
    
    Endpoints:
    - GET /api/payments/ - List user's payments
    - GET /api/payments/{id}/ - Get payment details
    """
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return PaymentDetailSerializer
        return PaymentSerializer
    
    def get_queryset(self):
        user = self.request.user
        
        # Admin can see all payments, users see only their own
        if user.has_admin_privileges():
            queryset = Payment.objects.all()
        else:
            queryset = Payment.objects.filter(order__user=user)
        
        # Filter by provider
        provider = self.request.query_params.get('provider', None)
        if provider:
            queryset = queryset.filter(provider=provider)
        
        # Filter by status
        status_param = self.request.query_params.get('status', None)
        if status_param:
            queryset = queryset.filter(status=status_param)
        
        return queryset.select_related('order').order_by('-created_at')


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def confirm_payment_view(request):
    """
    Confirm a payment (execute bKash payment or confirm Stripe payment intent)
    
    POST /api/payments/confirm/
    Body: {"transaction_id": "payment_id"}
    """
    serializer = PaymentConfirmSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    transaction_id = serializer.validated_data['transaction_id']
    
    try:
        payment = Payment.objects.get(transaction_id=transaction_id)
        
        # Check if user owns this payment
        if payment.order.user != request.user and not request.user.has_admin_privileges():
            return Response({
                'error': 'Permission denied'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Check if payment can be confirmed
        if not payment.is_pending():
            return Response({
                'error': f'Payment cannot be confirmed. Current status: {payment.status}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Confirm payment using strategy pattern
        strategy = get_payment_strategy(payment.provider)
        payment_context = PaymentContext(strategy)
        
        result = payment_context.confirm_payment(transaction_id)
        
        if result.get('success'):
            payment.mark_as_success(transaction_data=result.get('raw_response'))
            logger.info(f"Payment {payment.id} confirmed successfully")
            
            return Response({
                'payment': PaymentDetailSerializer(payment).data,
                'message': 'Payment confirmed successfully'
            })
        else:
            payment.mark_as_failed(
                error_message=result.get('error', 'Payment confirmation failed'),
                transaction_data=result
            )
            logger.error(f"Payment {payment.id} confirmation failed: {result.get('error')}")
            
            return Response({
                'error': result.get('error', 'Payment confirmation failed')
            }, status=status.HTTP_400_BAD_REQUEST)
    
    except Payment.DoesNotExist:
        return Response({
            'error': 'Payment not found'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def payment_status_view(request, transaction_id):
    """
    Get payment status from provider
    
    GET /api/payments/{transaction_id}/status/
    """
    try:
        payment = Payment.objects.get(transaction_id=transaction_id)
        
        # Check if user owns this payment
        if payment.order.user != request.user and not request.user.has_admin_privileges():
            return Response({
                'error': 'Permission denied'
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Query payment status using strategy pattern
        strategy = get_payment_strategy(payment.provider)
        payment_context = PaymentContext(strategy)
        
        result = payment_context.get_payment_status(transaction_id)
        
        if result.get('success'):
            # Update payment status if changed
            provider_status = result.get('status', '').lower()
            
            if provider_status in ['succeeded', 'completed', 'success']:
                if payment.status != 'success':
                    payment.mark_as_success(transaction_data=result.get('raw_response'))
            elif provider_status in ['failed', 'cancelled']:
                if payment.status not in ['failed', 'cancelled']:
                    payment.mark_as_failed(transaction_data=result.get('raw_response'))
            
            return Response({
                'payment': PaymentDetailSerializer(payment).data,
                'provider_status': result
            })
        else:
            return Response({
                'error': result.get('error', 'Failed to get payment status')
            }, status=status.HTTP_400_BAD_REQUEST)
    
    except Payment.DoesNotExist:
        return Response({
            'error': 'Payment not found'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def refund_payment_view(request, payment_id):
    """
    Refund a payment (Admin only)
    
    POST /api/payments/{payment_id}/refund/
    Body: {"amount": 100.00, "reason": "Customer request"}  // amount is optional
    """
    if not request.user.has_admin_privileges():
        return Response({
            'error': 'Permission denied. Admin access required.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    serializer = PaymentRefundSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    try:
        payment = get_object_or_404(Payment, id=payment_id)
        
        if not payment.can_be_refunded():
            return Response({
                'error': f'Payment cannot be refunded. Current status: {payment.status}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Refund payment using strategy pattern
        strategy = get_payment_strategy(payment.provider)
        payment_context = PaymentContext(strategy)
        
        amount = serializer.validated_data.get('amount')
        result = payment_context.refund_payment(payment.transaction_id, amount=amount)
        
        if result.get('success'):
            payment.status = 'refunded'
            payment.metadata['refund'] = {
                'refund_id': result.get('refund_id'),
                'amount': str(amount) if amount else str(payment.amount),
                'reason': serializer.validated_data.get('reason', ''),
            }
            payment.save(update_fields=['status', 'metadata', 'updated_at'])
            
            logger.info(f"Payment {payment.id} refunded successfully")
            
            return Response({
                'payment': PaymentDetailSerializer(payment).data,
                'message': 'Payment refunded successfully',
                'refund_id': result.get('refund_id')
            })
        else:
            logger.error(f"Payment {payment.id} refund failed: {result.get('error')}")
            return Response({
                'error': result.get('error', 'Refund failed')
            }, status=status.HTTP_400_BAD_REQUEST)
    
    except Payment.DoesNotExist:
        return Response({
            'error': 'Payment not found'
        }, status=status.HTTP_404_NOT_FOUND)


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def stripe_webhook_view(request):
    """
    Stripe webhook handler
    
    POST /api/payments/webhooks/stripe/
    """
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
    
    strategy = get_payment_strategy('stripe')
    payment_context = PaymentContext(strategy)
    
    result = payment_context.handle_webhook(payload, signature=sig_header)
    
    if not result.get('success'):
        logger.error(f"Stripe webhook error: {result.get('error')}")
        return HttpResponse(status=400)
    
    event_type = result.get('event_type')
    data = result.get('data')
    
    logger.info(f"Stripe webhook received: {event_type}")
    
    # Handle different event types
    if event_type == 'payment_intent.succeeded':
        transaction_id = data.get('id')
        try:
            payment = Payment.objects.get(transaction_id=transaction_id)
            payment.mark_as_success(transaction_data=data)
            logger.info(f"Payment {payment.id} marked as success via webhook")
        except Payment.DoesNotExist:
            logger.warning(f"Payment with transaction_id {transaction_id} not found")
    
    elif event_type == 'payment_intent.payment_failed':
        transaction_id = data.get('id')
        try:
            payment = Payment.objects.get(transaction_id=transaction_id)
            error_message = data.get('last_payment_error', {}).get('message', 'Payment failed')
            payment.mark_as_failed(error_message=error_message, transaction_data=data)
            logger.info(f"Payment {payment.id} marked as failed via webhook")
        except Payment.DoesNotExist:
            logger.warning(f"Payment with transaction_id {transaction_id} not found")
    
    return HttpResponse(status=200)


@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def bkash_webhook_view(request):
    """
    bKash webhook handler (placeholder - bKash doesn't support webhooks natively)
    
    POST /api/payments/webhooks/bkash/
    """
    logger.info("bKash webhook received (not implemented)")
    
    # bKash doesn't have native webhook support
    # This is a placeholder for future implementation or custom notification handling
    
    return HttpResponse(status=200)

"""
Payment Strategy Pattern Implementation

Design Pattern: Strategy Pattern
- Allows switching between different payment providers (Stripe, bKash) without modifying core logic
- Easy to add new payment providers in the future
"""

from abc import ABC, abstractmethod
from typing import Dict, Any
import stripe
import requests
import logging
from django.conf import settings
from decimal import Decimal

logger = logging.getLogger('payments')


class PaymentStrategy(ABC):
    """
    Abstract base class for payment strategies
    
    Design Pattern: Strategy Pattern - defines the interface for all payment providers
    """
    
    @abstractmethod
    def create_payment(self, order, amount: Decimal, currency: str = 'USD') -> Dict[str, Any]:
        """Create a payment intent/session"""
        pass
    
    @abstractmethod
    def confirm_payment(self, transaction_id: str) -> Dict[str, Any]:
        """Confirm/execute a payment"""
        pass
    
    @abstractmethod
    def get_payment_status(self, transaction_id: str) -> Dict[str, Any]:
        """Query payment status"""
        pass
    
    @abstractmethod
    def refund_payment(self, transaction_id: str, amount: Decimal = None) -> Dict[str, Any]:
        """Refund a payment"""
        pass
    
    @abstractmethod
    def handle_webhook(self, payload: bytes, signature: str = None) -> Dict[str, Any]:
        """Handle webhook notifications"""
        pass


class StripePaymentStrategy(PaymentStrategy):
    """
    Stripe payment implementation
    
    Design Pattern: Concrete Strategy for Stripe payments
    """
    
    def __init__(self):
        stripe.api_key = settings.STRIPE_SECRET_KEY
        self.webhook_secret = settings.STRIPE_WEBHOOK_SECRET
    
    def create_payment(self, order, amount: Decimal, currency: str = 'USD') -> Dict[str, Any]:
        """Create a Stripe Payment Intent"""
        try:
            # Convert amount to cents (Stripe uses smallest currency unit)
            amount_cents = int(amount * 100)
            
            payment_intent = stripe.PaymentIntent.create(
                amount=amount_cents,
                currency=currency.lower(),
                metadata={
                    'order_id': order.id,
                    'user_email': order.user.email,
                },
                description=f'Order #{order.id}',
            )
            
            logger.info(f"Stripe payment intent created: {payment_intent.id}")
            
            return {
                'success': True,
                'transaction_id': payment_intent.id,
                'client_secret': payment_intent.client_secret,
                'status': payment_intent.status,
                'raw_response': payment_intent,
            }
        
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating payment: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'error_type': type(e).__name__,
            }
    
    def confirm_payment(self, transaction_id: str) -> Dict[str, Any]:
        """Confirm a Stripe Payment Intent"""
        try:
            payment_intent = stripe.PaymentIntent.confirm(transaction_id)
            
            return {
                'success': True,
                'transaction_id': payment_intent.id,
                'status': payment_intent.status,
                'raw_response': payment_intent,
            }
        
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error confirming payment: {str(e)}")
            return {
                'success': False,
                'error': str(e),
            }
    
    def get_payment_status(self, transaction_id: str) -> Dict[str, Any]:
        """Get Stripe Payment Intent status"""
        try:
            payment_intent = stripe.PaymentIntent.retrieve(transaction_id)
            
            return {
                'success': True,
                'transaction_id': payment_intent.id,
                'status': payment_intent.status,
                'amount': Decimal(payment_intent.amount) / 100,
                'currency': payment_intent.currency.upper(),
                'raw_response': payment_intent,
            }
        
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error retrieving payment: {str(e)}")
            return {
                'success': False,
                'error': str(e),
            }
    
    def refund_payment(self, transaction_id: str, amount: Decimal = None) -> Dict[str, Any]:
        """Refund a Stripe payment"""
        try:
            refund_params = {'payment_intent': transaction_id}
            
            if amount:
                refund_params['amount'] = int(amount * 100)
            
            refund = stripe.Refund.create(**refund_params)
            
            logger.info(f"Stripe refund created: {refund.id}")
            
            return {
                'success': True,
                'refund_id': refund.id,
                'status': refund.status,
                'raw_response': refund,
            }
        
        except stripe.error.StripeError as e:
            logger.error(f"Stripe error creating refund: {str(e)}")
            return {
                'success': False,
                'error': str(e),
            }
    
    def handle_webhook(self, payload: bytes, signature: str = None) -> Dict[str, Any]:
        """Handle Stripe webhook events"""
        try:
            event = stripe.Webhook.construct_event(
                payload, signature, self.webhook_secret
            )
            
            logger.info(f"Stripe webhook received: {event.type}")
            
            return {
                'success': True,
                'event_type': event.type,
                'data': event.data.object,
            }
        
        except ValueError as e:
            logger.error(f"Invalid payload: {str(e)}")
            return {
                'success': False,
                'error': 'Invalid payload',
            }
        
        except stripe.error.SignatureVerificationError as e:
            logger.error(f"Invalid signature: {str(e)}")
            return {
                'success': False,
                'error': 'Invalid signature',
            }


class BkashPaymentStrategy(PaymentStrategy):
    """
    bKash payment implementation
    
    Design Pattern: Concrete Strategy for bKash payments
    """
    
    def __init__(self):
        self.app_key = settings.BKASH_APP_KEY
        self.app_secret = settings.BKASH_APP_SECRET
        self.username = settings.BKASH_USERNAME
        self.password = settings.BKASH_PASSWORD
        self.base_url = settings.BKASH_BASE_URL
        self.token = None
    
    def _get_token(self) -> str:
        """Get bKash authentication token"""
        if self.token:
            return self.token
        
        url = f"{self.base_url}/checkout/token/grant"
        headers = {
            'Content-Type': 'application/json',
            'username': self.username,
            'password': self.password,
        }
        data = {
            'app_key': self.app_key,
            'app_secret': self.app_secret,
        }
        
        try:
            response = requests.post(url, json=data, headers=headers)
            response.raise_for_status()
            
            result = response.json()
            self.token = result.get('id_token')
            
            logger.info("bKash token obtained successfully")
            return self.token
        
        except requests.RequestException as e:
            logger.error(f"bKash token error: {str(e)}")
            raise
    
    def create_payment(self, order, amount: Decimal, currency: str = 'BDT') -> Dict[str, Any]:
        """Create a bKash payment"""
        try:
            token = self._get_token()
            
            url = f"{self.base_url}/checkout/payment/create"
            headers = {
                'Content-Type': 'application/json',
                'Authorization': token,
                'X-APP-Key': self.app_key,
            }
            data = {
                'amount': str(amount),
                'currency': currency,
                'intent': 'sale',
                'merchantInvoiceNumber': f'ORDER-{order.id}',
            }
            
            response = requests.post(url, json=data, headers=headers)
            response.raise_for_status()
            
            result = response.json()
            
            logger.info(f"bKash payment created: {result.get('paymentID')}")
            
            return {
                'success': True,
                'transaction_id': result.get('paymentID'),
                'bkash_url': result.get('bkashURL'),
                'status': 'pending',
                'raw_response': result,
            }
        
        except requests.RequestException as e:
            logger.error(f"bKash create payment error: {str(e)}")
            return {
                'success': False,
                'error': str(e),
            }
    
    def confirm_payment(self, transaction_id: str) -> Dict[str, Any]:
        """Execute a bKash payment"""
        try:
            token = self._get_token()
            
            url = f"{self.base_url}/checkout/payment/execute/{transaction_id}"
            headers = {
                'Content-Type': 'application/json',
                'Authorization': token,
                'X-APP-Key': self.app_key,
            }
            
            response = requests.post(url, headers=headers)
            response.raise_for_status()
            
            result = response.json()
            
            logger.info(f"bKash payment executed: {transaction_id}")
            
            return {
                'success': True,
                'transaction_id': result.get('paymentID'),
                'status': result.get('transactionStatus'),
                'raw_response': result,
            }
        
        except requests.RequestException as e:
            logger.error(f"bKash execute payment error: {str(e)}")
            return {
                'success': False,
                'error': str(e),
            }
    
    def get_payment_status(self, transaction_id: str) -> Dict[str, Any]:
        """Query bKash payment status"""
        try:
            token = self._get_token()
            
            url = f"{self.base_url}/checkout/payment/query/{transaction_id}"
            headers = {
                'Content-Type': 'application/json',
                'Authorization': token,
                'X-APP-Key': self.app_key,
            }
            
            response = requests.get(url, headers=headers)
            response.raise_for_status()
            
            result = response.json()
            
            return {
                'success': True,
                'transaction_id': result.get('paymentID'),
                'status': result.get('transactionStatus'),
                'amount': Decimal(result.get('amount', '0')),
                'currency': result.get('currency', 'BDT'),
                'raw_response': result,
            }
        
        except requests.RequestException as e:
            logger.error(f"bKash query payment error: {str(e)}")
            return {
                'success': False,
                'error': str(e),
            }
    
    def refund_payment(self, transaction_id: str, amount: Decimal = None) -> Dict[str, Any]:
        """Refund a bKash payment"""
        try:
            token = self._get_token()
            
            url = f"{self.base_url}/checkout/payment/refund"
            headers = {
                'Content-Type': 'application/json',
                'Authorization': token,
                'X-APP-Key': self.app_key,
            }
            data = {
                'paymentID': transaction_id,
            }
            
            if amount:
                data['amount'] = str(amount)
            
            response = requests.post(url, json=data, headers=headers)
            response.raise_for_status()
            
            result = response.json()
            
            logger.info(f"bKash refund created: {result.get('refundTrxID')}")
            
            return {
                'success': True,
                'refund_id': result.get('refundTrxID'),
                'status': result.get('transactionStatus'),
                'raw_response': result,
            }
        
        except requests.RequestException as e:
            logger.error(f"bKash refund error: {str(e)}")
            return {
                'success': False,
                'error': str(e),
            }
    
    def handle_webhook(self, payload: bytes, signature: str = None) -> Dict[str, Any]:
        """Handle bKash webhook (if supported)"""
        # bKash doesn't have webhook support in the standard implementation
        # This is a placeholder for future implementation
        logger.warning("bKash webhook handling not implemented")
        return {
            'success': False,
            'error': 'bKash webhooks not supported',
        }


class PaymentContext:
    """
    Payment Context class that uses the strategy pattern
    
    Design Pattern: Context class that delegates payment operations to strategy
    OOP Principle: Composition over inheritance
    """
    
    def __init__(self, strategy: PaymentStrategy):
        self._strategy = strategy
    
    @property
    def strategy(self) -> PaymentStrategy:
        return self._strategy
    
    @strategy.setter
    def strategy(self, strategy: PaymentStrategy):
        """Allow dynamic strategy switching"""
        self._strategy = strategy
    
    def create_payment(self, order, amount: Decimal, currency: str = 'USD') -> Dict[str, Any]:
        return self._strategy.create_payment(order, amount, currency)
    
    def confirm_payment(self, transaction_id: str) -> Dict[str, Any]:
        return self._strategy.confirm_payment(transaction_id)
    
    def get_payment_status(self, transaction_id: str) -> Dict[str, Any]:
        return self._strategy.get_payment_status(transaction_id)
    
    def refund_payment(self, transaction_id: str, amount: Decimal = None) -> Dict[str, Any]:
        return self._strategy.refund_payment(transaction_id, amount)
    
    def handle_webhook(self, payload: bytes, signature: str = None) -> Dict[str, Any]:
        return self._strategy.handle_webhook(payload, signature)


def get_payment_strategy(provider: str) -> PaymentStrategy:
    """
    Factory function to get appropriate payment strategy
    
    Design Pattern: Factory pattern combined with Strategy pattern
    """
    strategies = {
        'stripe': StripePaymentStrategy,
        'bkash': BkashPaymentStrategy,
    }
    
    strategy_class = strategies.get(provider.lower())
    
    if not strategy_class:
        raise ValueError(f"Unsupported payment provider: {provider}")
    
    return strategy_class()

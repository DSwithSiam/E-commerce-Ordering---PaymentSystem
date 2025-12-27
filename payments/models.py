from django.db import models
from orders.models import Order


class Payment(models.Model):
    """
    Payment model to track payment transactions
    
    OOP Principle: Encapsulates payment data and status management
    Design Pattern: Works with Strategy pattern for multiple payment providers
    """
    
    PROVIDER_CHOICES = [
        ('stripe', 'Stripe'),
        ('bkash', 'bKash'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('processing', 'Processing'),
        ('success', 'Success'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
        ('refunded', 'Refunded'),
    ]
    
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='payments',
        db_index=True
    )
    provider = models.CharField(
        max_length=20,
        choices=PROVIDER_CHOICES,
        db_index=True,
        help_text='Payment provider (stripe/bkash)'
    )
    transaction_id = models.CharField(
        max_length=255,
        unique=True,
        db_index=True,
        help_text='Unique transaction ID from payment provider'
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        help_text='Payment amount'
    )
    currency = models.CharField(
        max_length=3,
        default='USD',
        help_text='Currency code (USD, BDT, etc.)'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        db_index=True
    )
    raw_response = models.JSONField(
        default=dict,
        blank=True,
        help_text='Raw JSON response from payment provider'
    )
    error_message = models.TextField(
        blank=True,
        help_text='Error message if payment failed'
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text='Additional metadata about the payment'
    )
    created_at = models.DateTimeField(auto_now_add=True, db_index=True)
    updated_at = models.DateTimeField(auto_now=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'payments'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['transaction_id']),
            models.Index(fields=['provider', 'status']),
            models.Index(fields=['order', 'status']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"Payment {self.transaction_id} - {self.provider} ({self.status})"
    
    def mark_as_success(self, transaction_data=None):
        """Mark payment as successful"""
        from django.utils import timezone
        
        self.status = 'success'
        self.completed_at = timezone.now()
        
        if transaction_data:
            self.raw_response = transaction_data
        
        self.save(update_fields=['status', 'completed_at', 'raw_response', 'updated_at'])
        
        # Mark order as paid
        try:
            self.order.mark_as_paid()
        except ValueError as e:
            # Log the error but don't fail the payment
            import logging
            logger = logging.getLogger('payments')
            logger.warning(f"Payment {self.id} succeeded but order update failed: {str(e)}")
    
    def mark_as_failed(self, error_message='', transaction_data=None):
        """Mark payment as failed"""
        from django.utils import timezone
        
        self.status = 'failed'
        self.error_message = error_message
        self.completed_at = timezone.now()
        
        if transaction_data:
            self.raw_response = transaction_data
        
        self.save(update_fields=['status', 'error_message', 'completed_at', 'raw_response', 'updated_at'])
    
    def mark_as_processing(self):
        """Mark payment as processing"""
        self.status = 'processing'
        self.save(update_fields=['status', 'updated_at'])
    
    def can_be_refunded(self):
        """Check if payment can be refunded"""
        return self.status == 'success'
    
    def is_successful(self):
        """Check if payment was successful"""
        return self.status == 'success'
    
    def is_pending(self):
        """Check if payment is pending"""
        return self.status == 'pending'

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from payments.views import (
    PaymentViewSet,
    confirm_payment_view,
    payment_status_view,
    refund_payment_view,
    stripe_webhook_view,
    bkash_webhook_view
)

app_name = 'payments'

router = DefaultRouter()
router.register(r'payments', PaymentViewSet, basename='payment')

urlpatterns = [
    path('', include(router.urls)),
    path('confirm/', confirm_payment_view, name='confirm-payment'),
    path('<str:transaction_id>/status/', payment_status_view, name='payment-status'),
    path('<int:payment_id>/refund/', refund_payment_view, name='refund-payment'),
    path('webhooks/stripe/', stripe_webhook_view, name='stripe-webhook'),
    path('webhooks/bkash/', bkash_webhook_view, name='bkash-webhook'),
]

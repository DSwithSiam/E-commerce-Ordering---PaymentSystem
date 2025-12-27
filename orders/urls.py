from django.urls import path, include
from rest_framework.routers import DefaultRouter
from orders.views import OrderViewSet, checkout_view

app_name = 'orders'

router = DefaultRouter()
router.register(r'orders', OrderViewSet, basename='order')

urlpatterns = [
    path('', include(router.urls)),
    path('checkout/', checkout_view, name='checkout'),
]

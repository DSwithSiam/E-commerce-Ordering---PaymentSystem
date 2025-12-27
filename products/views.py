from rest_framework import viewsets, status, filters
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from products.models import Product, Category
from products.serializers import (
    ProductListSerializer,
    ProductDetailSerializer,
    ProductCreateUpdateSerializer,
    CategorySerializer,
    CategoryTreeSerializer
)
from products.services import CategoryTreeService, ProductRecommendationService


class IsAdminOrReadOnly(AllowAny):
    """
    Custom permission: Admin can edit, others can only read
    """
    def has_permission(self, request, view):
        if request.method in ['GET', 'HEAD', 'OPTIONS']:
            return True
        return request.user and request.user.is_authenticated and request.user.has_admin_privileges()


class ProductViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Product CRUD operations
    
    Endpoints:
    - GET /api/products/ - List products
    - POST /api/products/ - Create product (Admin only)
    - GET /api/products/{id}/ - Get product details
    - PUT/PATCH /api/products/{id}/ - Update product (Admin only)
    - DELETE /api/products/{id}/ - Delete product (Admin only)
    - GET /api/products/{id}/related/ - Get related products
    """
    queryset = Product.objects.all()
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'sku', 'description']
    ordering_fields = ['name', 'price', 'created_at']
    ordering = ['-created_at']
    
    def get_serializer_class(self):
        if self.action in ['list']:
            return ProductListSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return ProductCreateUpdateSerializer
        return ProductDetailSerializer
    
    def get_queryset(self):
        queryset = Product.objects.select_related('category')
        
        # Filter by status
        status_param = self.request.query_params.get('status', None)
        if status_param:
            queryset = queryset.filter(status=status_param)
        else:
            # By default, show only active products for non-admin users
            if not (self.request.user and self.request.user.has_admin_privileges()):
                queryset = queryset.filter(status='active')
        
        # Filter by category
        category_id = self.request.query_params.get('category', None)
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        
        # Filter by price range
        min_price = self.request.query_params.get('min_price', None)
        max_price = self.request.query_params.get('max_price', None)
        if min_price:
            queryset = queryset.filter(price__gte=min_price)
        if max_price:
            queryset = queryset.filter(price__lte=max_price)
        
        # Filter by availability
        available = self.request.query_params.get('available', None)
        if available == 'true':
            queryset = queryset.filter(status='active', stock__gt=0)
        
        return queryset
    
    @action(detail=True, methods=['get'])
    def related(self, request, pk=None):
        """
        Get related products using DFS algorithm
        
        GET /api/products/{id}/related/
        """
        product = self.get_object()
        related_products = ProductRecommendationService.get_recommendations(product, limit=5)
        serializer = ProductListSerializer(related_products, many=True)
        return Response(serializer.data)


class CategoryViewSet(viewsets.ModelViewSet):
    """
    ViewSet for Category CRUD operations
    
    Endpoints:
    - GET /api/categories/ - List categories
    - POST /api/categories/ - Create category (Admin only)
    - GET /api/categories/{id}/ - Get category details
    - PUT/PATCH /api/categories/{id}/ - Update category (Admin only)
    - DELETE /api/categories/{id}/ - Delete category (Admin only)
    - GET /api/categories/tree/ - Get category tree
    - GET /api/categories/{id}/products/ - Get products in category
    """
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    ordering = ['name']
    
    def get_queryset(self):
        queryset = Category.objects.filter(is_active=True)
        
        # Filter by parent
        parent_id = self.request.query_params.get('parent', None)
        if parent_id == 'null':
            queryset = queryset.filter(parent=None)
        elif parent_id:
            queryset = queryset.filter(parent_id=parent_id)
        
        return queryset
    
    @action(detail=False, methods=['get'])
    def tree(self, request):
        """
        Get complete category tree with DFS and caching
        
        GET /api/categories/tree/
        """
        force_refresh = request.query_params.get('refresh', 'false').lower() == 'true'
        tree = CategoryTreeService.get_category_tree_cached(force_refresh=force_refresh)
        return Response(tree)
    
    @action(detail=True, methods=['get'])
    def products(self, request, pk=None):
        """
        Get all products in category and subcategories using DFS
        
        GET /api/categories/{id}/products/
        """
        category = self.get_object()
        
        # Include subcategories using DFS
        include_subcategories = request.query_params.get('include_subcategories', 'true').lower() == 'true'
        
        if include_subcategories:
            # Get descendant categories using DFS with caching
            descendant_ids = CategoryTreeService.get_descendant_categories_dfs(category.id)
            category_ids = [category.id] + descendant_ids
            products = Product.objects.filter(category_id__in=category_ids, status='active')
        else:
            products = Product.objects.filter(category=category, status='active')
        
        serializer = ProductListSerializer(products, many=True)
        return Response(serializer.data)

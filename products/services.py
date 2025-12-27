"""
Category Tree Service with DFS and Caching

DFS + Caching Requirement:
- Uses DFS to traverse category tree
- Caches category tree in Redis to minimize database calls
- Speeds up repeated traversals for product recommendations
"""

from django.core.cache import cache
from django.db.models import Prefetch
from products.models import Category, Product
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger('products')


class CategoryTreeService:
    """
    Service class for category tree operations with caching
    
    Design Pattern: Service Layer pattern
    Algorithm: Depth-First Search (DFS) for tree traversal
    Data Structure: Tree/Graph structure with caching
    """
    
    CACHE_KEY_PREFIX = 'category_tree'
    CACHE_TIMEOUT = 3600  # 1 hour
    
    @classmethod
    def get_category_tree_cached(cls, force_refresh: bool = False) -> List[Dict[str, Any]]:
        """
        Get the complete category tree with caching
        
        DFS + Caching: Retrieves tree from cache or builds using DFS
        Time Complexity: O(1) for cache hit, O(n) for cache miss
        """
        cache_key = f'{cls.CACHE_KEY_PREFIX}:full_tree'
        
        if not force_refresh:
            cached_tree = cache.get(cache_key)
            if cached_tree:
                logger.debug("Category tree retrieved from cache")
                return cached_tree
        
        # Cache miss - build tree using DFS
        logger.info("Building category tree from database")
        tree = cls._build_category_tree()
        
        # Cache the tree
        cache.set(cache_key, tree, cls.CACHE_TIMEOUT)
        
        return tree
    
    @classmethod
    def _build_category_tree(cls) -> List[Dict[str, Any]]:
        """
        Build category tree using DFS traversal
        
        Algorithm: Depth-First Search
        Returns: List of root categories with nested children
        """
        # Get all active categories with their children prefetched
        root_categories = Category.objects.filter(
            parent=None,
            is_active=True
        ).prefetch_related('children')
        
        tree = []
        for root in root_categories:
            tree.append(cls._serialize_category_dfs(root))
        
        return tree
    
    @classmethod
    def _serialize_category_dfs(cls, category: Category) -> Dict[str, Any]:
        """
        Serialize a category and its descendants using DFS
        
        Algorithm: Recursive DFS implementation
        Time Complexity: O(n) where n is number of descendants
        Space Complexity: O(h) where h is tree height (recursion stack)
        """
        serialized = {
            'id': category.id,
            'name': category.name,
            'slug': category.slug,
            'description': category.description,
            'children': []
        }
        
        # Recursively process children (DFS)
        for child in category.children.filter(is_active=True):
            serialized['children'].append(cls._serialize_category_dfs(child))
        
        return serialized
    
    @classmethod
    def get_category_with_ancestors_cached(cls, category_id: int) -> Optional[Dict[str, Any]]:
        """
        Get a category with its ancestor path (breadcrumbs) from cache
        
        Caching: Individual category paths are cached separately
        """
        cache_key = f'{cls.CACHE_KEY_PREFIX}:category:{category_id}:ancestors'
        
        cached_data = cache.get(cache_key)
        if cached_data:
            logger.debug(f"Category {category_id} ancestors retrieved from cache")
            return cached_data
        
        try:
            category = Category.objects.get(id=category_id, is_active=True)
            ancestors = category.get_ancestors()
            
            data = {
                'category': {
                    'id': category.id,
                    'name': category.name,
                    'slug': category.slug,
                },
                'ancestors': [
                    {'id': a.id, 'name': a.name, 'slug': a.slug}
                    for a in reversed(ancestors)
                ]
            }
            
            cache.set(cache_key, data, cls.CACHE_TIMEOUT)
            return data
        
        except Category.DoesNotExist:
            logger.warning(f"Category {category_id} not found")
            return None
    
    @classmethod
    def get_descendant_categories_dfs(cls, category_id: int) -> List[int]:
        """
        Get all descendant category IDs using DFS with caching
        
        DFS Algorithm: Non-recursive DFS using stack
        Caching: Results are cached for fast repeated access
        """
        cache_key = f'{cls.CACHE_KEY_PREFIX}:category:{category_id}:descendants'
        
        cached_ids = cache.get(cache_key)
        if cached_ids:
            logger.debug(f"Category {category_id} descendants retrieved from cache")
            return cached_ids
        
        try:
            category = Category.objects.get(id=category_id, is_active=True)
            descendants = category.get_descendants_dfs()
            descendant_ids = [cat.id for cat in descendants]
            
            cache.set(cache_key, descendant_ids, cls.CACHE_TIMEOUT)
            return descendant_ids
        
        except Category.DoesNotExist:
            logger.warning(f"Category {category_id} not found")
            return []
    
    @classmethod
    def get_related_products_cached(cls, product_id: int, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get related products using DFS traversal with caching
        
        DFS + Caching Requirement: Traverse category tree and cache results
        """
        cache_key = f'{cls.CACHE_KEY_PREFIX}:product:{product_id}:related:{limit}'
        
        cached_products = cache.get(cache_key)
        if cached_products:
            logger.debug(f"Related products for {product_id} retrieved from cache")
            return cached_products
        
        try:
            product = Product.objects.get(id=product_id)
            
            if not product.category:
                return []
            
            # Get descendant categories using DFS (with caching)
            descendant_ids = cls.get_descendant_categories_dfs(product.category.id)
            category_ids = [product.category.id] + descendant_ids
            
            # Find related products
            related = Product.objects.filter(
                category_id__in=category_ids,
                status='active'
            ).exclude(id=product_id).values(
                'id', 'name', 'slug', 'price', 'image_url'
            )[:limit]
            
            related_list = list(related)
            
            # Cache results
            cache.set(cache_key, related_list, cls.CACHE_TIMEOUT)
            
            return related_list
        
        except Product.DoesNotExist:
            logger.warning(f"Product {product_id} not found")
            return []
    
    @classmethod
    def invalidate_category_cache(cls, category_id: Optional[int] = None):
        """
        Invalidate category cache
        
        Args:
            category_id: If provided, invalidates specific category cache
                        If None, invalidates entire category tree cache
        """
        if category_id:
            # Invalidate specific category caches
            cache.delete(f'{cls.CACHE_KEY_PREFIX}:category:{category_id}:ancestors')
            cache.delete(f'{cls.CACHE_KEY_PREFIX}:category:{category_id}:descendants')
            logger.info(f"Invalidated cache for category {category_id}")
        else:
            # Invalidate entire tree
            cache.delete(f'{cls.CACHE_KEY_PREFIX}:full_tree')
            logger.info("Invalidated entire category tree cache")
    
    @classmethod
    def rebuild_cache(cls):
        """
        Rebuild all category caches
        
        Useful for maintenance or after bulk updates
        """
        logger.info("Rebuilding category tree cache")
        cls.get_category_tree_cached(force_refresh=True)


class ProductRecommendationService:
    """
    Service for product recommendations using category DFS
    
    OOP Principle: Separation of concerns - dedicated service for recommendations
    Algorithm: Uses DFS-based category traversal for finding related products
    """
    
    @staticmethod
    def get_recommendations(product: Product, limit: int = 5) -> List[Product]:
        """
        Get product recommendations based on category hierarchy
        
        DFS Algorithm: Uses category DFS traversal to find related products
        """
        if not product.category:
            # Fallback to popular products if no category
            return Product.objects.filter(status='active').exclude(id=product.id)[:limit]
        
        # Use cached category service for efficiency
        related_data = CategoryTreeService.get_related_products_cached(product.id, limit)
        
        if not related_data:
            return Product.objects.none()
        
        # Get full product objects
        product_ids = [p['id'] for p in related_data]
        products = Product.objects.filter(id__in=product_ids)
        
        return products
    
    @staticmethod
    def get_trending_in_category(category: Category, limit: int = 10) -> List[Product]:
        """
        Get trending products in category and subcategories using DFS
        
        DFS: Traverses category tree to get products from all subcategories
        """
        descendant_ids = CategoryTreeService.get_descendant_categories_dfs(category.id)
        category_ids = [category.id] + descendant_ids
        
        # Get products from category and subcategories
        # In real implementation, this would use order count, views, etc.
        products = Product.objects.filter(
            category_id__in=category_ids,
            status='active'
        )[:limit]
        
        return products

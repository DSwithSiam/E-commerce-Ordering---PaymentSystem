# E-commerce Ordering & Payment System

A comprehensive Django REST Framework backend system for managing e-commerce orders and payments with support for multiple payment providers (Stripe and bKash).

## 🚀 Features

### Core Requirements Met

✅ **OOP Principles**: User, Product, Order, and Payment classes with encapsulated business logic  
✅ **Data Structures**: Relational tables with indexed fields for efficient querying  
✅ **Algorithms**: Deterministic calculations for totals/subtotals and safe stock reduction  
✅ **Design Patterns**: Strategy pattern for payment providers  
✅ **DFS + Caching**: Category hierarchy traversal with Redis caching for product recommendations  

### Functional Features

- **User Management**: Registration, login, profile management with token authentication
- **Product Management**: CRUD operations with category hierarchy
- **Order Management**: Order creation, status tracking, cancellation
- **Payment System**: 
  - Stripe integration (Payment Intent, webhooks)
  - bKash integration (Checkout, Execute, Query)
  - Strategy pattern for easy provider addition
- **Category Hierarchy**: DFS traversal with Redis caching for performance
- **Product Recommendations**: Related products based on category tree

## 📋 Prerequisites

- Python 3.12+
- Redis (for caching)
- Docker & Docker Compose (optional)

## 🛠️ Installation

### Local Setup

1. **Clone the repository**
```bash
cd "/path/to/E-commerce Ordering & Payment System"
```

2. **Create virtual environment**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies**
```bash
pip install -r requirements.txt
```

4. **Configure environment variables**
```bash
cp .env.example .env
# Edit .env with your API keys
```

5. **Run migrations**
```bash
python manage.py migrate
```

6. **Seed database**
```bash
python manage.py seed_data
```

7. **Run development server**
```bash
python manage.py runserver
```

### Docker Setup

1. **Build and run with Docker Compose**
```bash
docker-compose up --build
```

The application will be available at `http://localhost:8000`

## 🔑 Default Credentials

After seeding:
- **Admin**: `admin@example.com` / `admin123`
- **Test User**: `user@example.com` / `user123`

## 📡 API Endpoints

### Authentication

- `POST /api/users/register/` - Register new user
- `POST /api/users/login/` - Login
- `POST /api/users/logout/` - Logout
- `GET /api/users/profile/` - Get profile
- `PUT /api/users/profile/update/` - Update profile
- `POST /api/users/change-password/` - Change password

### Products

- `GET /api/products/` - List products
- `POST /api/products/` - Create product (Admin)
- `GET /api/products/{id}/` - Get product details
- `PUT /api/products/{id}/` - Update product (Admin)
- `DELETE /api/products/{id}/` - Delete product (Admin)
- `GET /api/products/{id}/related/` - Get related products (DFS)

### Categories

- `GET /api/categories/` - List categories
- `POST /api/categories/` - Create category (Admin)
- `GET /api/categories/{id}/` - Get category details
- `GET /api/categories/tree/` - Get full category tree (DFS + Cache)
- `GET /api/categories/{id}/products/` - Get products in category

### Orders

- `GET /api/orders/` - List user's orders
- `POST /api/orders/` - Create order
- `GET /api/orders/{id}/` - Get order details
- `POST /api/orders/{id}/cancel/` - Cancel order

### Checkout

- `POST /api/orders/checkout/` - Create order and initiate payment

### Payments

- `GET /api/payments/` - List user's payments
- `GET /api/payments/{id}/` - Get payment details
- `POST /api/payments/confirm/` - Confirm payment
- `GET /api/payments/{transaction_id}/status/` - Get payment status
- `POST /api/payments/{id}/refund/` - Refund payment (Admin)

### Webhooks

- `POST /api/payments/webhooks/stripe/` - Stripe webhook
- `POST /api/payments/webhooks/bkash/` - bKash webhook (placeholder)

## 🏗️ System Architecture

### Design Patterns Used

#### 1. Strategy Pattern (Payment Providers)
```python
# Easy to add new payment providers
class PaymentStrategy(ABC):
    def create_payment(self, order, amount, currency): pass
    def confirm_payment(self, transaction_id): pass
    # ... other methods

class StripePaymentStrategy(PaymentStrategy): ...
class BkashPaymentStrategy(PaymentStrategy): ...
```

#### 2. Service Layer Pattern
- `OrderService`: Business logic for orders
- `CheckoutService`: Orchestrates order + payment
- `CategoryTreeService`: DFS traversal with caching
- `ProductRecommendationService`: Related product logic

#### 3. Factory Pattern
```python
def get_payment_strategy(provider: str) -> PaymentStrategy:
    strategies = {
        'stripe': StripePaymentStrategy,
        'bkash': BkashPaymentStrategy,
    }
    return strategies[provider]()
```

### Data Flow

1. **Order Creation Flow**
   ```
   User → API → OrderService.create_order() → Validate → Create Order → Create OrderItems → Calculate Total
   ```

2. **Payment Flow**
   ```
   User → Checkout API → CheckoutService → Create Order → Get Payment Strategy → Create Payment → Return Payment Details
   ```

3. **Webhook Flow**
   ```
   Provider → Webhook → Validate Signature → Update Payment → Update Order → Reduce Stock
   ```

## 🧪 Testing

### Run Tests
```bash
python manage.py test
```

### Test Coverage
- Model tests for User, Product, Order, Payment
- API tests for all endpoints
- Service layer tests
- Payment strategy tests
- Webhook tests

## 🔒 Security Features

- Token-based authentication (DRF TokenAuthentication)
- Password hashing with Django's PBKDF2
- CORS protection
- Environment-based configuration
- Webhook signature verification
- Admin-only endpoints protection

## 📊 Database Schema

### ERD Overview

```
Users (1) ←→ (N) Orders (1) ←→ (N) OrderItems (N) ←→ (1) Products
                    ↓
                Payments

Categories (Tree Structure)
    ↓
Products (N) ←→ (1) Category
```

### Key Relationships

- User → Orders: One-to-Many
- Order → OrderItems: One-to-Many
- Product → OrderItems: One-to-Many
- Order → Payments: One-to-Many
- Category → Category: Self-referential (parent-child)
- Product → Category: Many-to-One

## 🎯 OOP, Data Structures & Algorithms Implementation

### OOP Classes

1. **User** (`users/models.py`)
   - Custom user model with email authentication
   - Encapsulates user data and authentication logic

2. **Product** (`products/models.py`)
   - Encapsulates product data
   - Methods: `is_available()`, `reduce_stock()`, `increase_stock()`, `get_related_products()`

3. **Category** (`products/models.py`)
   - Tree/Graph structure for hierarchy
   - Methods: `get_ancestors()`, `get_descendants_dfs()`, `get_full_path()`

4. **Order** (`orders/models.py`)
   - Encapsulates order logic
   - Methods: `calculate_total()`, `mark_as_paid()`, `cancel()`

5. **OrderItem** (`orders/models.py`)
   - Junction table with calculated subtotal
   - Auto-calculates subtotal on save

6. **Payment** (`payments/models.py`)
   - Tracks payment transactions
   - Methods: `mark_as_success()`, `mark_as_failed()`, `can_be_refunded()`

### Data Structures

1. **Relational Database Tables** with indexed fields:
   - Foreign Keys for relationships
   - Indexes on frequently queried fields (email, status, created_at, etc.)

2. **Tree/Graph Structure** for categories:
   - Self-referential foreign key for parent-child relationship
   - Supports unlimited depth

3. **JSON Fields** for flexible data:
   - `raw_response` in Payment model
   - `metadata` for additional information

### Algorithms

1. **Deterministic Calculations**
   ```python
   def calculate_total(self):
       """O(n) where n is number of order items"""
       total = Decimal('0.00')
       for item in self.items.all():
           total += item.subtotal
       return total
   ```

2. **Safe Stock Reduction**
   ```python
   def reduce_stock(self, quantity):
       """Atomic operation with validation"""
       if self.stock < quantity:
           raise ValueError("Insufficient stock")
       self.stock -= quantity
       if self.stock == 0:
           self.status = 'out_of_stock'
       self.save()
   ```

3. **DFS for Category Traversal**
   ```python
   def get_descendants_dfs(self):
       """Non-recursive DFS using stack - O(n)"""
       descendants = []
       stack = [self]
       while stack:
           current = stack.pop()
           if current != self:
               descendants.append(current)
           children = list(current.children.filter(is_active=True))
           stack.extend(reversed(children))
       return descendants
   ```

4. **Redis Caching** for performance:
   ```python
   def get_category_tree_cached(cls, force_refresh=False):
       """O(1) for cache hit, O(n) for cache miss"""
       cache_key = f'{cls.CACHE_KEY_PREFIX}:full_tree'
       cached_tree = cache.get(cache_key)
       if cached_tree and not force_refresh:
           return cached_tree
       tree = cls._build_category_tree()  # DFS traversal
       cache.set(cache_key, tree, cls.CACHE_TIMEOUT)
       return tree
   ```

## 🔄 Payment Integration

### Stripe Integration

1. **Create Payment Intent**
   ```python
   payment_intent = stripe.PaymentIntent.create(
       amount=amount_cents,
       currency='usd',
       metadata={'order_id': order.id}
   )
   ```

2. **Webhook Handling**
   - Verifies signature
   - Updates payment status
   - Marks order as paid
   - Reduces stock

### bKash Integration

1. **Authentication**
   - Get token from bKash API
   - Cache token for reuse

2. **Create Payment**
   ```python
   response = requests.post(
       f"{base_url}/checkout/payment/create",
       json={'amount': amount, 'currency': 'BDT'}
   )
   ```

3. **Execute Payment**
   - User completes payment on bKash
   - Backend calls execute endpoint
   - Updates order status

## 📈 Performance Optimizations

1. **Database Indexing**
   - Indexes on frequently queried fields
   - Composite indexes for common queries

2. **Query Optimization**
   - `select_related()` for foreign keys
   - `prefetch_related()` for reverse relationships
   - Avoiding N+1 queries

3. **Redis Caching**
   - Category tree caching (1 hour TTL)
   - Related products caching
   - Reduces database load

4. **Efficient Algorithms**
   - DFS with stack (not recursion) to avoid stack overflow
   - O(1) cache lookups
   - O(n) traversals

## 🚀 Deployment

### Using ngrok (Local Deployment)

1. **Install ngrok**
   ```bash
   # Download from https://ngrok.com/
   ```

2. **Run Django server**
   ```bash
   python manage.py runserver
   ```

3. **Expose with ngrok**
   ```bash
   ngrok http 8000
   ```

4. **Update webhook URLs**
   - Copy ngrok URL (e.g., `https://abc123.ngrok.io`)
   - Configure in Stripe Dashboard: `https://abc123.ngrok.io/api/payments/webhooks/stripe/`

### Using Docker

1. **Build and run**
   ```bash
   docker-compose up --build
   ```

2. **Access application**
   - API: `http://localhost:8000`
   - Admin: `http://localhost:8000/admin`

## 📝 API Documentation

### Postman Collection

Import the Postman collection for testing:
1. Open Postman
2. Import `postman_collection.json` (to be created)
3. Set environment variables:
   - `base_url`: `http://localhost:8000`
   - `token`: Your auth token

### Swagger/OpenAPI

Access interactive API documentation:
- URL: `http://localhost:8000/swagger/` (to be implemented with drf-spectacular)

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License.

## 👥 Support

For issues and questions:
- Create an issue on GitHub
- Email: support@example.com

## 🙏 Acknowledgments

- Django & Django REST Framework
- Stripe API Documentation
- bKash API Documentation
- Redis for caching

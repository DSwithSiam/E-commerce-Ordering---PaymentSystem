# System Architecture & Documentation

## 1. System Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                             │
│  (Mobile App, Web Browser, Third-party Integrations)            │
└────────────────────────┬────────────────────────────────────────┘
                         │
                         ├── HTTP/HTTPS REST API
                         │
┌────────────────────────▼────────────────────────────────────────┐
│                      API GATEWAY LAYER                           │
│                    (Django REST Framework)                       │
│                                                                  │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐       │
│  │  Users   │  │ Products │  │  Orders  │  │ Payments │       │
│  │   API    │  │   API    │  │   API    │  │   API    │       │
│  └─────┬────┘  └─────┬────┘  └─────┬────┘  └─────┬────┘       │
└────────┼─────────────┼─────────────┼─────────────┼─────────────┘
         │             │             │             │
         │             │             │             │
┌────────▼─────────────▼─────────────▼─────────────▼─────────────┐
│                    BUSINESS LOGIC LAYER                          │
│                     (Service Classes)                            │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │   User       │  │   Order      │  │  Checkout    │         │
│  │  Service     │  │  Service     │  │  Service     │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  Category    │  │  Product     │  │  Payment     │         │
│  │   Tree       │  │ Recommend.   │  │  Strategy    │         │
│  │  Service     │  │  Service     │  │  (Factory)   │         │
│  └──────────────┘  └──────────────┘  └──────┬───────┘         │
└──────────────────────────────────────────────┼──────────────────┘
                                               │
                     ┌─────────────────────────┼─────────────┐
                     │                         │             │
              ┌──────▼──────┐          ┌──────▼──────┐      │
              │   Stripe    │          │   bKash     │      │
              │  Strategy   │          │  Strategy   │      │
              └─────────────┘          └─────────────┘      │
                                                             │
┌────────────────────────────────────────────────────────────▼────┐
│                     DATA LAYER                                   │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  PostgreSQL  │  │    Redis     │  │   Celery     │         │
│  │   Database   │  │    Cache     │  │   Worker     │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└──────────────────────────────────────────────────────────────────┘
         │                   │
         │                   │
┌────────▼───────────────────▼──────────────────────────────────┐
│              EXTERNAL SERVICES                                 │
│                                                                │
│    ┌─────────┐            ┌─────────┐                         │
│    │ Stripe  │            │ bKash   │                         │
│    │   API   │            │  API    │                         │
│    └─────────┘            └─────────┘                         │
└────────────────────────────────────────────────────────────────┘
```

## 2. Entity Relationship Diagram (ERD)

```
┌─────────────────────┐
│       Users         │
├─────────────────────┤
│ PK  id             │
│ UQ  email          │
│     first_name     │
│     last_name      │
│     phone          │
│     password       │
│     is_admin       │
│     created_at     │
│     updated_at     │
└──────────┬──────────┘
           │
           │ 1:N
           │
┌──────────▼──────────┐
│       Orders        │
├─────────────────────┤
│ PK  id             │
│ FK  user_id        │
│     total_amount   │
│ IDX status         │
│     notes          │
│ IDX created_at     │
│     updated_at     │
└──────────┬──────────┘
           │
           │ 1:N                ┌─────────────────────┐
           │                    │     Payments        │
           ├────────────────────┤─────────────────────┤
           │                    │ PK  id             │
           │                    │ FK  order_id       │
           │                    │ IDX provider       │
           │                    │ UQ  transaction_id │
           │                    │     amount         │
           │                    │     currency       │
           │                    │ IDX status         │
           │                    │     raw_response   │
           │                    │     error_message  │
           │                    │     metadata       │
           │                    │ IDX created_at     │
           │                    │     updated_at     │
           │                    │     completed_at   │
           │                    └─────────────────────┘
           │
           │ 1:N
           │
┌──────────▼──────────┐
│    OrderItems       │
├─────────────────────┤
│ PK  id             │
│ FK  order_id       │
│ FK  product_id     │
│     quantity       │
│     price          │
│     subtotal       │
│     created_at     │
│     updated_at     │
│ UQ (order,product) │
└──────────┬──────────┘
           │
           │ N:1
           │
┌──────────▼──────────┐
│      Products       │
├─────────────────────┤
│ PK  id             │
│     name           │
│ UQ  sku            │
│ UQ  slug           │
│     description    │
│ IDX price          │
│     stock          │
│ IDX status         │
│ FK  category_id    │
│     image_url      │
│ IDX created_at     │
│     updated_at     │
└──────────┬──────────┘
           │
           │ N:1
           │
┌──────────▼──────────┐
│     Categories      │
├─────────────────────┤
│ PK  id             │
│ UQ  name           │
│ IDX slug           │
│ FK  parent_id      │◄─┐
│     description    │  │ Self-referential
│ IDX is_active      │  │ (Tree Structure)
│     created_at     │  │
│     updated_at     │──┘
└─────────────────────┘

Indexes Legend:
  PK  = Primary Key
  FK  = Foreign Key
  UQ  = Unique
  IDX = Index
```

## 3. Payment Flow Diagram

### Stripe Payment Flow
```
┌──────┐                 ┌──────────┐              ┌─────────┐
│Client│                 │  Backend │              │ Stripe  │
└───┬──┘                 └────┬─────┘              └────┬────┘
    │                         │                         │
    │ 1. POST /checkout       │                         │
    ├────────────────────────►│                         │
    │   items, provider       │                         │
    │                         │                         │
    │                         │ 2. Create Order         │
    │                         ├────────────┐            │
    │                         │            │            │
    │                         │◄───────────┘            │
    │                         │                         │
    │                         │ 3. Create Payment Intent│
    │                         ├────────────────────────►│
    │                         │                         │
    │                         │ 4. Payment Intent       │
    │                         │◄────────────────────────┤
    │                         │    + client_secret      │
    │                         │                         │
    │ 5. Payment Info         │                         │
    │◄────────────────────────┤                         │
    │  {client_secret, etc}   │                         │
    │                         │                         │
    │ 6. Confirm Payment      │                         │
    ├─────────────────────────┼────────────────────────►│
    │   (Stripe.js)           │                         │
    │                         │                         │
    │                         │ 7. Webhook Event        │
    │                         │◄────────────────────────┤
    │                         │  payment_intent.success │
    │                         │                         │
    │                         │ 8. Update Order         │
    │                         ├────────────┐            │
    │                         │ - Mark Paid│            │
    │                         │ - Reduce   │            │
    │                         │   Stock    │            │
    │                         │◄───────────┘            │
    │                         │                         │
    │ 9. Success Response     │                         │
    │◄────────────────────────┤                         │
    │                         │                         │
```

### bKash Payment Flow
```
┌──────┐                 ┌──────────┐              ┌─────────┐
│Client│                 │  Backend │              │  bKash  │
└───┬──┘                 └────┬─────┘              └────┬────┘
    │                         │                         │
    │ 1. POST /checkout       │                         │
    ├────────────────────────►│                         │
    │   items, provider       │                         │
    │                         │                         │
    │                         │ 2. Create Order         │
    │                         ├────────────┐            │
    │                         │            │            │
    │                         │◄───────────┘            │
    │                         │                         │
    │                         │ 3. Get Token            │
    │                         ├────────────────────────►│
    │                         │                         │
    │                         │ 4. Token                │
    │                         │◄────────────────────────┤
    │                         │                         │
    │                         │ 5. Create Payment       │
    │                         ├────────────────────────►│
    │                         │                         │
    │                         │ 6. Payment ID + bkashURL│
    │                         │◄────────────────────────┤
    │                         │                         │
    │ 7. bKash URL            │                         │
    │◄────────────────────────┤                         │
    │                         │                         │
    │ 8. Redirect to bKash    │                         │
    ├─────────────────────────┼────────────────────────►│
    │                         │                         │
    │ 9. Complete Payment     │                         │
    │         (OTP)           │                         │
    │                         │                         │
    │ 10. Callback            │                         │
    ├────────────────────────►│                         │
    │                         │                         │
    │                         │ 11. Execute Payment     │
    │                         ├────────────────────────►│
    │                         │                         │
    │                         │ 12. Success Response    │
    │                         │◄────────────────────────┤
    │                         │                         │
    │                         │ 13. Update Order        │
    │                         ├────────────┐            │
    │                         │ - Mark Paid│            │
    │                         │ - Reduce   │            │
    │                         │   Stock    │            │
    │                         │◄───────────┘            │
    │                         │                         │
    │ 14. Success Response    │                         │
    │◄────────────────────────┤                         │
    │                         │                         │
```

## 4. Category Tree DFS Traversal

### Category Hierarchy Example
```
Electronics
├── Computers
│   ├── Laptops
│   └── Computer Accessories
└── Mobile Phones

Clothing
├── Men's Clothing
└── Women's Clothing

Books

Home & Garden
```

### DFS Traversal Algorithm
```python
def get_descendants_dfs(self):
    """
    Non-recursive DFS using stack
    Time Complexity: O(n) where n = number of descendants
    Space Complexity: O(h) where h = tree height
    """
    descendants = []
    stack = [self]
    
    while stack:
        current = stack.pop()
        if current != self:
            descendants.append(current)
        
        # Add children in reverse order for consistent traversal
        children = list(current.children.filter(is_active=True))
        stack.extend(reversed(children))
    
    return descendants
```

### Caching Strategy
```python
# Cache Key Structure
category_tree:full_tree              → Full tree (1 hour TTL)
category_tree:category:1:ancestors   → Category ancestors
category_tree:category:1:descendants → Category descendants
category_tree:product:5:related:5    → Related products

# Cache Hit: O(1)
# Cache Miss: O(n) + cache write
```

## 5. Class Diagram (OOP Structure)

```
┌────────────────────────────────────────────────────────────────┐
│                   AbstractPaymentStrategy                       │
│                        <<abstract>>                             │
├────────────────────────────────────────────────────────────────┤
│ + create_payment(order, amount, currency)                      │
│ + confirm_payment(transaction_id)                              │
│ + get_payment_status(transaction_id)                           │
│ + refund_payment(transaction_id, amount)                       │
│ + handle_webhook(payload, signature)                           │
└───────────────────────┬────────────────────────────────────────┘
                        │
         ┌──────────────┴──────────────┐
         │                             │
┌────────▼─────────┐         ┌─────────▼────────┐
│ StripeStrategy   │         │  BkashStrategy   │
├──────────────────┤         ├──────────────────┤
│ - api_key        │         │ - app_key        │
│ - webhook_secret │         │ - app_secret     │
├──────────────────┤         │ - token          │
│ + create_payment │         ├──────────────────┤
│ + confirm_payment│         │ + create_payment │
│ + ...            │         │ + confirm_payment│
└──────────────────┘         │ + _get_token     │
                             │ + ...            │
                             └──────────────────┘

┌──────────────────────┐
│  PaymentContext      │
├──────────────────────┤
│ - strategy           │
├──────────────────────┤
│ + set_strategy()     │
│ + create_payment()   │
│ + confirm_payment()  │
│ + ...                │
└──────────────────────┘

┌──────────────────────┐
│   OrderService       │
├──────────────────────┤
│ + create_order()     │
│ + get_user_orders()  │
│ + cancel_order()     │
│ + calculate_summary()│
└──────────────────────┘

┌──────────────────────┐
│  CheckoutService     │
├──────────────────────┤
│ + create_order_and_  │
│   initiate_payment() │
└──────────────────────┘

┌──────────────────────┐
│ CategoryTreeService  │
├──────────────────────┤
│ + get_tree_cached()  │
│ + get_descendants_   │
│   dfs()              │
│ + invalidate_cache() │
└──────────────────────┘
```

## 6. API Request/Response Examples

### User Registration
**Request:**
```http
POST /api/users/register/
Content-Type: application/json

{
  "email": "john@example.com",
  "password": "SecurePass123",
  "password_confirm": "SecurePass123",
  "first_name": "John",
  "last_name": "Doe",
  "phone": "+1234567890"
}
```

**Response:**
```json
{
  "user": {
    "id": 3,
    "email": "john@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "phone": "+1234567890",
    "is_admin": false,
    "created_at": "2025-12-27T10:30:00Z"
  },
  "token": "9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b",
  "message": "User registered successfully"
}
```

### Checkout (Order + Payment)
**Request:**
```http
POST /api/orders/checkout/
Authorization: Token 9944b09199c62bcf9418ad846dd0e4bbdfc6ee4b
Content-Type: application/json

{
  "items": [
    {"product_id": 1, "quantity": 2},
    {"product_id": 5, "quantity": 1}
  ],
  "payment_provider": "stripe",
  "notes": "Please deliver by Friday"
}
```

**Response:**
```json
{
  "success": true,
  "order_id": 15,
  "payment_id": 8,
  "transaction_id": "pi_3O8JQ2H3v9KLm6Wd1X2Y3Z4A",
  "amount": "5849.97",
  "currency": "USD",
  "provider": "stripe",
  "client_secret": "pi_3O8JQ2H3v9KLm6Wd1X2Y3Z4A_secret_abc123"
}
```

### Get Category Tree
**Request:**
```http
GET /api/categories/tree/
```

**Response:**
```json
[
  {
    "id": 1,
    "name": "Electronics",
    "slug": "electronics",
    "description": "Electronic devices and accessories",
    "children": [
      {
        "id": 5,
        "name": "Computers",
        "slug": "computers",
        "description": "Computers and computer accessories",
        "children": [
          {
            "id": 7,
            "name": "Laptops",
            "slug": "laptops",
            "description": "Laptop computers",
            "children": []
          },
          {
            "id": 8,
            "name": "Computer Accessories",
            "slug": "computer-accessories",
            "description": "Mouse, keyboard, and other accessories",
            "children": []
          }
        ]
      }
    ]
  }
]
```

## 7. Deployment Architecture

### Production Setup
```
                    ┌─────────────┐
                    │   Internet  │
                    └──────┬──────┘
                           │
                    ┌──────▼──────┐
                    │   Nginx     │
                    │  (Reverse   │
                    │   Proxy)    │
                    └──────┬──────┘
                           │
          ┌────────────────┼────────────────┐
          │                │                │
    ┌─────▼─────┐   ┌──────▼──────┐  ┌─────▼─────┐
    │  Gunicorn │   │  Gunicorn   │  │ Gunicorn  │
    │  Worker 1 │   │  Worker 2   │  │ Worker 3  │
    └─────┬─────┘   └──────┬──────┘  └─────┬─────┘
          │                │                │
          └────────────────┼────────────────┘
                           │
                    ┌──────▼──────┐
                    │  PostgreSQL │
                    │   Database  │
                    └─────────────┘
                           │
                    ┌──────▼──────┐
                    │    Redis    │
                    │    Cache    │
                    └─────────────┘
```

## 8. Security Measures

### Authentication Flow
```
1. User Login → Generate Token (PBKDF2 hash)
2. Store Token in Database
3. Client includes Token in Authorization header
4. Backend validates Token on each request
5. Token expires after logout
```

### Payment Security
```
1. API keys stored in environment variables
2. Webhook signature verification
3. HTTPS/TLS for all communications
4. PCI DSS compliance (Stripe handles card data)
5. No credit card data stored in database
```

### Data Protection
```
1. Password hashing (PBKDF2 + salt)
2. SQL injection prevention (ORM parameterized queries)
3. CORS configuration
4. Rate limiting (to be implemented)
5. Input validation on all endpoints
```

## 9. Monitoring & Logging

### Log Structure
```
logs/
  ecommerce.log      # General application logs
  
Log Format:
[LEVEL] [TIMESTAMP] [MODULE] MESSAGE

Example:
INFO 2025-12-27 10:30:15 payments Payment 123 created successfully
ERROR 2025-12-27 10:31:22 payments Stripe error: Invalid API key
DEBUG 2025-12-27 10:32:45 orders Order 456 total calculated: $129.99
```

### Key Metrics to Monitor
- API response times
- Payment success/failure rates
- Database query performance
- Cache hit rates
- Order conversion rates
- Stock levels
- Error rates

## 10. Future Enhancements

### Planned Features
1. **Payment Providers**: PayPal, Razorpay, etc.
2. **Notifications**: Email/SMS for order updates
3. **Reviews & Ratings**: Product review system
4. **Wishlist**: Save products for later
5. **Coupons & Discounts**: Promotional codes
6. **Inventory Alerts**: Low stock notifications
7. **Analytics Dashboard**: Sales reports
8. **Multi-currency**: Support for multiple currencies
9. **Shipping Integration**: Real-time shipping rates
10. **Tax Calculation**: Location-based tax

### Scalability Considerations
- Implement message queue (RabbitMQ/Kafka)
- Microservices architecture
- CDN for static content
- Database replication
- Horizontal scaling with load balancer
- Elasticsearch for product search
- GraphQL API option

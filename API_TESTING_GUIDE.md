# API Testing Guide

## Postman Collection

### Environment Variables
Set these variables in your Postman environment:
- `base_url`: `http://localhost:8000`
- `token`: Your authentication token (obtained from login)
- `user_email`: `user@example.com`
- `admin_email`: `admin@example.com`

## API Endpoints Collection

### 1. User Authentication

#### 1.1 Register User
```
POST {{base_url}}/api/users/register/
Content-Type: application/json

{
  "email": "newuser@example.com",
  "password": "SecurePass123",
  "password_confirm": "SecurePass123",
  "first_name": "John",
  "last_name": "Doe",
  "phone": "+1234567890"
}
```

#### 1.2 Login
```
POST {{base_url}}/api/users/login/
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "user123"
}
```
**Response:** Save the `token` to environment variable

#### 1.3 Get Profile
```
GET {{base_url}}/api/users/profile/
Authorization: Token {{token}}
```

#### 1.4 Update Profile
```
PATCH {{base_url}}/api/users/profile/update/
Authorization: Token {{token}}
Content-Type: application/json

{
  "first_name": "Updated",
  "phone": "+9876543210"
}
```

#### 1.5 Change Password
```
POST {{base_url}}/api/users/change-password/
Authorization: Token {{token}}
Content-Type: application/json

{
  "old_password": "user123",
  "new_password": "NewSecurePass123",
  "new_password_confirm": "NewSecurePass123"
}
```

#### 1.6 Logout
```
POST {{base_url}}/api/users/logout/
Authorization: Token {{token}}
```

---

### 2. Products

#### 2.1 List Products
```
GET {{base_url}}/api/products/
# Optional query parameters:
# ?status=active
# ?category=1
# ?min_price=100
# ?max_price=1000
# ?available=true
# ?search=laptop
```

#### 2.2 Get Product Details
```
GET {{base_url}}/api/products/1/
```

#### 2.3 Create Product (Admin Only)
```
POST {{base_url}}/api/products/
Authorization: Token {{admin_token}}
Content-Type: application/json

{
  "name": "New Laptop Model",
  "sku": "LAPTOP-999",
  "slug": "new-laptop-model",
  "description": "Latest laptop with amazing features",
  "price": "1599.99",
  "stock": 25,
  "status": "active",
  "category": 7,
  "image_url": "https://example.com/laptop.jpg"
}
```

#### 2.4 Update Product (Admin Only)
```
PATCH {{base_url}}/api/products/1/
Authorization: Token {{admin_token}}
Content-Type: application/json

{
  "price": "1499.99",
  "stock": 30
}
```

#### 2.5 Delete Product (Admin Only)
```
DELETE {{base_url}}/api/products/1/
Authorization: Token {{admin_token}}
```

#### 2.6 Get Related Products
```
GET {{base_url}}/api/products/1/related/
```

---

### 3. Categories

#### 3.1 List Categories
```
GET {{base_url}}/api/categories/
# Optional query parameters:
# ?parent=1
# ?parent=null (get root categories)
```

#### 3.2 Get Category Details
```
GET {{base_url}}/api/categories/1/
```

#### 3.3 Get Category Tree (DFS + Cache)
```
GET {{base_url}}/api/categories/tree/
# Optional: ?refresh=true (to force cache refresh)
```

#### 3.4 Get Products in Category
```
GET {{base_url}}/api/categories/1/products/
# Optional: ?include_subcategories=true (default)
```

#### 3.5 Create Category (Admin Only)
```
POST {{base_url}}/api/categories/
Authorization: Token {{admin_token}}
Content-Type: application/json

{
  "name": "New Category",
  "slug": "new-category",
  "description": "Description here",
  "parent": null,
  "is_active": true
}
```

---

### 4. Orders

#### 4.1 List User Orders
```
GET {{base_url}}/api/orders/
Authorization: Token {{token}}
# Optional: ?status=pending
```

#### 4.2 Get Order Details
```
GET {{base_url}}/api/orders/1/
Authorization: Token {{token}}
```

#### 4.3 Create Order
```
POST {{base_url}}/api/orders/
Authorization: Token {{token}}
Content-Type: application/json

{
  "items": [
    {
      "product_id": 1,
      "quantity": 2
    },
    {
      "product_id": 5,
      "quantity": 1
    }
  ],
  "notes": "Please deliver by Friday"
}
```

#### 4.4 Cancel Order
```
POST {{base_url}}/api/orders/1/cancel/
Authorization: Token {{token}}
```

---

### 5. Checkout (Order + Payment)

#### 5.1 Checkout with Stripe
```
POST {{base_url}}/api/orders/checkout/
Authorization: Token {{token}}
Content-Type: application/json

{
  "items": [
    {
      "product_id": 1,
      "quantity": 2
    },
    {
      "product_id": 5,
      "quantity": 1
    }
  ],
  "payment_provider": "stripe",
  "notes": "Optional notes"
}
```
**Response:** Save `client_secret` for Stripe.js confirmation

#### 5.2 Checkout with bKash
```
POST {{base_url}}/api/orders/checkout/
Authorization: Token {{token}}
Content-Type: application/json

{
  "items": [
    {
      "product_id": 1,
      "quantity": 1
    }
  ],
  "payment_provider": "bkash",
  "notes": "Optional notes"
}
```
**Response:** Redirect user to `bkash_url` for payment

---

### 6. Payments

#### 6.1 List User Payments
```
GET {{base_url}}/api/payments/
Authorization: Token {{token}}
# Optional: ?provider=stripe&status=success
```

#### 6.2 Get Payment Details
```
GET {{base_url}}/api/payments/1/
Authorization: Token {{token}}
```

#### 6.3 Confirm Payment (bKash Execute)
```
POST {{base_url}}/api/payments/confirm/
Authorization: Token {{token}}
Content-Type: application/json

{
  "transaction_id": "TRX123456789"
}
```

#### 6.4 Get Payment Status
```
GET {{base_url}}/api/payments/pi_test_123/status/
Authorization: Token {{token}}
```

#### 6.5 Refund Payment (Admin Only)
```
POST {{base_url}}/api/payments/1/refund/
Authorization: Token {{admin_token}}
Content-Type: application/json

{
  "amount": "50.00",
  "reason": "Customer request"
}
```

---

### 7. Webhooks (For testing with ngrok)

#### 7.1 Stripe Webhook
```
POST {{base_url}}/api/payments/webhooks/stripe/
Stripe-Signature: {{stripe_signature}}
Content-Type: application/json

{
  "id": "evt_test_123",
  "type": "payment_intent.succeeded",
  "data": {
    "object": {
      "id": "pi_test_123",
      "amount": 9999,
      "currency": "usd",
      "status": "succeeded"
    }
  }
}
```

#### 7.2 bKash Webhook
```
POST {{base_url}}/api/payments/webhooks/bkash/
Content-Type: application/json

{
  "paymentID": "TRX123456789",
  "transactionStatus": "Completed"
}
```

---

## Testing Workflow

### Complete Purchase Flow Test

1. **Register/Login**
   ```
   POST /api/users/login/
   ```
   → Save token

2. **Browse Products**
   ```
   GET /api/products/
   GET /api/categories/tree/
   GET /api/categories/1/products/
   ```

3. **View Product Details**
   ```
   GET /api/products/1/
   GET /api/products/1/related/
   ```

4. **Checkout with Stripe**
   ```
   POST /api/orders/checkout/
   {
     "items": [{"product_id": 1, "quantity": 2}],
     "payment_provider": "stripe"
   }
   ```
   → Save client_secret

5. **Confirm Payment (Frontend with Stripe.js)**
   ```javascript
   // In your frontend
   const {error} = await stripe.confirmCardPayment(client_secret, {
     payment_method: {
       card: cardElement,
       billing_details: {email: 'user@example.com'}
     }
   });
   ```

6. **Webhook receives payment_intent.succeeded**
   - Order marked as paid
   - Stock reduced automatically

7. **Check Order Status**
   ```
   GET /api/orders/{order_id}/
   ```
   → Status should be 'paid'

8. **View Payment Details**
   ```
   GET /api/payments/
   GET /api/payments/{payment_id}/
   ```

---

## Admin Testing

### Admin Workflow

1. **Login as Admin**
   ```
   POST /api/users/login/
   {
     "email": "admin@example.com",
     "password": "admin123"
   }
   ```

2. **Manage Products**
   ```
   POST /api/products/ (Create)
   PATCH /api/products/1/ (Update)
   DELETE /api/products/1/ (Delete)
   ```

3. **Manage Categories**
   ```
   POST /api/categories/
   PATCH /api/categories/1/
   ```

4. **View All Orders**
   ```
   GET /api/orders/
   ```

5. **Refund Payment**
   ```
   POST /api/payments/1/refund/
   ```

---

## Error Handling Test Cases

### 1. Authentication Errors
```
GET /api/orders/ (without token)
→ 401 Unauthorized
```

### 2. Validation Errors
```
POST /api/orders/checkout/
{
  "items": [],  # Empty items
  "payment_provider": "stripe"
}
→ 400 Bad Request
```

### 3. Insufficient Stock
```
POST /api/orders/checkout/
{
  "items": [{"product_id": 1, "quantity": 9999}],
  "payment_provider": "stripe"
}
→ 400 Bad Request: "Insufficient stock"
```

### 4. Permission Errors
```
POST /api/products/ (as regular user)
→ 403 Forbidden
```

### 5. Not Found
```
GET /api/products/99999/
→ 404 Not Found
```

---

## Performance Testing

### 1. Category Tree Caching
```
# First request (cache miss)
GET /api/categories/tree/
→ Check response time

# Second request (cache hit)
GET /api/categories/tree/
→ Should be significantly faster
```

### 2. Related Products (DFS)
```
GET /api/products/1/related/
→ Uses cached category descendants
```

### 3. Force Cache Refresh
```
GET /api/categories/tree/?refresh=true
→ Rebuilds cache
```

---

## Stripe Testing

### Test Card Numbers
```
Success: 4242 4242 4242 4242
Decline: 4000 0000 0000 0002
Insufficient Funds: 4000 0000 0000 9995
```

### Test Expiry: Any future date (e.g., 12/25)
### Test CVV: Any 3 digits (e.g., 123)

---

## bKash Testing

### Sandbox Credentials
```
Wallet: 01XXXXXXXXX
OTP: 123456 (sandbox)
PIN: 12345 (sandbox)
```

Note: Use sandbox credentials provided by bKash for testing.

---

## Monitoring & Logging

### Check Logs
```bash
# View application logs
tail -f logs/ecommerce.log

# Filter payment logs
grep "payments" logs/ecommerce.log

# Filter errors
grep "ERROR" logs/ecommerce.log
```

---

## Tips for Testing

1. **Use Postman Collections**: Import all requests into a collection
2. **Set Environment Variables**: Use {{variables}} for reusable values
3. **Test Scripts**: Add tests in Postman to automate validation
4. **Sequential Testing**: Test complete flows, not just individual endpoints
5. **Error Scenarios**: Test all error cases, not just happy paths
6. **Performance**: Monitor response times and cache effectiveness
7. **Webhooks**: Use ngrok to test webhooks locally

---

## Sample Postman Test Scripts

```javascript
// Save token from login response
pm.environment.set("token", pm.response.json().token);

// Test status code
pm.test("Status code is 200", function () {
    pm.response.to.have.status(200);
});

// Test response structure
pm.test("Response has user object", function () {
    var jsonData = pm.response.json();
    pm.expect(jsonData).to.have.property('user');
    pm.expect(jsonData.user).to.have.property('email');
});

// Test response time
pm.test("Response time is less than 200ms", function () {
    pm.expect(pm.response.responseTime).to.be.below(200);
});
```

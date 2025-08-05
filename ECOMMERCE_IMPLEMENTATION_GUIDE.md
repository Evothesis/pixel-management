# SecurePixel E-commerce & Conversion Tracking Implementation Guide

## 🚀 Quick Start

### 1. Install SecurePixel
Add to your website's `<head>` section:
```html
<script src="https://pixel-management-275731808857.us-central1.run.app/pixel/{YOUR_CLIENT_ID}/tracking.js" async></script>
```

**📝 Replace these values:**
- `{YOUR_CLIENT_ID}` → Your actual client ID from SecurePixel Management dashboard

### 2. Verify Installation
Open browser console and look for:
```
[SecurePixel] Analytics pixel loaded for client: {your_actual_client_id}
[SecurePixel] DataLayer integration active
```

---

## 📊 E-commerce Tracking Methods

### Purchase Tracking
```javascript
// Track completed orders
securepixel.trackPurchase({
    order_id: '{ORDER_ID}',           // Required: Your order/transaction ID
    revenue: {TOTAL_AMOUNT},          // Required: Total order value (number, no currency symbols)
    currency: '{CURRENCY_CODE}',      // Optional: 3-letter currency code (default: 'USD')
    products: [                       // Optional: Array of purchased products
        {
            sku: '{PRODUCT_SKU}',         // Product SKU/ID
            name: '{PRODUCT_NAME}',       // Product name
            price: {UNIT_PRICE},          // Price per unit (number)
            quantity: {QUANTITY},         // Quantity purchased (integer)
            category: '{CATEGORY_NAME}'   // Product category
        }
        // ... more products
    ],
    shipping: {SHIPPING_COST},        // Optional: Shipping amount (number)
    tax: {TAX_AMOUNT},               // Optional: Tax amount (number)
    customer_type: '{CUSTOMER_TYPE}', // Optional: 'new' or 'returning'
    coupon_code: '{COUPON_CODE}'     // Optional: Discount code used
});
```

**📝 Replace these placeholders:**
- `{ORDER_ID}` → Your order ID (e.g., `'12345'`, `'ORD-2024-001'`)
- `{TOTAL_AMOUNT}` → Order total as number (e.g., `99.99`, `156.50`)
- `{CURRENCY_CODE}` → Currency code (e.g., `'USD'`, `'EUR'`, `'GBP'`)
- `{PRODUCT_SKU}` → Product SKU (e.g., `'TSHIRT-M-BLU'`, `'WIDGET-001'`)
- `{PRODUCT_NAME}` → Product name (e.g., `'Blue T-Shirt Medium'`)
- `{UNIT_PRICE}` → Price per item (e.g., `29.99`, `45.00`)
- `{QUANTITY}` → Number of items (e.g., `1`, `2`, `5`)
- `{CATEGORY_NAME}` → Product category (e.g., `'Clothing'`, `'Electronics'`)
- `{SHIPPING_COST}` → Shipping cost (e.g., `5.99`, `0`)
- `{TAX_AMOUNT}` → Tax amount (e.g., `8.50`, `12.75`)
- `{CUSTOMER_TYPE}` → Either `'new'` or `'returning'`
- `{COUPON_CODE}` → Coupon code (e.g., `'SAVE10'`, `'WELCOME20'`)

### Product View Tracking
```javascript
// Track product page views
securepixel.trackProduct({
    sku: '{PRODUCT_SKU}',             // Required: Product SKU/ID
    name: '{PRODUCT_NAME}',           // Optional: Product name
    price: {PRODUCT_PRICE},           // Optional: Product price (number)
    category: '{PRODUCT_CATEGORY}',   // Optional: Product category
    brand: '{PRODUCT_BRAND}',         // Optional: Product brand
    currency: '{CURRENCY_CODE}',      // Optional: Currency code (default: 'USD')
    in_stock: {STOCK_STATUS}          // Optional: true/false stock status
});
```

**📝 Replace these placeholders:**
- `{PRODUCT_SKU}` → Product SKU (e.g., `'TSHIRT-M-BLU'`, `'12345'`)
- `{PRODUCT_NAME}` → Product name (e.g., `'Blue T-Shirt Medium'`)
- `{PRODUCT_PRICE}` → Product price (e.g., `29.99`, `45.00`)
- `{PRODUCT_CATEGORY}` → Category (e.g., `'Clothing'`, `'Electronics'`)
- `{PRODUCT_BRAND}` → Brand name (e.g., `'Nike'`, `'Apple'`)
- `{CURRENCY_CODE}` → Currency (e.g., `'USD'`, `'EUR'`)
- `{STOCK_STATUS}` → `true` or `false` (no quotes)

### Shopping Cart Events
```javascript
// Add to cart
securepixel.trackAddToCart({
    sku: '{PRODUCT_SKU}',             // Required: Product SKU/ID
    name: '{PRODUCT_NAME}',           // Optional: Product name
    price: {UNIT_PRICE},              // Optional: Price per unit (number)
    quantity: {QUANTITY},             // Optional: Quantity added (integer, default: 1)
    currency: '{CURRENCY_CODE}',      // Optional: Currency code (default: 'USD')
    cart_value: {TOTAL_CART_VALUE}    // Optional: Total cart value after addition
});

// Remove from cart
securepixel.trackRemoveFromCart({
    sku: '{PRODUCT_SKU}',             // Required: Product SKU/ID
    quantity: {QUANTITY},             // Optional: Quantity removed (integer)
    price: {UNIT_PRICE}               // Optional: Price per unit (number)
});

// Begin checkout
securepixel.trackBeginCheckout({
    cart_value: {CART_TOTAL},         // Required: Total cart value (number)
    currency: '{CURRENCY_CODE}',      // Optional: Currency code (default: 'USD')
    item_count: {TOTAL_ITEMS}         // Optional: Total number of items (integer)
});
```

**📝 Replace these placeholders:**
- `{PRODUCT_SKU}` → Product SKU being added/removed
- `{PRODUCT_NAME}` → Product name
- `{UNIT_PRICE}` → Price per item (e.g., `29.99`, `15.50`)
- `{QUANTITY}` → Number of items (e.g., `1`, `2`, `3`)
- `{CURRENCY_CODE}` → Currency code (e.g., `'USD'`, `'EUR'`)
- `{TOTAL_CART_VALUE}` → Cart total after addition (e.g., `89.97`, `156.50`)
- `{CART_TOTAL}` → Total cart value (e.g., `125.50`, `89.99`)
- `{TOTAL_ITEMS}` → Total items in cart (e.g., `3`, `7`)

---

## 🎯 Lead & Conversion Tracking

### Lead Form Tracking
```javascript
// Manual lead tracking
securepixel.trackLead({
    form_id: '{FORM_ID}',              // Required: Form identifier
    lead_type: '{LEAD_TYPE}',          // Required: Type of lead (contact, demo, trial, quote, etc.)
    lead_value: {LEAD_VALUE},          // Optional: Estimated value (number)
    source: '{LEAD_SOURCE}',           // Optional: Lead source
    campaign: '{CAMPAIGN_NAME}'        // Optional: Campaign identifier
});
```

### Automatic Lead Detection
SecurePixel automatically detects lead forms with these indicators:
- Form IDs containing: `contact`, `lead`, `quote`, `demo`, `trial`
- Form classes containing: `lead-form`
- Data attributes: `data-securepixel-lead="true"`

**📝 Replace these placeholders:**
- `{FORM_ID}` → Your form ID (e.g., `'contact-form'`, `'demo-request'`)
- `{LEAD_TYPE}` → Lead type (e.g., `'contact'`, `'demo'`, `'trial'`, `'quote'`)
- `{LEAD_VALUE}` → Estimated lead value (e.g., `100`, `500`, `1000`)
- `{LEAD_SOURCE}` → Lead source (e.g., `'website'`, `'landing-page'`, `'blog'`)
- `{CAMPAIGN_NAME}` → Campaign name (e.g., `'summer-promo'`, `'black-friday'`)

**Enhanced Form Example:**
```html
<form id="{YOUR_FORM_ID}" 
      data-securepixel-lead="true" 
      data-lead-type="{YOUR_LEAD_TYPE}" 
      data-lead-value="{YOUR_LEAD_VALUE}">
    <input type="text" name="name" required>
    <input type="email" name="email" required>
    <button type="submit">Submit</button>
</form>
```

### Conversion Goals
```javascript
// Track custom conversions
securepixel.trackConversion({
    conversion_type: '{CONVERSION_TYPE}',  // Required: Type of conversion
    value: {CONVERSION_VALUE},             // Optional: Conversion value (number)
    currency: '{CURRENCY_CODE}',           // Optional: Currency code (default: 'USD')
    goal_id: '{GOAL_ID}'                   // Optional: Goal identifier
});

// Track subscriptions
securepixel.trackSubscription({
    plan: '{SUBSCRIPTION_PLAN}',           // Required: Plan name/ID
    value: {SUBSCRIPTION_VALUE},           // Required: Subscription value (number)
    currency: '{CURRENCY_CODE}',           // Optional: Currency code (default: 'USD')
    billing_cycle: '{BILLING_CYCLE}',      // Optional: Billing cycle (monthly, yearly, etc.)
    trial_days: {TRIAL_DAYS}               // Optional: Trial period in days (integer)
});
```

**📝 Replace these placeholders:**
- `{CONVERSION_TYPE}` → Conversion type (e.g., `'newsletter_signup'`, `'demo_request'`)
- `{CONVERSION_VALUE}` → Value (e.g., `25`, `100`, `500`)
- `{CURRENCY_CODE}` → Currency (e.g., `'USD'`, `'EUR'`, `'GBP'`)
- `{GOAL_ID}` → Goal ID (e.g., `'newsletter_goal_1'`, `'signup_goal'`)
- `{SUBSCRIPTION_PLAN}` → Plan name (e.g., `'pro'`, `'premium'`, `'basic'`)
- `{SUBSCRIPTION_VALUE}` → Plan price (e.g., `29.99`, `99.00`)
- `{BILLING_CYCLE}` → Cycle (e.g., `'monthly'`, `'yearly'`, `'quarterly'`)
- `{TRIAL_DAYS}` → Trial days (e.g., `14`, `30`, `7`)
```

---

## 🔄 DataLayer Integration (Automatic)

SecurePixel automatically processes standard e-commerce dataLayer events:

### Purchase Events
```javascript
dataLayer.push({
    'event': 'purchase',
    'ecommerce': {
        'transaction_id': '{TRANSACTION_ID}',     // Your order/transaction ID
        'value': {TOTAL_VALUE},                   // Total order value (number)
        'currency': '{CURRENCY_CODE}',            // Currency code (e.g., 'USD')
        'items': [
            {
                'item_id': '{ITEM_SKU}',              // Product SKU/ID
                'item_name': '{ITEM_NAME}',           // Product name
                'price': {ITEM_PRICE},                // Price per item (number)
                'quantity': {ITEM_QUANTITY}           // Quantity (integer)
            }
            // ... more items
        ]
    }
});
```

**📝 Replace these placeholders:**
- `{TRANSACTION_ID}` → Order ID (e.g., `'ORD-12345'`, `'TXN-789'`)
- `{TOTAL_VALUE}` → Order total (e.g., `99.99`, `156.50`)
- `{CURRENCY_CODE}` → Currency (e.g., `'USD'`, `'EUR'`)
- `{ITEM_SKU}` → Product SKU (e.g., `'WIDGET-123'`, `'PROD-456'`)
- `{ITEM_NAME}` → Product name (e.g., `'Blue Widget'`, `'Premium Plan'`)
- `{ITEM_PRICE}` → Item price (e.g., `49.99`, `25.00`)
- `{ITEM_QUANTITY}` → Quantity (e.g., `1`, `2`, `5`)
```

### Product & Cart Events
```javascript
// Product view
dataLayer.push({
    'event': 'view_item',
    'ecommerce': {
        'currency': '{CURRENCY_CODE}',            // Currency code
        'value': {PRODUCT_VALUE},                 // Product value (number)
        'items': [{ 
            'item_id': '{PRODUCT_SKU}',           // Product SKU/ID
            'item_name': '{PRODUCT_NAME}'         // Product name
        }]
    }
});

// Add to cart
dataLayer.push({
    'event': 'add_to_cart',
    'ecommerce': {
        'currency': '{CURRENCY_CODE}',            // Currency code
        'value': {CART_VALUE},                    // Cart value after addition (number)
        'items': [{ 
            'item_id': '{PRODUCT_SKU}',           // Product SKU/ID
            'quantity': {QUANTITY}                // Quantity added (integer)
        }]
    }
});
```

**📝 Replace these placeholders:**
- `{CURRENCY_CODE}` → Currency (e.g., `'USD'`, `'EUR'`, `'GBP'`)
- `{PRODUCT_VALUE}` → Product price (e.g., `49.99`, `25.00`)
- `{PRODUCT_SKU}` → Product SKU (e.g., `'WIDGET-123'`, `'ITEM-456'`)
- `{PRODUCT_NAME}` → Product name (e.g., `'Blue Widget'`, `'Premium Service'`)
- `{CART_VALUE}` → Total cart value (e.g., `49.99`, `125.50`)
- `{QUANTITY}` → Item quantity (e.g., `1`, `2`, `3`)
```

---

## 🛍️ Platform-Specific Integration

### Shopify
Use the provided `shopify-integration.liquid` template:
1. Add SecurePixel script to `theme.liquid`
2. Add tracking code to `checkout.liquid`
3. Add product view tracking to `product.liquid`

**Key Features:**
- Automatic purchase tracking on order confirmation
- Product view tracking on product pages
- Cart event tracking via Shopify's cart API

### WooCommerce
Use the provided `woocommerce-integration.php`:
1. Add to your theme's `functions.php`
2. Replace `{CLIENT_ID}` with your client ID

**Key Features:**
- Purchase tracking on order received page
- Product view tracking on product pages
- AJAX add-to-cart tracking
- Contact Form 7 lead tracking integration

### Custom E-commerce
Use the `generic-ecommerce.html` examples for:
- Manual tracking implementation
- DataLayer setup
- Lead form enhancement
- Product page tracking

---

## 🔒 Privacy & Compliance

### GDPR Compliance
SecurePixel automatically applies privacy filters for GDPR clients:
- IP address hashing
- PII field filtering
- Consent-based tracking

### Data Attributes for Control
```html
<!-- Disable tracking for specific forms -->
<form data-securepixel-ignore="true">...</form>

<!-- Set lead value -->
<form data-lead-value="250">...</form>

<!-- Specify lead type -->
<form data-lead-type="consultation">...</form>
```

---

## 🧪 Testing & Debugging

### Debug Mode
```javascript
// Enable debug logging
securepixel.debug(true);

// Check tracking status
console.log(securepixel.getStats());
```

### Verify Events
1. Open browser DevTools
2. Go to Network tab
3. Look for requests to `/collect` endpoint
4. Check Console tab for `[SecurePixel]` messages

### Common Issues
- **Script not loading**: Check client ID and domain authorization
- **Events not firing**: Verify element selectors and event handlers
- **DataLayer not working**: Ensure dataLayer is initialized before SecurePixel

---

## 📈 Analytics & Reporting

### Available Event Types
- `purchase` - Completed transactions
- `product_view` - Product page views
- `add_to_cart` - Cart additions
- `remove_from_cart` - Cart removals
- `begin_checkout` - Checkout initiation
- `lead_form_submit` - Lead form submissions
- `signup` - User registrations
- `subscription` - Subscription purchases
- `conversion` - Custom conversion goals

### Revenue Attribution
SecurePixel tracks:
- First-touch attribution (session start)
- Last-touch attribution (current visit)
- UTM parameter capture
- Referrer classification
- Campaign tracking

---

## 🚀 Advanced Features

### Custom Event Tracking
```javascript
// Track any custom event
securepixel.track('video_play', {
    video_title: 'Product Demo',
    video_duration: 120,
    completion_rate: 75
});
```

### Batch Processing
Events are automatically batched for performance:
- 5-second timeout or 20 events trigger batch send
- Activity-based batching (1 minute inactivity)
- Page exit batch sending

### Cross-Domain Tracking
SecurePixel maintains session consistency across:
- Subdomains (automatic)
- Multiple authorized domains
- Checkout flows on different domains

---

## 💡 Best Practices

### 1. Implement Core Events First
Priority order:
1. Purchase tracking (highest ROI)
2. Product view tracking
3. Add to cart tracking
4. Lead form tracking

### 2. Use DataLayer When Possible
- More maintainable than manual tracking
- Compatible with other analytics tools
- Automatic event processing

### 3. Test Thoroughly
- Test on staging environment first
- Verify all e-commerce flows
- Check mobile compatibility
- Validate privacy compliance

### 4. Monitor Performance
- Use `securepixel.getStats()` for diagnostics
- Monitor network requests
- Check for JavaScript errors

---

## 🔧 Troubleshooting

### Script Loading Issues
```javascript
// Check if SecurePixel loaded
if (typeof window.securepixel === 'undefined') {
    console.error('SecurePixel failed to load');
} else {
    console.log('SecurePixel loaded successfully');
}
```

### Event Validation Errors
Common validation issues:
- Missing required fields (order_id, sku, form_id)
- Invalid currency codes (must be 3-letter ISO)
- Excessive string lengths
- Invalid numeric values

### Support
For implementation support:
1. Check browser console for error messages
2. Verify domain authorization in SecurePixel Management
3. Test with debug mode enabled
4. Contact support with specific error details

---

**🎉 You're Ready to Track E-commerce Events with SecurePixel!**

This implementation provides comprehensive tracking for purchases, products, leads, and conversions while maintaining privacy compliance and high performance.
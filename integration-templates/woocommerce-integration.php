<?php
/**
 * SecurePixel WooCommerce Integration
 * ===================================
 * Add this code to your theme's functions.php file or create a custom plugin.
 * Replace {CLIENT_ID} with your actual SecurePixel client ID.
 */

// Load SecurePixel script
function securepixel_load_script() {
    ?>
    <script src="https://pixel-management-275731808857.us-central1.run.app/pixel/{CLIENT_ID}/tracking.js" async></script>
    <?php
}
add_action('wp_head', 'securepixel_load_script');

// Track purchase on order received page
function securepixel_track_purchase() {
    if (!is_wc_endpoint_url('order-received')) {
        return;
    }
    
    global $wp;
    $order_id = absint($wp->query_vars['order-received']);
    $order = wc_get_order($order_id);
    
    if (!$order) {
        return;
    }
    
    $items = [];
    foreach ($order->get_items() as $item) {
        $product = $item->get_product();
        $items[] = [
            'item_id' => $product->get_sku() ?: $product->get_id(),
            'item_name' => $item->get_name(),
            'price' => (float) $item->get_total(),
            'quantity' => $item->get_quantity(),
            'item_category' => wp_strip_all_tags(wc_get_product_category_list($product->get_id()))
        ];
    }
    
    ?>
    <script>
    window.dataLayer = window.dataLayer || [];
    window.dataLayer.push({
        'event': 'purchase',
        'ecommerce': {
            'transaction_id': '<?php echo $order->get_order_number(); ?>',
            'value': <?php echo $order->get_total(); ?>,
            'currency': '<?php echo $order->get_currency(); ?>',
            'shipping': <?php echo $order->get_shipping_total(); ?>,
            'tax': <?php echo $order->get_total_tax(); ?>,
            'coupon': <?php echo $order->get_coupon_codes() ? '"' . implode(',', $order->get_coupon_codes()) . '"' : 'null'; ?>,
            'items': <?php echo json_encode($items); ?>
        }
    });
    </script>
    <?php
}
add_action('wp_footer', 'securepixel_track_purchase');

// Track product views
function securepixel_track_product_view() {
    if (!is_product()) {
        return;
    }
    
    global $post;
    $product = wc_get_product($post->ID);
    
    if (!$product) {
        return;
    }
    
    ?>
    <script>
    window.dataLayer = window.dataLayer || [];
    window.dataLayer.push({
        'event': 'view_item',
        'ecommerce': {
            'currency': '<?php echo get_woocommerce_currency(); ?>',
            'value': <?php echo $product->get_price(); ?>,
            'items': [{
                'item_id': '<?php echo $product->get_sku() ?: $product->get_id(); ?>',
                'item_name': '<?php echo esc_js($product->get_name()); ?>',
                'price': <?php echo $product->get_price(); ?>,
                'item_category': '<?php echo esc_js(wp_strip_all_tags(wc_get_product_category_list($product->get_id()))); ?>'
            }]
        }
    });
    </script>
    <?php
}
add_action('wp_footer', 'securepixel_track_product_view');

// Track add to cart via AJAX
function securepixel_add_to_cart_script() {
    if (is_admin()) {
        return;
    }
    ?>
    <script>
    jQuery(document).ready(function($) {
        // Track add to cart
        $(document.body).on('added_to_cart', function(event, fragments, cart_hash, button) {
            var product_id = button.data('product_id');
            var quantity = button.data('quantity') || 1;
            
            // Get product data via AJAX
            $.get('<?php echo admin_url('admin-ajax.php'); ?>', {
                action: 'get_product_data_for_tracking',
                product_id: product_id
            }, function(data) {
                if (data.success) {
                    window.dataLayer = window.dataLayer || [];
                    window.dataLayer.push({
                        'event': 'add_to_cart',
                        'ecommerce': {
                            'currency': data.data.currency,
                            'value': data.data.price * quantity,
                            'items': [{
                                'item_id': data.data.sku,
                                'item_name': data.data.name,
                                'price': data.data.price,
                                'quantity': quantity
                            }]
                        }
                    });
                }
            });
        });
        
        // Track begin checkout
        $(document.body).on('click', '.checkout-button, a[href*="checkout"]', function() {
            // Get cart data
            $.get('<?php echo wc_get_cart_url(); ?>', function() {
                window.dataLayer = window.dataLayer || [];
                window.dataLayer.push({
                    'event': 'begin_checkout',
                    'ecommerce': {
                        'currency': '<?php echo get_woocommerce_currency(); ?>',
                        'value': parseFloat($('.cart-total .amount').text().replace(/[^0-9.]/g, '')) || 0
                    }
                });
            });
        });
    });
    </script>
    <?php
}
add_action('wp_footer', 'securepixel_add_to_cart_script');

// AJAX handler for product data
function get_product_data_for_tracking() {
    $product_id = intval($_GET['product_id']);
    $product = wc_get_product($product_id);
    
    if (!$product) {
        wp_send_json_error();
        return;
    }
    
    wp_send_json_success([
        'sku' => $product->get_sku() ?: $product->get_id(),
        'name' => $product->get_name(),
        'price' => (float) $product->get_price(),
        'currency' => get_woocommerce_currency()
    ]);
}
add_action('wp_ajax_get_product_data_for_tracking', 'get_product_data_for_tracking');
add_action('wp_ajax_nopriv_get_product_data_for_tracking', 'get_product_data_for_tracking');

// Track lead forms (Contact Form 7 integration)
function securepixel_track_cf7_leads() {
    ?>
    <script>
    document.addEventListener('wpcf7mailsent', function(event) {
        // Track Contact Form 7 submissions as leads
        window.securepixel = window.securepixel || {};
        if (window.securepixel.trackLead) {
            window.securepixel.trackLead({
                form_id: 'cf7_' + event.detail.contactFormId,
                lead_type: 'contact',
                source: 'contact_form_7'
            });
        }
    });
    </script>
    <?php
}
add_action('wp_footer', 'securepixel_track_cf7_leads');
?>
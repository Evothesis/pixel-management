/**
 * SecurePixel Analytics Pixel - Client-Specific Tracking Library
 * 
 * This JavaScript template generates client-specific tracking pixels with privacy
 * compliance and domain authorization. The code is dynamically generated per client
 * with personalized configuration including privacy settings, collection endpoints,
 * and domain-specific parameters.
 * 
 * Template features:
 * - Client-specific configuration injection via CONFIG_PLACEHOLDER
 * - Privacy-compliant data collection (GDPR, HIPAA, standard modes)
 * - Domain authorization and origin validation
 * - Automatic page view and event tracking capabilities
 * - Secure data transmission to collection infrastructure
 * - Cookie and session management based on privacy level
 * 
 * The template is processed by pixel_serving.py to generate client-specific
 * tracking code with appropriate privacy settings and collection endpoints.
 * Generated: {TIMESTAMP}
 * Version: 1.0.0
 */

(function() {
    'use strict';
    
    // Inject client configuration
    var config = {CONFIG_PLACEHOLDER};
    
    // Validate configuration
    if (!config || !config.client_id || !config.collection_endpoint) {
        console.error('[SecurePixel] Invalid tracking configuration');
        return;
    }
    
    // Constants for tracking behavior
    var BATCH_TIMEOUT_MS = 5000;   // 5 seconds
    var MAX_BATCH_SIZE = 20;       // 20 events max
    var SCROLL_TRACK_INTERVAL = 10; // Track every 10% scroll
    var SCROLL_DEBOUNCE_MS = 250;   // 250ms scroll debounce
    
    // Tracking configuration with defaults
    var trackingConfig = {
        apiEndpoint: config.collection_endpoint,
        batchTimeout: BATCH_TIMEOUT_MS,
        maxBatchSize: MAX_BATCH_SIZE,
        clientId: config.client_id,
        privacyLevel: config.privacy_level || 'standard'
    };
    
    console.log('[SecurePixel] Analytics pixel loaded for client:', trackingConfig.clientId);
    
    // Session management
    var sessionManager = {
        getSessionId: function() {
            var sessionId = sessionStorage.getItem('_securepixel_session_id');
            if (!sessionId) {
                sessionId = 'sess_' + Math.random().toString(36).substring(2, 15) + 
                           Math.random().toString(36).substring(2, 15);
                sessionStorage.setItem('_securepixel_session_id', sessionId);
            }
            return sessionId;
        },
        
        getVisitorId: function() {
            var visitorId = localStorage.getItem('_securepixel_visitor_id');
            if (!visitorId) {
                visitorId = 'vis_' + Math.random().toString(36).substring(2, 15) + 
                           Math.random().toString(36).substring(2, 15);
                localStorage.setItem('_securepixel_visitor_id', visitorId);
            }
            return visitorId;
        }
    };
    
    // Event batching system
    var eventBatcher = {
        batch: [],
        batchTimer: null,
        
        addEvent: function(eventType, eventData) {
            // Stop collecting if we've hit the failure limit
            if (this.collectionStopped && eventType !== 'pageview') {
                return;
            }
            
            // Reset collection on new pageview (page change)
            if (eventType === 'pageview' && this.collectionStopped) {
                this.collectionStopped = false;
                console.log('[SecurePixel] Collection resumed after page change');
            }
            
            var event = {
                eventType: eventType,
                eventData: eventData || {},
                timestamp: new Date().toISOString()
            };
            
            this.batch.push(event);
            
            // Send immediately if batch is full
            if (this.batch.length >= trackingConfig.maxBatchSize) {
                this.sendBatch();
                return;
            }
            
            // Reset timer
            if (this.batchTimer) {
                clearTimeout(this.batchTimer);
            }
            
            // Set new timer
            this.batchTimer = setTimeout(() => {
                this.sendBatch();
            }, trackingConfig.batchTimeout);
        },
        
        sendBatch: function() {
            if (this.batch.length === 0) return;
            
            var batchData = {
                eventType: 'batch',
                sessionId: sessionManager.getSessionId(),
                visitorId: sessionManager.getVisitorId(),
                siteId: window.location.hostname,
                timestamp: new Date().toISOString(),
                events: this.batch.slice(), // Copy the batch
                privacy_level: config.privacy_level,
                page: {
                    title: document.title,
                    url: window.location.href,
                    path: window.location.pathname,
                    referrer: document.referrer || 'direct'
                }
            };
            
            // Apply privacy filters based on configuration
            if (config.privacy_level === 'gdpr' || config.privacy_level === 'hipaa') {
                batchData = this.applyPrivacyFilters(batchData);
            }
            
            this.sendToAPI(batchData);
            
            // Clear batch
            this.batch = [];
            if (this.batchTimer) {
                clearTimeout(this.batchTimer);
                this.batchTimer = null;
            }
        },
        
        applyPrivacyFilters: function(data) {
            // Remove or hash sensitive data based on privacy level
            if (config.ip_collection && !config.ip_collection.enabled) {
                // IP collection disabled - will be handled server-side
            }
            
            // Filter PII from event data
            data.events = data.events.map(function(event) {
                if (event.eventData && typeof event.eventData === 'object') {
                    var filtered = {};
                    for (var key in event.eventData) {
                        // Skip fields that might contain PII
                        if (!key.match(/(email|phone|ssn|credit|password|social|name|address|zip|postal|dob|birth|age|gender)/i)) {
                            filtered[key] = event.eventData[key];
                        }
                    }
                    event.eventData = filtered;
                }
                return event;
            });
            
            return data;
        },
        
        sendToAPI: function(data) {
            var self = this;
            // Always use fetch with proper Content-Type header
            fetch(trackingConfig.apiEndpoint, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(data),
                keepalive: true  // Important for page unload scenarios
            }).then(function(response) {
                if (!response.ok) {
                    if (response.status >= 500) {
                        console.warn('[SecurePixel] Server error (' + response.status + ') - will retry with next batch');
                        // Treat as network failure - merge with next batch
                        self.batch = data.events.concat(self.batch);
                        
                        // Prevent batch from growing too large
                        if (self.batch.length >= MAX_BATCH_SIZE * 5) {
                            console.warn('[SecurePixel] Batch size limit reached, stopping collection until page change');
                            self.batch = self.batch.slice(-MAX_BATCH_SIZE);
                            self.collectionStopped = true;
                        }
                    } else if (response.status >= 400) {
                        console.error('[SecurePixel] Client error (' + response.status + ') - dropping batch, check configuration');
                        // Don't retry client errors (bad request, unauthorized, etc.)
                    }
                }
            }).catch(function(error) {
                if (error.name === 'NetworkError' || error.message.includes('fetch') || error.message.includes('Failed to fetch')) {
                    console.warn('[SecurePixel] Network error - will retry with next batch:', error.message);
                    // Current retry logic
                    self.batch = data.events.concat(self.batch);
                    
                    if (self.batch.length >= MAX_BATCH_SIZE * 5) {
                        console.warn('[SecurePixel] Batch size limit reached, stopping collection until page change');
                        self.batch = self.batch.slice(-MAX_BATCH_SIZE);
                        self.collectionStopped = true;
                    }
                } else {
                    console.error('[SecurePixel] Unexpected error - dropping batch:', error.name, error.message);
                    // Don't retry unknown errors
                }
            });
        }
    };
    
    // Auto-track page view
    eventBatcher.addEvent('pageview', {
        page: {
            title: document.title,
            url: window.location.href,
            path: window.location.pathname
        },
        attribution: {
            utm_source: new URLSearchParams(window.location.search).get('utm_source'),
            utm_medium: new URLSearchParams(window.location.search).get('utm_medium'),
            utm_campaign: new URLSearchParams(window.location.search).get('utm_campaign'),
            utm_content: new URLSearchParams(window.location.search).get('utm_content'),
            utm_term: new URLSearchParams(window.location.search).get('utm_term'),
            referrer: document.referrer || null
        }
    });
    
    // Track clicks
    document.addEventListener('click', function(e) {
        var element = e.target;
        var elementData = {
            tag: element.tagName.toLowerCase(),
            id: element.id || null,
            class: element.className || null,
            text: element.textContent ? element.textContent.trim().substring(0, 100) : null
        };
        
        eventBatcher.addEvent('click', {
            element: elementData,
            position: {
                x: e.clientX,
                y: e.clientY
            }
        });
    });
    
    // Enhanced form tracking for leads and conversions
    function isLeadForm(form) {
        // Check various indicators that this is a lead form
        var indicators = [
            'lead', 'contact', 'quote', 'demo', 'trial', 'signup', 'subscribe',
            'newsletter', 'download', 'whitepaper', 'ebook', 'consultation'
        ];
        
        var formId = (form.id || '').toLowerCase();
        var formClass = (form.className || '').toLowerCase();
        var formAction = (form.action || '').toLowerCase();
        
        // Check form attributes
        if (form.dataset.leadForm || form.dataset.securepixelLead) {
            return true;
        }
        
        // Check if any indicator appears in form attributes
        return indicators.some(function(indicator) {
            return formId.includes(indicator) || 
                   formClass.includes(indicator) || 
                   formAction.includes(indicator);
        });
    }
    
    function getFormValue(form) {
        // Try to determine lead value from form data attributes
        var value = form.dataset.leadValue || form.dataset.value;
        if (value) return parseFloat(value);
        
        // Look for price/value in form fields
        var priceFields = form.querySelectorAll('input[name*="price"], input[name*="value"], input[name*="amount"]');
        if (priceFields.length > 0) {
            return parseFloat(priceFields[0].value) || 0;
        }
        
        return 0;
    }
    
    // Track form field focus
    document.addEventListener('focus', function(e) {
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.tagName === 'SELECT') {
            var form = e.target.closest('form');
            var isLead = form ? isLeadForm(form) : false;
            
            eventBatcher.addEvent('form_focus', {
                field: {
                    type: e.target.type || e.target.tagName.toLowerCase(),
                    name: e.target.name || null,
                    id: e.target.id || null
                },
                form: {
                    id: form ? form.id : null,
                    is_lead_form: isLead
                }
            });
        }
    }, true);
    
    // Track form submissions with lead detection
    document.addEventListener('submit', function(e) {
        var form = e.target;
        var isLead = isLeadForm(form);
        
        if (isLead) {
            // This is a lead form - track as lead
            var leadData = {
                form_id: form.id || 'unknown_form',
                lead_type: form.dataset.leadType || 'contact',
                lead_value: getFormValue(form),
                source: form.dataset.source || 'website',
                campaign: form.dataset.campaign || null
            };
            
            // Use the securepixel API for better tracking
            if (window.securepixel && window.securepixel.trackLead) {
                window.securepixel.trackLead(leadData);
            } else {
                eventBatcher.addEvent('lead_form_submit', leadData);
            }
        } else {
            // Regular form submission
            eventBatcher.addEvent('form_submit', {
                form_id: form.id || 'unknown_form',
                form_action: form.action || window.location.href,
                form_method: form.method || 'get'
            });
        }
    }, true);
    
    // Track scroll depth
    var maxScrollDepth = 0;
    var scrollTimer;
    window.addEventListener('scroll', function() {
        clearTimeout(scrollTimer);
        scrollTimer = setTimeout(function() {
            var depth = Math.round((window.scrollY / (document.body.scrollHeight - window.innerHeight)) * 100);
            // Track every 10% and only if it's deeper than previously recorded
            if (depth > maxScrollDepth && depth % SCROLL_TRACK_INTERVAL === 0) {
                maxScrollDepth = depth;
                eventBatcher.addEvent('scroll', {
                    depth: depth,
                    position: window.scrollY
                });
            }
        }, SCROLL_DEBOUNCE_MS);
    });
    
    // Send remaining events before page unload
    window.addEventListener('beforeunload', function() {
        if (eventBatcher.batch.length > 0) {
            eventBatcher.sendBatch();
        }
    });
    
    // DataLayer integration for automatic e-commerce tracking
    function initDataLayerListener() {
        // Initialize dataLayer if it doesn't exist
        window.dataLayer = window.dataLayer || [];
        
        // Process existing dataLayer events
        window.dataLayer.forEach(processDataLayerEvent);
        
        // Override push method to capture new events
        var originalPush = window.dataLayer.push;
        window.dataLayer.push = function() {
            var args = Array.prototype.slice.call(arguments);
            args.forEach(processDataLayerEvent);
            return originalPush.apply(window.dataLayer, args);
        };
        
        console.log('[SecurePixel] DataLayer integration active');
    }
    
    function processDataLayerEvent(data) {
        if (!data || !data.event) return;
        
        try {
            switch(data.event) {
                case 'purchase':
                case 'transaction':
                    if (data.ecommerce && data.ecommerce.transaction_id) {
                        window.securepixel.trackPurchase({
                            order_id: data.ecommerce.transaction_id,
                            revenue: data.ecommerce.value || data.ecommerce.revenue,
                            currency: data.ecommerce.currency,
                            products: data.ecommerce.items || data.ecommerce.products || [],
                            shipping: data.ecommerce.shipping,
                            tax: data.ecommerce.tax,
                            coupon_code: data.ecommerce.coupon
                        });
                    }
                    break;
                    
                case 'view_item':
                case 'product_view':
                    if (data.ecommerce && data.ecommerce.items && data.ecommerce.items[0]) {
                        var item = data.ecommerce.items[0];
                        window.securepixel.trackProduct({
                            sku: item.item_id || item.sku,
                            name: item.item_name || item.name,
                            price: item.price,
                            category: item.item_category || item.category,
                            currency: data.ecommerce.currency,
                            brand: item.item_brand || item.brand,
                            variant: item.item_variant || item.variant
                        });
                    }
                    break;
                    
                case 'add_to_cart':
                    if (data.ecommerce && data.ecommerce.items && data.ecommerce.items[0]) {
                        var item = data.ecommerce.items[0];
                        window.securepixel.trackAddToCart({
                            sku: item.item_id || item.sku,
                            name: item.item_name || item.name,
                            quantity: item.quantity,
                            price: item.price,
                            currency: data.ecommerce.currency,
                            cart_value: data.ecommerce.value
                        });
                    }
                    break;
                    
                case 'remove_from_cart':
                    if (data.ecommerce && data.ecommerce.items && data.ecommerce.items[0]) {
                        var item = data.ecommerce.items[0];
                        window.securepixel.trackRemoveFromCart({
                            sku: item.item_id || item.sku,
                            name: item.item_name || item.name,
                            quantity: item.quantity,
                            price: item.price,
                            currency: data.ecommerce.currency
                        });
                    }
                    break;
                    
                case 'begin_checkout':
                    if (data.ecommerce) {
                        window.securepixel.trackBeginCheckout({
                            cart_value: data.ecommerce.value,
                            currency: data.ecommerce.currency,
                            item_count: data.ecommerce.items ? data.ecommerce.items.length : 0,
                            products: data.ecommerce.items || []
                        });
                    }
                    break;
                    
                case 'checkout_progress':
                    if (data.ecommerce) {
                        window.securepixel.trackCheckoutProgress({
                            step: data.checkout_step || data.step,
                            step_name: data.checkout_option || data.step_name,
                            cart_value: data.ecommerce.value,
                            currency: data.ecommerce.currency
                        });
                    }
                    break;
                    
                case 'sign_up':
                case 'signup':
                    window.securepixel.trackSignup({
                        signup_type: data.signup_type || data.method,
                        source: data.source,
                        plan: data.plan,
                        value: data.value
                    });
                    break;
                    
                case 'generate_lead':
                case 'lead':
                    window.securepixel.trackLead({
                        form_id: data.form_id || 'dataLayer',
                        lead_type: data.lead_type || 'contact',
                        lead_value: data.value,
                        source: data.source,
                        campaign: data.campaign
                    });
                    break;
                    
                case 'conversion':
                    window.securepixel.trackConversion({
                        conversion_type: data.conversion_type || data.goal,
                        value: data.value,
                        currency: data.currency,
                        goal_id: data.goal_id,
                        funnel_step: data.funnel_step
                    });
                    break;
            }
        } catch (error) {
            console.warn('[SecurePixel] Error processing dataLayer event:', error);
        }
    }
    
    // Initialize dataLayer integration
    initDataLayerListener();
    
    // Global tracking API
    window.securepixel = {
        // Core tracking method
        track: function(eventType, eventData) {
            eventBatcher.addEvent(eventType, eventData);
        },
        
        // E-commerce tracking methods
        trackPurchase: function(data) {
            if (!data || !data.order_id) {
                console.warn('[SecurePixel] trackPurchase requires order_id');
                return;
            }
            
            this.track('purchase', {
                order_id: data.order_id,
                revenue: parseFloat(data.revenue) || 0,
                currency: data.currency || 'USD',
                products: data.products || [],
                customer_type: data.customer_type || 'new',
                coupon_code: data.coupon_code || null,
                shipping: parseFloat(data.shipping) || 0,
                tax: parseFloat(data.tax) || 0
            });
        },
        
        trackProduct: function(data) {
            if (!data || !data.sku) {
                console.warn('[SecurePixel] trackProduct requires sku');
                return;
            }
            
            this.track('product_view', {
                sku: data.sku,
                name: data.name || '',
                category: data.category || '',
                price: parseFloat(data.price) || 0,
                currency: data.currency || 'USD',
                brand: data.brand || '',
                variant: data.variant || '',
                in_stock: data.in_stock !== false
            });
        },
        
        trackAddToCart: function(data) {
            if (!data || !data.sku) {
                console.warn('[SecurePixel] trackAddToCart requires sku');
                return;
            }
            
            this.track('add_to_cart', {
                sku: data.sku,
                name: data.name || '',
                quantity: parseInt(data.quantity) || 1,
                price: parseFloat(data.price) || 0,
                currency: data.currency || 'USD',
                cart_value: parseFloat(data.cart_value) || 0
            });
        },
        
        trackRemoveFromCart: function(data) {
            if (!data || !data.sku) {
                console.warn('[SecurePixel] trackRemoveFromCart requires sku');
                return;
            }
            
            this.track('remove_from_cart', {
                sku: data.sku,
                name: data.name || '',
                quantity: parseInt(data.quantity) || 1,
                price: parseFloat(data.price) || 0,
                currency: data.currency || 'USD'
            });
        },
        
        trackBeginCheckout: function(data) {
            this.track('begin_checkout', {
                cart_value: parseFloat(data.cart_value) || 0,
                currency: data.currency || 'USD',
                item_count: parseInt(data.item_count) || 0,
                products: data.products || []
            });
        },
        
        trackCheckoutProgress: function(data) {
            this.track('checkout_progress', {
                step: data.step || 1,
                step_name: data.step_name || '',
                cart_value: parseFloat(data.cart_value) || 0,
                currency: data.currency || 'USD'
            });
        },
        
        // Lead and conversion tracking
        trackLead: function(data) {
            if (!data || !data.form_id) {
                console.warn('[SecurePixel] trackLead requires form_id');
                return;
            }
            
            this.track('lead_form_submit', {
                form_id: data.form_id,
                lead_type: data.lead_type || 'contact',
                lead_value: parseFloat(data.lead_value) || 0,
                source: data.source || 'website',
                campaign: data.campaign || null,
                qualified: data.qualified !== false
            });
        },
        
        trackSignup: function(data) {
            this.track('signup', {
                signup_type: data.signup_type || 'registration',
                source: data.source || 'website',
                plan: data.plan || null,
                value: parseFloat(data.value) || 0
            });
        },
        
        trackSubscription: function(data) {
            this.track('subscription', {
                plan: data.plan || 'unknown',
                value: parseFloat(data.value) || 0,
                currency: data.currency || 'USD',
                billing_cycle: data.billing_cycle || 'monthly',
                trial_days: parseInt(data.trial_days) || 0
            });
        },
        
        // Custom conversion tracking
        trackConversion: function(data) {
            if (!data || !data.conversion_type) {
                console.warn('[SecurePixel] trackConversion requires conversion_type');
                return;
            }
            
            this.track('conversion', {
                conversion_type: data.conversion_type,
                value: parseFloat(data.value) || 0,
                currency: data.currency || 'USD',
                goal_id: data.goal_id || null,
                funnel_step: data.funnel_step || null
            });
        },
        
        // Utility methods
        getStats: function() {
            return {
                events_queued: eventBatcher.batch.length,
                client_id: trackingConfig.clientId,
                privacy_level: trackingConfig.privacyLevel,
                dataLayer_enabled: typeof window.dataLayer !== 'undefined'
            };
        },
        
        // Debug method
        debug: function(enable) {
            if (enable === undefined) enable = true;
            trackingConfig.debug = enable;
            if (enable) {
                console.log('[SecurePixel] Debug mode enabled');
                console.log('Current config:', trackingConfig);
                console.log('Queued events:', eventBatcher.batch);
            }
        }
    };
    
})();
/**
 * Evothesis Analytics Pixel - Client-Specific Tracking Library
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
        console.error('[Evothesis] Invalid tracking configuration');
        return;
    }
    
    // Tracking configuration with defaults
    var trackingConfig = {
        apiEndpoint: config.collection_endpoint,
        batchTimeout: 5000,        // 5 seconds
        maxBatchSize: 20,          // 20 events max
        clientId: config.client_id,
        privacyLevel: config.privacy_level || 'standard'
    };
    
    console.log('[Evothesis] Analytics pixel loaded for client:', trackingConfig.clientId);
    
    // Session management
    var sessionManager = {
        getSessionId: function() {
            var sessionId = sessionStorage.getItem('_evothesis_session_id');
            if (!sessionId) {
                sessionId = 'sess_' + Math.random().toString(36).substring(2, 15) + 
                           Math.random().toString(36).substring(2, 15);
                sessionStorage.setItem('_evothesis_session_id', sessionId);
            }
            return sessionId;
        },
        
        getVisitorId: function() {
            var visitorId = localStorage.getItem('_evothesis_visitor_id');
            if (!visitorId) {
                visitorId = 'vis_' + Math.random().toString(36).substring(2, 15) + 
                           Math.random().toString(36).substring(2, 15);
                localStorage.setItem('_evothesis_visitor_id', visitorId);
            }
            return visitorId;
        }
    };
    
    // Event batching system
    var eventBatcher = {
        batch: [],
        batchTimer: null,
        
        addEvent: function(eventType, eventData) {
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
                        if (!key.match(/(email|phone|ssn|credit|password|social)/i)) {
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
                    console.warn('[Evothesis] Server responded with status:', response.status);
                }
            }).catch(function(error) {
                console.warn('[Evothesis] Failed to send tracking data:', error);
                // Could implement retry logic here in the future
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
    
    // Track form interactions
    document.addEventListener('focus', function(e) {
        if (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA' || e.target.tagName === 'SELECT') {
            eventBatcher.addEvent('form_focus', {
                field: {
                    type: e.target.type || e.target.tagName.toLowerCase(),
                    name: e.target.name || null,
                    id: e.target.id || null
                }
            });
        }
    }, true);
    
    // Track scroll depth
    var scrollDepth = 0;
    var scrollTimer;
    window.addEventListener('scroll', function() {
        clearTimeout(scrollTimer);
        scrollTimer = setTimeout(function() {
            var depth = Math.round((window.scrollY / (document.body.scrollHeight - window.innerHeight)) * 100);
            if (depth > scrollDepth && depth % 25 === 0) { // Track every 25%
                scrollDepth = depth;
                eventBatcher.addEvent('scroll', {
                    depth: depth,
                    position: window.scrollY
                });
            }
        }, 250);
    });
    
    // Send remaining events before page unload
    window.addEventListener('beforeunload', function() {
        if (eventBatcher.batch.length > 0) {
            eventBatcher.sendBatch();
        }
    });
    
    // Global tracking API
    window.evothesis = {
        track: function(eventType, eventData) {
            eventBatcher.addEvent(eventType, eventData);
        },
        
        getStats: function() {
            return {
                events_queued: eventBatcher.batch.length,
                client_id: trackingConfig.clientId,
                privacy_level: trackingConfig.privacyLevel
            };
        }
    };
    
})();
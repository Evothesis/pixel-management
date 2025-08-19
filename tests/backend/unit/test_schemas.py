"""
Test suite for Pydantic schema validation and type safety.

This module validates all API request/response schemas including input validation
rules, type safety enforcement, nested object validation, and format validation.
Tests ensure robust data validation that prevents malformed data from entering
the system and maintains API contract integrity.

Test categories:
- Input validation rules and comprehensive error messages
- Type safety enforcement for all API endpoints
- Nested object validation in complex client features
- Email and domain format validation with edge cases

All tests validate both successful validation scenarios and failure cases
with appropriate error handling and user-friendly error messages.
"""

import pytest
from pydantic import ValidationError
from datetime import datetime
from typing import Dict, Any

from app.schemas import (
    ClientCreate, ClientUpdate, ClientResponse,
    DomainCreate, DomainResponse,
    ClientConfigResponse, HealthResponse
)


class TestSchemaValidation:
    """Test suite for comprehensive schema validation."""

    def test_input_validation_rules(self):
        """
        Test input validation rules and error messages.
        
        Validates:
        - Required field validation with clear error messages
        - Field length and format constraints
        - Business logic validation rules
        - Custom validator behavior
        - Error message clarity and actionability
        """
        # Test ClientCreate validation
        
        # Valid client creation
        valid_client_data = {
            'name': 'Test Company',
            'email': 'test@company.com',
            'owner': 'owner@company.com',
            'billing_entity': 'billing@company.com',
            'client_type': 'end_client',
            'deployment_type': 'shared',
            'privacy_level': 'standard',
            'features': {'analytics': True}
        }
        
        client = ClientCreate(**valid_client_data)
        assert client.name == 'Test Company'
        assert client.privacy_level == 'standard'
        assert client.deployment_type == 'shared'
        assert client.client_type == 'end_client'
        
        # Test required field validation
        with pytest.raises(ValidationError) as exc_info:
            ClientCreate()  # Missing required fields
        
        error_dict = exc_info.value.errors()
        required_errors = [e for e in error_dict if e['type'] == 'missing']
        assert len(required_errors) >= 2  # At least name and owner are required
        
        # Verify error messages are informative
        field_names = [e['loc'][0] for e in required_errors]
        assert 'name' in field_names
        assert 'owner' in field_names
        
        # Test privacy level validation
        with pytest.raises(ValidationError) as exc_info:
            ClientCreate(
                name='Test Company',
                owner='owner@test.com',
                privacy_level='invalid_level'
            )
        
        privacy_error = next(e for e in exc_info.value.errors() if 'privacy_level' in str(e['loc']))
        assert 'Privacy level must be standard, gdpr, or hipaa' in privacy_error['msg']
        
        # Test deployment type validation
        with pytest.raises(ValidationError) as exc_info:
            ClientCreate(
                name='Test Company',
                owner='owner@test.com',
                deployment_type='invalid_deployment'
            )
        
        deployment_error = next(e for e in exc_info.value.errors() if 'deployment_type' in str(e['loc']))
        assert 'Deployment type must be shared or dedicated' in deployment_error['msg']
        
        # Test client type validation
        with pytest.raises(ValidationError) as exc_info:
            ClientCreate(
                name='Test Company',
                owner='owner@test.com',
                client_type='invalid_type'
            )
        
        client_type_error = next(e for e in exc_info.value.errors() if 'client_type' in str(e['loc']))
        assert 'Client type must be end_client, agency, enterprise, or admin' in client_type_error['msg']
        
        # Test DomainCreate validation
        valid_domain = DomainCreate(domain='example.com', is_primary=True)
        assert valid_domain.domain == 'example.com'
        assert valid_domain.is_primary is True
        
        # Test domain length validation
        with pytest.raises(ValidationError) as exc_info:
            DomainCreate(domain='ab')  # Too short
        
        domain_error = next(e for e in exc_info.value.errors() if 'domain' in str(e['loc']))
        assert 'Domain must be at least 3 characters' in domain_error['msg']
        
        # Test domain normalization (lowercase, strip)
        normalized_domain = DomainCreate(domain='  EXAMPLE.COM  ')
        assert normalized_domain.domain == 'example.com'

    def test_type_safety_enforcement(self):
        """
        Test type safety enforcement for all endpoints.
        
        Validates:
        - Strict type checking for all fields
        - Automatic type coercion where appropriate
        - Type mismatch error handling
        - Complex type validation (Dict, List, Optional)
        - DateTime and custom type handling
        """
        # Test string type enforcement
        with pytest.raises(ValidationError):
            ClientCreate(
                name=12345,  # Should be string
                owner='owner@test.com'
            )
        
        # Test boolean type enforcement
        with pytest.raises(ValidationError):
            ClientCreate(
                name='Test Company',
                owner='owner@test.com',
                features={'analytics': 'true'}  # Should be boolean, not string
            )
        
        # Test email type validation
        with pytest.raises(ValidationError):
            ClientCreate(
                name='Test Company',
                email='not-an-email',  # Invalid email format
                owner='owner@test.com'
            )
        
        # Test valid email formats
        valid_emails = [
            'user@domain.com',
            'user.name@domain.co.uk',
            'user+tag@domain.org',
            'user123@domain-name.com'
        ]
        
        for email in valid_emails:
            client = ClientCreate(
                name='Test Company',
                email=email,
                owner='owner@test.com'
            )
            assert client.email == email
        
        # Test Dict type validation for features
        valid_features = {
            'analytics': True,
            'conversion_tracking': False,
            'custom_events': True,
            'advanced_reporting': {'enabled': True, 'retention_days': 30}
        }
        
        client = ClientCreate(
            name='Test Company',
            owner='owner@test.com',
            features=valid_features
        )
        assert client.features == valid_features
        
        # Test optional field type safety
        # None should be allowed for optional fields
        client_with_none = ClientCreate(
            name='Test Company',
            owner='owner@test.com',
            email=None,  # Optional field
            billing_entity=None,  # Optional field
            vm_hostname=None  # Optional field
        )
        assert client_with_none.email is None
        assert client_with_none.billing_entity is None
        
        # Test ClientUpdate partial validation
        update_data = ClientUpdate(
            name='Updated Name',
            privacy_level='gdpr'
            # Other fields should remain None/unset
        )
        assert update_data.name == 'Updated Name'
        assert update_data.privacy_level == 'gdpr'
        assert update_data.email is None
        
        # Test response schema type safety
        response_data = {
            'client_id': 'client_123',
            'name': 'Test Company',
            'owner': 'owner@test.com',
            'billing_entity': 'billing@test.com',
            'privacy_level': 'standard',
            'ip_collection_enabled': True,
            'consent_required': False,
            'features': {'analytics': True},
            'deployment_type': 'shared',
            'billing_rate_per_1k': 0.01,
            'created_at': datetime.utcnow(),
            'is_active': True,
            'client_type': 'end_client'
        }
        
        response = ClientResponse(**response_data)
        assert isinstance(response.created_at, datetime)
        assert isinstance(response.billing_rate_per_1k, float)
        assert isinstance(response.features, dict)

    def test_nested_object_validation(self):
        """
        Test nested object validation in client features.
        
        Validates:
        - Deep nested object structure validation
        - Complex feature configuration validation
        - Recursive validation of nested schemas
        - Error propagation from nested objects
        - Mixed type validation in nested structures
        """
        # Test simple nested features
        simple_features = {
            'analytics': True,
            'conversion_tracking': False,
            'custom_events': True
        }
        
        client = ClientCreate(
            name='Test Company',
            owner='owner@test.com',
            features=simple_features
        )
        assert client.features == simple_features
        
        # Test complex nested features with configuration objects
        complex_features = {
            'analytics': {
                'enabled': True,
                'tracking_level': 'detailed',
                'retention_days': 365,
                'custom_dimensions': ['category', 'user_type', 'campaign']
            },
            'conversion_tracking': {
                'enabled': True,
                'attribution_window': 30,
                'cross_domain': True,
                'goals': [
                    {'name': 'purchase', 'value_threshold': 50.0},
                    {'name': 'signup', 'value_threshold': 0.0},
                    {'name': 'download', 'value_threshold': 10.0}
                ]
            },
            'privacy': {
                'ip_anonymization': True,
                'cookie_consent': {
                    'required': True,
                    'banner_text': 'We use cookies to improve your experience',
                    'categories': ['necessary', 'analytics', 'marketing']
                },
                'data_retention': {
                    'user_data_days': 1095,
                    'event_data_days': 730,
                    'log_data_days': 90
                }
            },
            'integrations': {
                'google_analytics': {
                    'enabled': True,
                    'measurement_id': 'G-XXXXXXXXXX',
                    'enhanced_ecommerce': True
                },
                'facebook_pixel': {
                    'enabled': False,
                    'pixel_id': None
                },
                'custom_webhooks': [
                    {
                        'name': 'order_webhook',
                        'url': 'https://api.example.com/orders',
                        'events': ['purchase', 'add_to_cart'],
                        'headers': {'Authorization': 'Bearer token123'}
                    }
                ]
            }
        }
        
        # This should validate successfully with complex nested structure
        client_complex = ClientCreate(
            name='Enterprise Company',
            owner='admin@enterprise.com',
            client_type='enterprise',
            privacy_level='gdpr',
            features=complex_features
        )
        
        assert client_complex.features['analytics']['enabled'] is True
        assert client_complex.features['conversion_tracking']['attribution_window'] == 30
        assert len(client_complex.features['conversion_tracking']['goals']) == 3
        assert client_complex.features['privacy']['cookie_consent']['required'] is True
        assert len(client_complex.features['integrations']['custom_webhooks']) == 1
        
        # Test nested validation with invalid types
        invalid_nested_features = {
            'analytics': {
                'enabled': 'yes',  # Should be boolean
                'retention_days': '365'  # Should be integer
            }
        }
        
        # Should still validate as features is Dict[str, Any]
        client_with_invalid = ClientCreate(
            name='Test Company',
            owner='owner@test.com',
            features=invalid_nested_features
        )
        assert client_with_invalid.features == invalid_nested_features
        
        # Test deeply nested configuration validation
        deep_nested_features = {
            'level1': {
                'level2': {
                    'level3': {
                        'level4': {
                            'deep_setting': True,
                            'deep_value': 42,
                            'deep_list': [1, 2, 3, {'nested_in_list': 'value'}]
                        }
                    }
                }
            }
        }
        
        client_deep = ClientCreate(
            name='Deep Config Company',
            owner='deep@test.com',
            features=deep_nested_features
        )
        
        deep_value = client_deep.features['level1']['level2']['level3']['level4']['deep_value']
        assert deep_value == 42
        
        # Test ClientConfigResponse nested validation
        config_response_data = {
            'client_id': 'client_123',
            'privacy_level': 'gdpr',
            'ip_collection': {
                'enabled': True,
                'hash_required': True,
                'salt': 'random_salt_value',
                'anonymization_level': 'full'
            },
            'consent': {
                'required': True,
                'default_behavior': 'deny',
                'banner_config': {
                    'position': 'bottom',
                    'theme': 'dark',
                    'language': 'en'
                }
            },
            'features': complex_features,  # Reuse complex features
            'deployment': {
                'type': 'dedicated',
                'hostname': 'client123.pixels.com',
                'region': 'us-east-1',
                'resources': {
                    'cpu_cores': 4,
                    'memory_gb': 16,
                    'storage_gb': 100
                }
            }
        }
        
        config_response = ClientConfigResponse(**config_response_data)
        assert config_response.ip_collection['hash_required'] is True
        assert config_response.consent['banner_config']['theme'] == 'dark'
        assert config_response.deployment['resources']['cpu_cores'] == 4

    def test_email_domain_format_validation(self):
        """
        Test email and domain format validation.
        
        Validates:
        - RFC-compliant email format validation
        - Domain name format validation and normalization
        - International domain name support
        - Edge cases and malformed input handling
        - Security considerations for email/domain inputs
        """
        # Test valid email formats
        valid_emails = [
            'user@domain.com',
            'user.name@domain.com',
            'user+tag@domain.com',
            'user123@domain123.com',
            'user_name@domain-name.com',
            'user@subdomain.domain.com',
            'a@b.co',  # Minimal valid email
            'very.long.email.address@very.long.domain.name.com',
            'user@domain.co.uk',
            'user@domain.travel'
        ]
        
        for email in valid_emails:
            client = ClientCreate(
                name='Test Company',
                email=email,
                owner='owner@test.com'
            )
            assert client.email == email
        
        # Test invalid email formats
        invalid_emails = [
            'not-an-email',
            '@domain.com',
            'user@',
            'user..name@domain.com',
            'user@domain',
            'user @domain.com',  # Space not allowed
            'user@domain .com',  # Space not allowed
            'user@domain..com',
            'user@.domain.com',
            'user@domain.c',  # TLD too short
            '',  # Empty string
            'user@domain@domain.com',  # Multiple @
            'user"@domain.com',  # Quotes not properly handled
            'user@[domain.com]',  # Brackets not valid without IP
        ]
        
        for email in invalid_emails:
            with pytest.raises(ValidationError):
                ClientCreate(
                    name='Test Company',
                    email=email,
                    owner='owner@test.com'
                )
        
        # Test valid domain formats
        valid_domains = [
            'example.com',
            'subdomain.example.com',
            'www.example.com',
            'example-site.com',
            'example123.com',
            'example.co.uk',
            'example.travel',
            'very-long-domain-name-that-is-still-valid.com',
            'xn--nxasmq6b.com',  # Internationalized domain (Chinese)
            '1example.com',  # Can start with number
            'example-with-dashes.com',
            'multiple.sub.domains.example.com'
        ]
        
        for domain in valid_domains:
            domain_obj = DomainCreate(domain=domain)
            assert domain_obj.domain == domain.lower()
        
        # Test invalid domain formats
        invalid_domains = [
            '',  # Empty
            'ab',  # Too short (less than 3 characters)
            'domain',  # No TLD
            '.com',  # No domain
            'domain.',  # Trailing dot without completion
            'domain..com',  # Double dots
            '-domain.com',  # Leading dash
            'domain-.com',  # Trailing dash in subdomain
            'domain .com',  # Space not allowed
            'domain,com',  # Comma instead of dot
            'domain@com',  # @ not allowed
            'domain#com',  # # not allowed
            'do main.com',  # Space in domain
            'domain.c',  # TLD too short
            'domain.toolongtld',  # TLD too long (if we had such validation)
        ]
        
        for domain in invalid_domains:
            with pytest.raises(ValidationError):
                DomainCreate(domain=domain)
        
        # Test domain normalization
        normalization_tests = [
            ('EXAMPLE.COM', 'example.com'),
            ('  example.com  ', 'example.com'),
            ('SUBDOMAIN.EXAMPLE.COM', 'subdomain.example.com'),
            ('ExAmPlE.CoM', 'example.com'),
            ('  MIXED.CASE.DOMAIN.COM  ', 'mixed.case.domain.com')
        ]
        
        for input_domain, expected_output in normalization_tests:
            domain_obj = DomainCreate(domain=input_domain)
            assert domain_obj.domain == expected_output
        
        # Test email validation in different schema contexts
        email_contexts = [
            # (schema_class, field_name, email_value)
            (ClientCreate, 'email', 'test@example.com'),
            (ClientCreate, 'owner', 'owner@example.com'),
            (ClientUpdate, 'email', 'updated@example.com'),
        ]
        
        for schema_class, field_name, email_value in email_contexts:
            if schema_class == ClientCreate:
                if field_name == 'email':
                    obj = schema_class(
                        name='Test Company',
                        owner='owner@test.com',
                        email=email_value
                    )
                    assert getattr(obj, field_name) == email_value
                elif field_name == 'owner':
                    obj = schema_class(
                        name='Test Company',
                        owner=email_value
                    )
                    assert getattr(obj, field_name) == email_value
            elif schema_class == ClientUpdate:
                obj = schema_class(**{field_name: email_value})
                assert getattr(obj, field_name) == email_value
        
        # Test security considerations - potential XSS/injection in emails
        malicious_emails = [
            'user+<script>alert("xss")</script>@domain.com',
            'user+javascript:alert("xss")@domain.com',
            'user+\">@domain.com',
            'user+\'OR\'1\'=\'1@domain.com'
        ]
        
        for malicious_email in malicious_emails:
            with pytest.raises(ValidationError):
                ClientCreate(
                    name='Test Company',
                    email=malicious_email,
                    owner='owner@test.com'
                )
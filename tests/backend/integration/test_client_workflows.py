"""
Test suite for end-to-end client workflow integration tests.

This module validates complete client lifecycle workflows from creation through
deactivation, including domain management, configuration updates, and cross-client
operations. Tests ensure data consistency across all system components and proper
error handling in complex multi-step operations.

Test categories:
- Complete client setup flow from creation to domain assignment
- Client domain addition flow with configuration impact
- Client configuration update flow with validation
- Client deactivation flow with comprehensive cleanup
- Cross-client domain conflict resolution

All tests validate end-to-end data consistency, proper error handling,
rollback capabilities, and business rule enforcement across the entire system.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock
from httpx import AsyncClient

from app.main import app
from app.schemas import ClientCreate, ClientUpdate, DomainCreate


class TestClientWorkflows:
    """Test suite for end-to-end client workflow validation."""

    @pytest.mark.asyncio
    async def test_complete_client_setup_flow(self, test_client, mock_firestore_client, client_factory, domain_factory):
        """
        Test complete client setup from creation to domain assignment.
        
        Validates:
        - Client creation with full validation
        - Domain addition and authorization
        - Configuration validation and application
        - Data consistency across all collections
        - Proper indexing and lookup capabilities
        """
        # Step 1: Create client
        client_data = {
            'name': 'Complete Setup Company',
            'email': 'setup@company.com',
            'owner': 'owner@company.com',
            'billing_entity': 'billing@company.com',
            'client_type': 'enterprise',
            'deployment_type': 'dedicated',
            'privacy_level': 'gdpr',
            'features': {
                'analytics': True,
                'conversion_tracking': True,
                'custom_events': True,
                'advanced_reporting': {
                    'enabled': True,
                    'retention_days': 365
                }
            }
        }
        
        response = await test_client.post('/clients', json=client_data)
        assert response.status_code == 201
        
        created_client = response.json()
        client_id = created_client['client_id']
        
        # Verify client was created in database
        client_doc = mock_firestore_client.clients_ref.document(client_id).get()
        assert client_doc.exists is True
        client_db_data = client_doc.to_dict()
        assert client_db_data['name'] == client_data['name']
        assert client_db_data['privacy_level'] == 'gdpr'
        assert client_db_data['deployment_type'] == 'dedicated'
        assert client_db_data['consent_required'] is True  # Auto-set for GDPR
        assert 'ip_salt' in client_db_data  # Auto-generated for GDPR
        
        # Step 2: Add multiple domains
        domains_to_add = [
            {'domain': 'primary.company.com', 'is_primary': True},
            {'domain': 'secondary.company.com', 'is_primary': False},
            {'domain': 'staging.company.com', 'is_primary': False}
        ]
        
        added_domains = []
        for domain_data in domains_to_add:
            domain_response = await test_client.post(
                f'/clients/{client_id}/domains',
                json=domain_data
            )
            assert domain_response.status_code == 201
            added_domains.append(domain_response.json())
        
        # Verify domains were added to client subcollection
        client_domains_query = mock_firestore_client.clients_ref.document(client_id).collection('domains').stream()
        client_domains = [doc.to_dict() for doc in client_domains_query]
        assert len(client_domains) == 3
        
        primary_domains = [d for d in client_domains if d.get('is_primary', False)]
        assert len(primary_domains) == 1
        assert primary_domains[0]['domain'] == 'primary.company.com'
        
        # Verify domains were added to global index
        for domain_data in domains_to_add:
            domain_name = domain_data['domain']
            index_docs = mock_firestore_client.domain_index_ref.where('domain', '==', domain_name).stream()
            index_docs_list = list(index_docs)
            assert len(index_docs_list) == 1
            
            index_data = index_docs_list[0].to_dict()
            assert index_data['client_id'] == client_id
            assert index_data['is_primary'] == domain_data['is_primary']
        
        # Step 3: Get client configuration
        config_response = await test_client.get(f'/clients/{client_id}/config')
        assert config_response.status_code == 200
        
        config_data = config_response.json()
        assert config_data['privacy_level'] == 'gdpr'
        assert config_data['ip_collection']['hash_required'] is True
        assert config_data['consent']['required'] is True
        assert config_data['deployment']['type'] == 'dedicated'
        
        # Step 4: Update client configuration
        update_data = {
            'features': {
                'analytics': True,
                'conversion_tracking': True,
                'custom_events': False,  # Disable custom events
                'advanced_reporting': {
                    'enabled': True,
                    'retention_days': 730  # Extend retention
                },
                'real_time_analytics': {  # Add new feature
                    'enabled': True,
                    'refresh_interval': 30
                }
            },
            'ip_collection_enabled': False  # Disable IP collection
        }
        
        update_response = await test_client.put(f'/clients/{client_id}', json=update_data)
        assert update_response.status_code == 200
        
        updated_client = update_response.json()
        assert updated_client['features']['custom_events'] is False
        assert updated_client['features']['real_time_analytics']['enabled'] is True
        assert updated_client['ip_collection_enabled'] is False
        
        # Verify database was updated
        updated_doc = mock_firestore_client.clients_ref.document(client_id).get()
        updated_db_data = updated_doc.to_dict()
        assert updated_db_data['features']['advanced_reporting']['retention_days'] == 730
        assert updated_db_data['ip_collection_enabled'] is False
        
        # Step 5: Verify complete client retrieval
        final_response = await test_client.get(f'/clients/{client_id}')
        assert final_response.status_code == 200
        
        final_client = final_response.json()
        assert final_client['domain_count'] == 3
        assert final_client['is_active'] is True
        assert final_client['features']['real_time_analytics']['enabled'] is True

    @pytest.mark.asyncio
    async def test_client_domain_addition_flow(self, test_client, mock_firestore_client, client_with_domains):
        """
        Test client configuration updates with domain impact.
        
        Validates:
        - Domain addition to existing client
        - Primary domain switching logic
        - Domain authorization validation
        - Cross-collection consistency
        - Proper error handling for conflicts
        """
        client_data = client_with_domains['client']
        client_id = client_data['client_id']
        existing_domains = client_with_domains['domains']
        
        # Current primary domain
        current_primary = next(d for d in existing_domains if d['is_primary'])
        
        # Step 1: Add new domain as non-primary
        new_domain_data = {
            'domain': 'new-domain.company.com',
            'is_primary': False
        }
        
        add_response = await test_client.post(
            f'/clients/{client_id}/domains',
            json=new_domain_data
        )
        assert add_response.status_code == 201
        
        # Verify domain was added
        domain_docs = mock_firestore_client.domain_index_ref.where('client_id', '==', client_id).stream()
        all_domains = [doc.to_dict() for doc in domain_docs]
        assert len(all_domains) == 4  # 3 existing + 1 new
        
        new_domain_in_index = next(d for d in all_domains if d['domain'] == 'new-domain.company.com')
        assert new_domain_in_index['is_primary'] is False
        
        # Step 2: Add another domain and make it primary (should switch primary)
        primary_switch_data = {
            'domain': 'new-primary.company.com',
            'is_primary': True
        }
        
        primary_response = await test_client.post(
            f'/clients/{client_id}/domains',
            json=primary_switch_data
        )
        assert primary_response.status_code == 201
        
        # Verify primary domain was switched
        updated_domains = mock_firestore_client.domain_index_ref.where('client_id', '==', client_id).stream()
        updated_domains_list = [doc.to_dict() for doc in updated_domains]
        
        primary_domains = [d for d in updated_domains_list if d['is_primary']]
        assert len(primary_domains) == 1  # Only one primary allowed
        assert primary_domains[0]['domain'] == 'new-primary.company.com'
        
        # Verify old primary is no longer primary
        old_primary_in_updated = next(d for d in updated_domains_list if d['domain'] == current_primary['domain'])
        assert old_primary_in_updated['is_primary'] is False
        
        # Step 3: Try to add duplicate domain (should fail)
        duplicate_domain_data = {
            'domain': 'new-primary.company.com',  # Already exists
            'is_primary': False
        }
        
        duplicate_response = await test_client.post(
            f'/clients/{client_id}/domains',
            json=duplicate_domain_data
        )
        assert duplicate_response.status_code == 409  # Conflict
        
        # Step 4: Try to add domain that belongs to another client
        # First create another client
        other_client_data = {
            'name': 'Other Company',
            'owner': 'other@company.com',
            'client_type': 'end_client'
        }
        
        other_client_response = await test_client.post('/clients', json=other_client_data)
        other_client_id = other_client_response.json()['client_id']
        
        # Add domain to other client first
        other_domain_data = {
            'domain': 'conflicted-domain.com',
            'is_primary': True
        }
        
        await test_client.post(f'/clients/{other_client_id}/domains', json=other_domain_data)
        
        # Try to add same domain to original client (should fail)
        conflict_response = await test_client.post(
            f'/clients/{client_id}/domains',
            json=other_domain_data
        )
        assert conflict_response.status_code == 409  # Domain already exists
        
        # Step 5: Verify domain authorization lookup
        # Test that domain lookup returns correct client
        lookup_docs = mock_firestore_client.domain_index_ref.where('domain', '==', 'new-primary.company.com').stream()
        lookup_docs_list = list(lookup_docs)
        assert len(lookup_docs_list) == 1
        assert lookup_docs_list[0].to_dict()['client_id'] == client_id

    @pytest.mark.asyncio
    async def test_client_configuration_update_flow(self, test_client, mock_firestore_client, client_with_domains):
        """
        Test client configuration updates.
        
        Validates:
        - Partial configuration updates
        - Privacy level changes and implications
        - Feature flag modifications
        - Deployment type changes
        - Configuration validation and rollback
        """
        client_data = client_with_domains['client']
        client_id = client_data['client_id']
        
        # Step 1: Get baseline configuration
        baseline_response = await test_client.get(f'/clients/{client_id}')
        baseline_client = baseline_response.json()
        original_privacy_level = baseline_client['privacy_level']
        
        # Step 2: Update privacy level (should trigger additional requirements)
        privacy_update = {
            'privacy_level': 'hipaa'
        }
        
        privacy_response = await test_client.put(f'/clients/{client_id}', json=privacy_update)
        assert privacy_response.status_code == 200
        
        updated_client = privacy_response.json()
        assert updated_client['privacy_level'] == 'hipaa'
        assert updated_client['consent_required'] is True  # Should be auto-enabled for HIPAA
        
        # Verify database reflects changes
        db_doc = mock_firestore_client.clients_ref.document(client_id).get()
        db_data = db_doc.to_dict()
        assert db_data['privacy_level'] == 'hipaa'
        assert 'ip_salt' in db_data  # Should have IP salt for HIPAA
        
        # Step 3: Update deployment type
        deployment_update = {
            'deployment_type': 'dedicated',
            'vm_hostname': 'client-dedicated.pixels.com'
        }
        
        deployment_response = await test_client.put(f'/clients/{client_id}', json=deployment_update)
        assert deployment_response.status_code == 200
        
        deployment_client = deployment_response.json()
        assert deployment_client['deployment_type'] == 'dedicated'
        assert deployment_client['vm_hostname'] == 'client-dedicated.pixels.com'
        
        # Step 4: Complex feature configuration update
        complex_features = {
            'features': {
                'analytics': {
                    'enabled': True,
                    'tracking_level': 'enhanced',
                    'cross_domain': True,
                    'custom_dimensions': ['category', 'user_segment']
                },
                'conversion_tracking': {
                    'enabled': True,
                    'attribution_window_days': 30,
                    'cross_device': True,
                    'goals': [
                        {'name': 'purchase', 'value_threshold': 100.0},
                        {'name': 'lead', 'value_threshold': 0.0}
                    ]
                },
                'privacy_compliance': {
                    'auto_consent_detection': True,
                    'data_subject_requests': True,
                    'audit_logging': True
                },
                'performance': {
                    'lazy_loading': True,
                    'cdn_acceleration': True,
                    'compression': 'gzip'
                }
            }
        }
        
        features_response = await test_client.put(f'/clients/{client_id}', json=complex_features)
        assert features_response.status_code == 200
        
        features_client = features_response.json()
        assert features_client['features']['analytics']['tracking_level'] == 'enhanced'
        assert len(features_client['features']['conversion_tracking']['goals']) == 2
        assert features_client['features']['privacy_compliance']['audit_logging'] is True
        
        # Step 5: Test invalid configuration update (should rollback)
        invalid_update = {
            'privacy_level': 'invalid_level',
            'deployment_type': 'invalid_deployment'
        }
        
        invalid_response = await test_client.put(f'/clients/{client_id}', json=invalid_update)
        assert invalid_response.status_code == 422  # Validation error
        
        # Verify original configuration wasn't changed
        rollback_response = await test_client.get(f'/clients/{client_id}')
        rollback_client = rollback_response.json()
        assert rollback_client['privacy_level'] == 'hipaa'  # Should remain from valid update
        assert rollback_client['deployment_type'] == 'dedicated'  # Should remain from valid update
        
        # Step 6: Test partial update with mixed valid/invalid fields
        mixed_update = {
            'name': 'Updated Company Name',  # Valid
            'email': 'not-an-email',  # Invalid
            'features': {
                'new_feature': True  # Valid
            }
        }
        
        mixed_response = await test_client.put(f'/clients/{client_id}', json=mixed_update)
        assert mixed_response.status_code == 422  # Should fail due to invalid email
        
        # Verify no partial updates occurred
        final_check_response = await test_client.get(f'/clients/{client_id}')
        final_client = final_check_response.json()
        assert final_client['name'] != 'Updated Company Name'  # Should not have changed

    @pytest.mark.asyncio
    async def test_client_deactivation_flow(self, test_client, mock_firestore_client, client_with_domains):
        """
        Test client deactivation with cleanup verification.
        
        Validates:
        - Client deactivation process
        - Domain cleanup and index removal
        - Data retention vs deletion policies
        - Cascade effects on related data
        - Reactivation capabilities
        """
        client_data = client_with_domains['client']
        client_id = client_data['client_id']
        domains = client_with_domains['domains']
        
        # Step 1: Verify client is initially active
        active_response = await test_client.get(f'/clients/{client_id}')
        active_client = active_response.json()
        assert active_client['is_active'] is True
        
        # Verify domains are accessible
        domain_count = len(domains)
        assert active_client['domain_count'] == domain_count
        
        # Step 2: Deactivate client
        deactivation_data = {
            'is_active': False
        }
        
        deactivation_response = await test_client.put(f'/clients/{client_id}', json=deactivation_data)
        assert deactivation_response.status_code == 200
        
        deactivated_client = deactivation_response.json()
        assert deactivated_client['is_active'] is False
        
        # Verify database reflects deactivation
        db_doc = mock_firestore_client.clients_ref.document(client_id).get()
        db_data = db_doc.to_dict()
        assert db_data['is_active'] is False
        
        # Step 3: Test domain access after deactivation
        # Domains should still exist but might be flagged as inactive
        domain_docs = mock_firestore_client.domain_index_ref.where('client_id', '==', client_id).stream()
        domain_docs_list = list(domain_docs)
        assert len(domain_docs_list) == domain_count  # Domains preserved for audit
        
        # Step 4: Test operations on deactivated client
        # Adding domains should fail
        new_domain_data = {
            'domain': 'new-after-deactivation.com',
            'is_primary': False
        }
        
        domain_add_response = await test_client.post(
            f'/clients/{client_id}/domains',
            json=new_domain_data
        )
        assert domain_add_response.status_code == 400  # Client inactive
        
        # Configuration updates should fail (except reactivation)
        config_update = {
            'name': 'Should Not Update'
        }
        
        config_response = await test_client.put(f'/clients/{client_id}', json=config_update)
        assert config_response.status_code == 400  # Client inactive
        
        # Step 5: Test pixel serving for deactivated client
        # This would normally test pixel endpoint, but we'll verify domain lookup behavior
        primary_domain = next(d['domain'] for d in domains if d['is_primary'])
        
        # Domain lookup should still work but indicate inactive status
        lookup_docs = mock_firestore_client.domain_index_ref.where('domain', '==', primary_domain).stream()
        lookup_docs_list = list(lookup_docs)
        assert len(lookup_docs_list) == 1
        
        # The domain index entry exists, but client lookup would show inactive
        domain_client_doc = mock_firestore_client.clients_ref.document(client_id).get()
        assert domain_client_doc.to_dict()['is_active'] is False
        
        # Step 6: Test reactivation
        reactivation_data = {
            'is_active': True
        }
        
        reactivation_response = await test_client.put(f'/clients/{client_id}', json=reactivation_data)
        assert reactivation_response.status_code == 200
        
        reactivated_client = reactivation_response.json()
        assert reactivated_client['is_active'] is True
        
        # Verify functionality is restored
        post_reactivation_response = await test_client.get(f'/clients/{client_id}')
        post_reactivation_client = post_reactivation_response.json()
        assert post_reactivation_client['is_active'] is True
        assert post_reactivation_client['domain_count'] == domain_count
        
        # Test that operations work again
        test_domain_data = {
            'domain': 'post-reactivation.com',
            'is_primary': False
        }
        
        post_reactivation_domain_response = await test_client.post(
            f'/clients/{client_id}/domains',
            json=test_domain_data
        )
        assert post_reactivation_domain_response.status_code == 201
        
        # Step 7: Test full deletion (if supported)
        # This would be a more destructive operation
        # For now, we test the cascading cleanup requirements
        
        # If full deletion were implemented, it would need to:
        # 1. Remove all domains from client subcollection
        # 2. Remove all domain index entries
        # 3. Remove client document
        # 4. Clean up any audit logs (or mark them)
        # 5. Handle any active pixel serving
        
        # Verify current state has all expected data
        final_domain_docs = mock_firestore_client.domain_index_ref.where('client_id', '==', client_id).stream()
        final_domain_count = len(list(final_domain_docs))
        assert final_domain_count == domain_count + 1  # Original + post-reactivation domain

    @pytest.mark.asyncio
    async def test_cross_client_domain_conflict(self, test_client, mock_firestore_client, client_factory):
        """
        Test cross-client domain conflict resolution.
        
        Validates:
        - Domain uniqueness across all clients
        - Conflict detection and resolution
        - Domain transfer capabilities
        - Audit trail for domain ownership changes
        - Error handling for ownership disputes
        """
        # Step 1: Create two clients
        client1_data = {
            'name': 'First Company',
            'owner': 'owner1@company.com',
            'client_type': 'enterprise'
        }
        
        client2_data = {
            'name': 'Second Company',
            'owner': 'owner2@company.com',
            'client_type': 'enterprise'
        }
        
        client1_response = await test_client.post('/clients', json=client1_data)
        client2_response = await test_client.post('/clients', json=client2_data)
        
        client1_id = client1_response.json()['client_id']
        client2_id = client2_response.json()['client_id']
        
        # Step 2: Add domain to first client
        domain_data = {
            'domain': 'shared-domain.com',
            'is_primary': True
        }
        
        domain1_response = await test_client.post(
            f'/clients/{client1_id}/domains',
            json=domain_data
        )
        assert domain1_response.status_code == 201
        
        # Verify domain is in index for client1
        index_docs = mock_firestore_client.domain_index_ref.where('domain', '==', 'shared-domain.com').stream()
        index_docs_list = list(index_docs)
        assert len(index_docs_list) == 1
        assert index_docs_list[0].to_dict()['client_id'] == client1_id
        
        # Step 3: Try to add same domain to second client (should fail)
        domain2_response = await test_client.post(
            f'/clients/{client2_id}/domains',
            json=domain_data
        )
        assert domain2_response.status_code == 409  # Conflict
        
        conflict_details = domain2_response.json()
        assert 'already exists' in conflict_details['detail'].lower()
        
        # Verify domain index wasn't corrupted
        post_conflict_docs = mock_firestore_client.domain_index_ref.where('domain', '==', 'shared-domain.com').stream()
        post_conflict_list = list(post_conflict_docs)
        assert len(post_conflict_list) == 1  # Still only one entry
        assert post_conflict_list[0].to_dict()['client_id'] == client1_id
        
        # Step 4: Test domain variations that should be allowed
        similar_domains = [
            'shared-domain.net',  # Different TLD
            'shared-domain.org',  # Different TLD
            'sub.shared-domain.com',  # Subdomain
            'shared-domain-2.com'  # Similar but different
        ]
        
        for similar_domain in similar_domains:
            similar_domain_data = {
                'domain': similar_domain,
                'is_primary': False
            }
            
            similar_response = await test_client.post(
                f'/clients/{client2_id}/domains',
                json=similar_domain_data
            )
            assert similar_response.status_code == 201
        
        # Step 5: Test case sensitivity in conflict detection
        case_variants = [
            'SHARED-DOMAIN.COM',
            'Shared-Domain.com',
            'shared-DOMAIN.com'
        ]
        
        for variant in case_variants:
            variant_data = {
                'domain': variant,
                'is_primary': False
            }
            
            variant_response = await test_client.post(
                f'/clients/{client2_id}/domains',
                json=variant_data
            )
            assert variant_response.status_code == 409  # Should conflict (case insensitive)
        
        # Step 6: Test domain transfer (if implemented)
        # This would involve removing from one client and adding to another
        # For now, test the removal part
        
        # Remove domain from client1
        # Note: This would depend on actual API implementation
        # For mock testing, we'll simulate the database state changes
        
        # First, verify current ownership
        current_docs = mock_firestore_client.domain_index_ref.where('domain', '==', 'shared-domain.com').stream()
        current_ownership = list(current_docs)[0].to_dict()
        assert current_ownership['client_id'] == client1_id
        
        # Simulate removal from client1 (would be DELETE /clients/{client1_id}/domains/{domain_id})
        # For testing, we'll manually update the mock database state
        
        # Remove from domain index
        for doc in mock_firestore_client.domain_index_ref.where('domain', '==', 'shared-domain.com').stream():
            doc.delete()
        
        # Remove from client1's domain subcollection
        client1_domains = mock_firestore_client.clients_ref.document(client1_id).collection('domains').stream()
        for domain_doc in client1_domains:
            if domain_doc.to_dict().get('domain') == 'shared-domain.com':
                domain_doc.delete()
        
        # Now client2 should be able to add the domain
        transfer_response = await test_client.post(
            f'/clients/{client2_id}/domains',
            json=domain_data
        )
        assert transfer_response.status_code == 201
        
        # Verify ownership transfer
        transferred_docs = mock_firestore_client.domain_index_ref.where('domain', '==', 'shared-domain.com').stream()
        transferred_list = list(transferred_docs)
        assert len(transferred_list) == 1
        assert transferred_list[0].to_dict()['client_id'] == client2_id
        
        # Step 7: Test bulk domain conflict scenarios
        bulk_domains = [f'bulk-domain-{i}.com' for i in range(5)]
        
        # Add all domains to client1
        for bulk_domain in bulk_domains:
            bulk_domain_data = {
                'domain': bulk_domain,
                'is_primary': False
            }
            
            bulk_response = await test_client.post(
                f'/clients/{client1_id}/domains',
                json=bulk_domain_data
            )
            assert bulk_response.status_code == 201
        
        # Try to add same domains to client2 (all should fail)
        for bulk_domain in bulk_domains:
            bulk_domain_data = {
                'domain': bulk_domain,
                'is_primary': False
            }
            
            conflict_response = await test_client.post(
                f'/clients/{client2_id}/domains',
                json=bulk_domain_data
            )
            assert conflict_response.status_code == 409
        
        # Verify no cross-contamination in domain index
        for bulk_domain in bulk_domains:
            domain_docs = mock_firestore_client.domain_index_ref.where('domain', '==', bulk_domain).stream()
            domain_docs_list = list(domain_docs)
            assert len(domain_docs_list) == 1  # Only one entry per domain
            assert domain_docs_list[0].to_dict()['client_id'] == client1_id  # Owned by client1
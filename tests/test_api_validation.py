"""
Test API Input Validation and Error Handling

Comprehensive validation testing for all API endpoints including:
- Request validation (field types, constraints, required fields)
- Response validation (status codes, error messages)
- Business logic validation (entity relationships, constraints)
- Edge cases and boundary conditions
"""

import pytest
from uuid import uuid4
from datetime import datetime
import json

from .conftest import test_data_cleanup


class TestEntityValidation:
    """Test entity endpoint input validation"""
    
    def test_entity_create_missing_required_fields(self, client):
        """Test entity creation with missing required fields"""
        # Missing name
        response = client.post("/api/v1/entities", json={
            "entity_type": "character",
            "description": "Missing name"
        })
        assert response.status_code == 422
        error_detail = response.json()["detail"]
        assert any("name" in str(error).lower() for error in error_detail)
        
        # Missing entity_type
        response = client.post("/api/v1/entities", json={
            "name": "Test Entity",
            "description": "Missing entity type"
        })
        assert response.status_code == 422
        error_detail = response.json()["detail"]
        assert any("entity_type" in str(error).lower() for error in error_detail)
    
    def test_entity_create_invalid_entity_type(self, client):
        """Test entity creation with invalid entity type"""
        response = client.post("/api/v1/entities", json={
            "name": "Test Entity",
            "entity_type": "invalid_type",
            "description": "Should fail validation"
        })
        assert response.status_code == 422
        error_detail = response.json()["detail"]
        assert any("entity_type" in str(error).lower() for error in error_detail)
    
    def test_entity_create_invalid_field_types(self, client):
        """Test entity creation with invalid field types"""
        # Name as non-string
        response = client.post("/api/v1/entities", json={
            "name": 123,
            "entity_type": "character"
        })
        assert response.status_code == 422
        
        # Metadata as non-object
        response = client.post("/api/v1/entities", json={
            "name": "Test Entity",
            "entity_type": "character",
            "metadata": "should be object"
        })
        assert response.status_code == 422
    
    def test_entity_create_string_length_validation(self, client):
        """Test entity creation with string length violations"""
        # Empty name
        response = client.post("/api/v1/entities", json={
            "name": "",
            "entity_type": "character"
        })
        assert response.status_code == 422
        
        # Name too long (exceeds 255 characters)
        response = client.post("/api/v1/entities", json={
            "name": "A" * 256,
            "entity_type": "character"
        })
        assert response.status_code == 422
    
    def test_entity_update_validation(self, client, sample_entity_data, cleanup_test_data):
        """Test entity update validation"""
        # Create entity first
        create_response = client.post("/api/v1/entities", json=sample_entity_data)
        create_data = create_response.json()
        assert create_data["success"] is True
        entity = create_data["data"]["entity"]
        test_data_cleanup["entities"].append(entity["id"])
        
        # Invalid entity type in update
        response = client.put(f"/api/v1/entities/{entity['id']}", json={
            "entity_type": "invalid_type"
        })
        assert response.status_code == 422
        
        # Invalid field types in update
        response = client.put(f"/api/v1/entities/{entity['id']}", json={
            "metadata": "should be object"
        })
        assert response.status_code == 422
    
    def test_entity_get_invalid_uuid(self, client):
        """Test entity retrieval with invalid UUID format"""
        # Invalid UUID format
        response = client.get("/api/v1/entities/not-a-valid-uuid")
        assert response.status_code == 422
        
        # Valid UUID format but non-existent entity
        fake_uuid = str(uuid4())
        response = client.get(f"/api/v1/entities/{fake_uuid}")
        assert response.status_code == 404


class TestSceneValidation:
    """Test scene endpoint input validation"""
    
    def test_scene_create_missing_required_fields(self, client):
        """Test scene creation with missing required fields"""
        # Missing title
        response = client.post("/api/v1/scenes", json={
            "timestamp": 100
        })
        assert response.status_code == 422
        error_detail = response.json()["detail"]
        assert any("title" in str(error).lower() for error in error_detail)
    
    def test_scene_create_invalid_field_types(self, client):
        """Test scene creation with invalid field types"""
        # Title as non-string
        response = client.post("/api/v1/scenes", json={
            "title": 123,
            "timestamp": 100
        })
        assert response.status_code == 422
        
        # Timestamp as string
        response = client.post("/api/v1/scenes", json={
            "title": "Test Scene",
            "timestamp": "should be integer"
        })
        assert response.status_code == 422
        
        # Invalid location_id format
        response = client.post("/api/v1/scenes", json={
            "title": "Test Scene",
            "location_id": "not-a-uuid"
        })
        assert response.status_code == 422
    
    def test_scene_create_boundary_values(self, client, cleanup_test_data):
        """Test scene creation with boundary values"""
        # Zero timestamp (should be valid)
        response = client.post("/api/v1/scenes", json={
            "title": "Zero Timestamp Scene",
            "timestamp": 0
        })
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["success"] is True
        scene = response_data["data"]["scene"]
        test_data_cleanup["scenes"].append(scene["id"])
        assert scene["timestamp"] == 0
        
        # Negative timestamp (should be valid for "before story start")
        response = client.post("/api/v1/scenes", json={
            "title": "Negative Timestamp Scene", 
            "timestamp": -100
        })
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["success"] is True
        scene = response_data["data"]["scene"]
        test_data_cleanup["scenes"].append(scene["id"])
        assert scene["timestamp"] == -100
        
        # Very large timestamp
        response = client.post("/api/v1/scenes", json={
            "title": "Large Timestamp Scene",
            "timestamp": 999999999
        })
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["success"] is True
        scene = response_data["data"]["scene"]
        test_data_cleanup["scenes"].append(scene["id"])
        assert scene["timestamp"] == 999999999
    
    def test_scene_create_with_nonexistent_location(self, client, cleanup_test_data):
        """Test scene creation with non-existent location_id"""
        fake_location_id = str(uuid4())
        response = client.post("/api/v1/scenes", json={
            "title": "Scene with Fake Location",
            "location_id": fake_location_id,
            "timestamp": 100
        })
        # This might succeed at API level but fail at database level
        # depending on foreign key constraint enforcement
        assert response.status_code in [200, 400, 422]
        
        if response.status_code == 200:
            response_data = response.json()
            assert response_data["success"] is True
            scene = response_data["data"]["scene"]
            test_data_cleanup["scenes"].append(scene["id"])
    
    def test_scene_update_validation(self, client, cleanup_test_data):
        """Test scene update validation"""
        # Create scene first
        scene_response = client.post("/api/v1/scenes", json={
            "title": "Update Test Scene",
            "timestamp": 100
        })
        scene_response_data = scene_response.json()
        assert scene_response_data["success"] is True
        scene = scene_response_data["data"]["scene"]
        test_data_cleanup["scenes"].append(scene["id"])
        
        # Invalid field types in update
        response = client.put(f"/api/v1/scenes/{scene['id']}", json={
            "title": 123
        })
        assert response.status_code == 422
        
        response = client.put(f"/api/v1/scenes/{scene['id']}", json={
            "timestamp": "not an integer"
        })
        assert response.status_code == 422


class TestSceneBlockValidation:
    """Test scene block endpoint input validation"""
    
    def test_block_create_missing_required_fields(self, client, cleanup_test_data):
        """Test scene block creation with missing required fields"""
        # Create scene first
        scene_response = client.post("/api/v1/scenes", json={
            "title": "Block Test Scene",
            "timestamp": 100
        })
        scene_response_data = scene_response.json()
        assert scene_response_data["success"] is True
        scene = scene_response_data["data"]["scene"]
        test_data_cleanup["scenes"].append(scene["id"])
        
        # Missing block_type
        response = client.post(f"/api/v1/scenes/{scene['id']}/blocks", json={
            "content": "Missing block type",
            "order": 1,
            "scene_id": scene["id"]
        })
        assert response.status_code == 422
        
        # Missing content (should be allowed since it's optional)
        response = client.post(f"/api/v1/scenes/{scene['id']}/blocks", json={
            "block_type": "prose",
            "order": 1,
            "scene_id": scene["id"]
        })
        assert response.status_code == 200  # Content is optional
        if response.status_code == 200:
            response_data = response.json()
            assert response_data["success"] is True
            block = response_data["data"]["block"]
            test_data_cleanup["scene_blocks"].append(block["id"])
        
        # Missing order
        response = client.post(f"/api/v1/scenes/{scene['id']}/blocks", json={
            "block_type": "prose",
            "content": "Missing order",
            "scene_id": scene["id"]
        })
        assert response.status_code == 422
    
    def test_block_invalid_block_type(self, client, cleanup_test_data):
        """Test scene block creation with invalid block type"""
        # Create scene first
        scene_response = client.post("/api/v1/scenes", json={
            "title": "Block Type Test Scene",
            "timestamp": 100
        })
        scene_response_data = scene_response.json()
        assert scene_response_data["success"] is True
        scene = scene_response_data["data"]["scene"]
        test_data_cleanup["scenes"].append(scene["id"])
        
        # Invalid block type
        response = client.post(f"/api/v1/scenes/{scene['id']}/blocks", json={
            "block_type": "invalid_type",
            "content": "This should fail",
            "order": 1,
            "scene_id": scene["id"]
        })
        assert response.status_code == 422
        error_detail = response.json()["detail"]
        assert any("block_type" in str(error).lower() for error in error_detail)
    
    def test_block_dialogue_validation(self, client, sample_entity_data, cleanup_test_data):
        """Test dialogue block specific validation"""
        # Create character and scene
        char_response = client.post("/api/v1/entities", json=sample_entity_data)
        char_response_data = char_response.json()
        assert char_response_data["success"] is True
        character = char_response_data["data"]["entity"]
        test_data_cleanup["entities"].append(character["id"])
        
        scene_response = client.post("/api/v1/scenes", json={
            "title": "Dialogue Test Scene",
            "timestamp": 100
        })
        scene_response_data = scene_response.json()
        assert scene_response_data["success"] is True
        scene = scene_response_data["data"]["scene"]
        test_data_cleanup["scenes"].append(scene["id"])
        
        # Dialogue with invalid speaker_id format
        response = client.post(f"/api/v1/scenes/{scene['id']}/blocks", json={
            "block_type": "dialogue",
            "content": "Hello there!",
            "order": 1,
            "scene_id": scene["id"],
            "lines": "not-an-object"  # Invalid lines format
        })
        assert response.status_code == 422
        
        # Dialogue with invalid listener_ids format
        response = client.post(f"/api/v1/scenes/{scene['id']}/blocks", json={
            "block_type": "dialogue",
            "content": "Hello there!",
            "order": 1,
            "scene_id": scene["id"],
            "lines": {
                "speaker_id": character["id"],
                "listener_ids": ["not-a-uuid"]  # Invalid UUID in lines
            }
        })
        assert response.status_code == 422
        
        # Valid dialogue block
        response = client.post(f"/api/v1/scenes/{scene['id']}/blocks", json={
            "block_type": "dialogue",
            "content": "Hello there!",
            "order": 1,
            "scene_id": scene["id"],
            "lines": {
                "speaker_id": character["id"],
                "listener_ids": [character["id"]],
                "emotion": "friendly"
            }
        })
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["success"] is True
        block = response_data["data"]["block"]
        test_data_cleanup["scene_blocks"].append(block["id"])
    
    def test_block_milestone_validation(self, client, cleanup_test_data):
        """Test milestone block specific validation"""
        # Create scene
        scene_response = client.post("/api/v1/scenes", json={
            "title": "Milestone Test Scene",
            "timestamp": 100
        })
        scene_response_data = scene_response.json()
        assert scene_response_data["success"] is True
        scene = scene_response_data["data"]["scene"]
        test_data_cleanup["scenes"].append(scene["id"])
        
        # Milestone with invalid subject_id format
        response = client.post(f"/api/v1/scenes/{scene['id']}/blocks", json={
            "block_type": "milestone",
            "content": "Hero obtains sword",
            "order": 1,
            "scene_id": scene["id"],
            "subject_id": "not-a-uuid",
            "verb": "obtains"
        })
        assert response.status_code == 422
    
    def test_block_sort_order_validation(self, client, cleanup_test_data):
        """Test sort_order field validation"""
        # Create scene
        scene_response = client.post("/api/v1/scenes", json={
            "title": "Sort Order Test Scene",
            "timestamp": 100
        })
        scene_response_data = scene_response.json()
        assert scene_response_data["success"] is True
        scene = scene_response_data["data"]["scene"]
        test_data_cleanup["scenes"].append(scene["id"])
        
        # Negative order
        response = client.post(f"/api/v1/scenes/{scene['id']}/blocks", json={
            "block_type": "prose",
            "content": "Negative order",
            "order": -1,
            "scene_id": scene["id"]
        })
        # This should fail validation since order must be >= 0
        assert response.status_code == 422
        
        # Zero order
        response = client.post(f"/api/v1/scenes/{scene['id']}/blocks", json={
            "block_type": "prose",
            "content": "Zero order",
            "order": 0,
            "scene_id": scene["id"]
        })
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["success"] is True
        block = response_data["data"]["block"]
        test_data_cleanup["scene_blocks"].append(block["id"])
    
    def test_block_create_for_nonexistent_scene(self, client):
        """Test creating block for non-existent scene"""
        fake_scene_id = str(uuid4())
        response = client.post(f"/api/v1/scenes/{fake_scene_id}/blocks", json={
            "block_type": "prose",
            "content": "Block for fake scene",
            "order": 1,
            "scene_id": fake_scene_id
        })
        assert response.status_code == 404


class TestMilestoneValidation:
    """Test milestone endpoint input validation (first-class entities)"""
    
    def test_milestone_create_missing_required_fields(self, client):
        """Test milestone creation with missing required fields"""
        # Missing subject_id
        response = client.post("/api/v1/milestones", json={
            "verb": "defeats",
            "object_id": str(uuid4()),
            "timestamp": 100
        })
        assert response.status_code == 422
        
        # Missing verb
        response = client.post("/api/v1/milestones", json={
            "subject_id": str(uuid4()),
            "object_id": str(uuid4()),
            "timestamp": 100
        })
        assert response.status_code == 422
        
        # Missing object_id
        response = client.post("/api/v1/milestones", json={
            "subject_id": str(uuid4()),
            "verb": "defeats",
            "timestamp": 100
        })
        assert response.status_code == 422
        
        # Missing timestamp
        response = client.post("/api/v1/milestones", json={
            "subject_id": str(uuid4()),
            "verb": "defeats",
            "object_id": str(uuid4())
        })
        assert response.status_code == 422
    
    def test_milestone_create_invalid_uuid_fields(self, client):
        """Test milestone creation with invalid UUID fields"""
        # Invalid subject_id
        response = client.post("/api/v1/milestones", json={
            "subject_id": "not-a-uuid",
            "verb": "defeats",
            "object_id": str(uuid4()),
            "timestamp": 100
        })
        assert response.status_code == 422
        
        # Invalid object_id
        response = client.post("/api/v1/milestones", json={
            "subject_id": str(uuid4()),
            "verb": "defeats", 
            "object_id": "not-a-uuid",
            "timestamp": 100
        })
        assert response.status_code == 422
    
    def test_milestone_create_invalid_field_types(self, client):
        """Test milestone creation with invalid field types"""
        # Timestamp as string
        response = client.post("/api/v1/milestones", json={
            "subject_id": str(uuid4()),
            "verb": "defeats",
            "object_id": str(uuid4()),
            "timestamp": "not an integer"
        })
        assert response.status_code == 422
        
        # Verb as non-string
        response = client.post("/api/v1/milestones", json={
            "subject_id": str(uuid4()),
            "verb": 123,
            "object_id": str(uuid4()),
            "timestamp": 100
        })
        assert response.status_code == 422


class TestGoalValidation:
    """Test story goal endpoint input validation"""
    
    def test_goal_create_missing_required_fields(self, client):
        """Test goal creation with missing required fields"""
        # Missing subject_id
        response = client.post("/api/v1/goals", json={
            "verb": "rescue",
            "object_id": str(uuid4())
        })
        assert response.status_code == 422
        
        # Missing verb
        response = client.post("/api/v1/goals", json={
            "subject_id": str(uuid4()),
            "object_id": str(uuid4())
        })
        assert response.status_code == 422
        
        # Missing object_id
        response = client.post("/api/v1/goals", json={
            "subject_id": str(uuid4()),
            "verb": "rescue"
        })
        assert response.status_code == 422
    
    def test_goal_create_invalid_uuid_fields(self, client):
        """Test goal creation with invalid UUID fields"""
        # Invalid subject_id
        response = client.post("/api/v1/goals", json={
            "subject_id": "not-a-uuid",
            "verb": "rescue",
            "object_id": str(uuid4())
        })
        assert response.status_code == 422
        
        # Invalid object_id
        response = client.post("/api/v1/goals", json={
            "subject_id": str(uuid4()),
            "verb": "rescue",
            "object_id": "not-a-uuid"
        })
        assert response.status_code == 422
    
    def test_goal_create_invalid_field_types(self, client):
        """Test goal creation with invalid field types"""
        # Verb as non-string
        response = client.post("/api/v1/goals", json={
            "subject_id": str(uuid4()),
            "verb": 123,
            "object_id": str(uuid4())
        })
        assert response.status_code == 422


class TestCommonValidationPatterns:
    """Test common validation patterns across all endpoints"""
    
    def test_invalid_json_payload(self, client):
        """Test endpoints with invalid JSON payloads"""
        import requests
        
        # Use requests directly to send malformed JSON
        base_url = client.base_url
        
        # Malformed JSON to entity creation
        response = requests.post(
            f"{base_url}/api/v1/entities",
            data="{ invalid json }",
            headers={"Content-Type": "application/json"}
        )
        assert response.status_code == 422
    
    def test_missing_content_type(self, client):
        """Test endpoints without Content-Type header"""
        import requests
        
        base_url = client.base_url
        
        # Missing Content-Type header
        response = requests.post(
            f"{base_url}/api/v1/entities",
            data='{"name": "Test", "entity_type": "character"}'
        )
        # FastAPI should handle this gracefully
        assert response.status_code in [200, 422]
    
    def test_empty_request_body(self, client):
        """Test endpoints with empty request body"""
        # Empty body for entity creation
        response = client.post("/api/v1/entities", json={})
        assert response.status_code == 422
        
        # Empty body for scene creation
        response = client.post("/api/v1/scenes", json={})
        assert response.status_code == 422
    
    def test_oversized_request_body(self, client):
        """Test endpoints with oversized request bodies"""
        # Very large metadata field
        large_metadata = {
            "large_field": "A" * 100000  # 100KB string
        }
        
        response = client.post("/api/v1/entities", json={
            "name": "Large Entity",
            "entity_type": "character",
            "metadata": large_metadata
        })
        # This should either succeed or fail gracefully
        assert response.status_code in [200, 413, 422]
    
    def test_null_values_in_required_fields(self, client):
        """Test endpoints with null values in required fields"""
        # Null name in entity creation
        response = client.post("/api/v1/entities", json={
            "name": None,
            "entity_type": "character"
        })
        assert response.status_code == 422
        
        # Null title in scene creation
        response = client.post("/api/v1/scenes", json={
            "title": None,
            "timestamp": 100
        })
        assert response.status_code == 422
    
    def test_unicode_and_special_characters(self, client, cleanup_test_data):
        """Test endpoints with Unicode and special characters"""
        # Unicode characters in entity name
        response = client.post("/api/v1/entities", json={
            "name": "测试角色 🎭 éñüñé",
            "entity_type": "character",
            "description": "Unicode description with emoji 🌟"
        })
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["success"] is True
        entity = response_data["data"]["entity"]
        test_data_cleanup["entities"].append(entity["id"])
        assert entity["name"] == "测试角色 🎭 éñüñé"
        
        # Special characters in scene title
        response = client.post("/api/v1/scenes", json={
            "title": "Scene: Chapter 1 - \"The Beginning\" (Part A) [Draft]",
            "timestamp": 100
        })
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["success"] is True
        scene = response_data["data"]["scene"]
        test_data_cleanup["scenes"].append(scene["id"])
    
    def test_sql_injection_attempts(self, client):
        """Test endpoints against SQL injection attempts"""
        # SQL injection attempt in entity name
        response = client.post("/api/v1/entities", json={
            "name": "'; DROP TABLE entities; --",
            "entity_type": "character"
        })
        # Should succeed as a literal string (SQL injection prevented by ORM)
        assert response.status_code == 200
        
        # Clean up the test entity
        if response.status_code == 200:
            response_data = response.json()
            assert response_data["success"] is True
            entity = response_data["data"]["entity"]
            client.delete(f"/api/v1/entities/{entity['id']}")
    
    def test_xss_attempts(self, client, cleanup_test_data):
        """Test endpoints against XSS attempts"""
        # XSS attempt in entity description
        response = client.post("/api/v1/entities", json={
            "name": "XSS Test Entity",
            "entity_type": "character",
            "description": "<script>alert('xss')</script>"
        })
        assert response.status_code == 200
        response_data = response.json()
        assert response_data["success"] is True
        entity = response_data["data"]["entity"]
        test_data_cleanup["entities"].append(entity["id"])
        
        # Content should be stored as-is (XSS prevention handled at display layer)
        assert entity["description"] == "<script>alert('xss')</script>"


class TestConcurrencyAndRaceConditions:
    """Test API behavior under concurrent access"""
    
    def test_concurrent_entity_creation(self, client):
        """Test creating entities concurrently"""
        import threading
        import time
        
        results = []
        errors = []
        
        def create_entity(thread_id):
            try:
                response = client.post("/api/v1/entities", json={
                    "name": f"Concurrent Entity {thread_id}",
                    "entity_type": "character",
                    "metadata": {"thread_id": thread_id}
                })
                results.append((thread_id, response.status_code, response.json()))
            except Exception as e:
                errors.append((thread_id, str(e)))
        
        # Create 5 entities concurrently
        threads = []
        for i in range(5):
            thread = threading.Thread(target=create_entity, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check results
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 5, f"Expected 5 results, got {len(results)}"
        
        # All should succeed
        for thread_id, status_code, response_data in results:
            assert status_code == 200, f"Thread {thread_id} failed with status {status_code}"
            assert response_data["success"] is True
            entity = response_data["data"]["entity"]
            assert entity["name"] == f"Concurrent Entity {thread_id}"
        
        # Clean up created entities
        for thread_id, status_code, response_data in results:
            if status_code == 200:
                entity_id = response_data["data"]["entity"]["id"]
                client.delete(f"/api/v1/entities/{entity_id}")
    
    def test_concurrent_block_creation(self, client, cleanup_test_data):
        """Test creating scene blocks concurrently"""
        import threading
        
        # Create scene first
        scene_response = client.post("/api/v1/scenes", json={
            "title": "Concurrent Block Test Scene",
            "timestamp": 100
        })
        scene_response_data = scene_response.json()
        assert scene_response_data["success"] is True
        scene = scene_response_data["data"]["scene"]
        test_data_cleanup["scenes"].append(scene["id"])
        
        results = []
        errors = []
        
        def create_block(thread_id):
            try:
                response = client.post(f"/api/v1/scenes/{scene['id']}/blocks", json={
                    "block_type": "prose",
                    "content": f"Concurrent block content {thread_id}",
                    "order": thread_id + 1,
                    "scene_id": scene["id"]
                })
                results.append((thread_id, response.status_code, response.json()))
            except Exception as e:
                errors.append((thread_id, str(e)))
        
        # Create 3 blocks concurrently
        threads = []
        for i in range(3):
            thread = threading.Thread(target=create_block, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Check results
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 3, f"Expected 3 results, got {len(results)}"
        
        # All should succeed
        for thread_id, status_code, response_data in results:
            assert status_code == 200, f"Thread {thread_id} failed with status {status_code}"
            assert response_data["success"] is True
            block = response_data["data"]["block"]
            test_data_cleanup["scene_blocks"].append(block["id"])


class TestPerformanceAndLimits:
    """Test API performance characteristics and limits"""
    
    def test_large_metadata_handling(self, client, cleanup_test_data):
        """Test handling of large metadata objects"""
        # Create entity with large metadata
        large_metadata = {
            f"field_{i}": f"value_{i}" * 100  # Each field ~600 chars
            for i in range(100)  # 100 fields
        }
        
        response = client.post("/api/v1/entities", json={
            "name": "Large Metadata Entity",
            "entity_type": "character",
            "metadata": large_metadata
        })
        
        # Should succeed or fail gracefully
        assert response.status_code in [200, 413, 422]
        
        if response.status_code == 200:
            response_data = response.json()
            assert response_data["success"] is True
            entity = response_data["data"]["entity"]
            test_data_cleanup["entities"].append(entity["id"])
            assert len(entity["metadata"]) == 100
    
    def test_response_time_reasonable(self, client):
        """Test that API responses are reasonably fast"""
        import time
        
        # Test entity listing performance
        start_time = time.time()
        response = client.get("/api/v1/entities")
        end_time = time.time()
        
        assert response.status_code == 200
        response_time = end_time - start_time
        assert response_time < 5.0, f"Entity listing took too long: {response_time:.2f}s"
        
        # Test health check performance
        start_time = time.time()
        response = client.get("/health")
        end_time = time.time()
        
        assert response.status_code == 200
        response_time = end_time - start_time
        assert response_time < 2.0, f"Health check took too long: {response_time:.2f}s"
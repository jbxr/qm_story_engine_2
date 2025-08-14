"""Test suite for relationships API with temporal support

Comprehensive tests covering CRUD operations, temporal queries, and API field mapping.
"""

import pytest
from fastapi.testclient import TestClient
from uuid import uuid4
import json


def test_create_relationship(client: TestClient, sample_entities):
    """Test creating a new relationship with temporal support"""
    # Use sample entities for relationship
    entity1_id = sample_entities[0]["id"]
    entity2_id = sample_entities[1]["id"]
    
    relationship_data = {
        "source_id": entity1_id,
        "target_id": entity2_id,
        "relation_type": "friends_with",
        "weight": 0.8,
        "starts_at": 100,
        "ends_at": 500,
        "meta": {"intensity": "high"}
    }
    
    response = client.post("/api/v1/relationships/", json=relationship_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "data" in data
    
    # Check API field mapping
    rel_data = data["data"]
    assert rel_data["subject_id"] == entity1_id  # source_id mapped to subject_id
    assert rel_data["object_id"] == entity2_id   # target_id mapped to object_id
    assert rel_data["predicate"] == "friends_with"  # relation_type mapped to predicate
    assert rel_data["weight"] == 0.8
    assert rel_data["starts_at"] == 100
    assert rel_data["ends_at"] == 500
    assert rel_data["meta"]["intensity"] == "high"
    assert "id" in rel_data
    assert "created_at" in rel_data


def test_get_relationship(client: TestClient, sample_relationship):
    """Test retrieving a specific relationship by ID"""
    relationship_id = sample_relationship["id"]
    
    response = client.get(f"/api/v1/relationships/{relationship_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    
    rel_data = data["data"]
    assert rel_data["id"] == relationship_id
    assert "subject_id" in rel_data
    assert "object_id" in rel_data
    assert "predicate" in rel_data


def test_get_nonexistent_relationship(client: TestClient):
    """Test retrieving a relationship that doesn't exist"""
    fake_id = str(uuid4())
    
    response = client.get(f"/api/v1/relationships/{fake_id}")
    
    assert response.status_code == 404


def test_update_relationship(client: TestClient, sample_relationship):
    """Test updating relationship fields including temporal bounds"""
    relationship_id = sample_relationship["id"]
    
    update_data = {
        "relation_type": "close_friends_with",
        "weight": 0.9,
        "starts_at": 150,
        "ends_at": 600,
        "meta": {"intensity": "very_high", "updated": True}
    }
    
    response = client.put(f"/api/v1/relationships/{relationship_id}", json=update_data)
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    
    rel_data = data["data"]
    assert rel_data["predicate"] == "close_friends_with"
    assert rel_data["weight"] == 0.9
    assert rel_data["starts_at"] == 150
    assert rel_data["ends_at"] == 600
    assert rel_data["meta"]["intensity"] == "very_high"
    assert rel_data["meta"]["updated"] is True


def test_delete_relationship(client: TestClient, sample_relationship):
    """Test deleting a relationship"""
    relationship_id = sample_relationship["id"]
    
    response = client.delete(f"/api/v1/relationships/{relationship_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["id"] == relationship_id
    
    # Verify deletion
    get_response = client.get(f"/api/v1/relationships/{relationship_id}")
    assert get_response.status_code == 404


def test_get_entity_relationships(client: TestClient, sample_temporal_relationships):
    """Test retrieving all relationships for an entity"""
    entity_id = sample_temporal_relationships["entity_id"]
    
    response = client.get(f"/api/v1/relationships/entity/{entity_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["data"]) > 0  # Should have relationships
    
    # Check that all relationships involve the entity
    for rel in data["data"]:
        assert entity_id in [rel["subject_id"], rel["object_id"]]


def test_get_entity_relationships_with_temporal_filter(client: TestClient, sample_temporal_relationships):
    """Test retrieving entity relationships with temporal filtering"""
    entity_id = sample_temporal_relationships["entity_id"]
    
    # Test timestamp where relationship is active
    response = client.get(f"/api/v1/relationships/entity/{entity_id}?time=300")
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    # Should have the relationship that spans 200-400
    assert len(data["data"]) == 1
    
    # Test timestamp where relationship is not active
    response = client.get(f"/api/v1/relationships/entity/{entity_id}?time=600")
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    # Should have no relationships at this time
    assert len(data["data"]) == 0


def test_get_active_relationships(client: TestClient, sample_temporal_relationships):
    """Test getting active relationships at a specific timestamp"""
    response = client.get("/api/v1/relationships/active?time=300")
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    
    # Should return relationships active at timestamp 300
    assert len(data["data"]) >= 1
    
    # Verify all returned relationships are active at the timestamp
    for rel in data["data"]:
        starts_at = rel.get("starts_at")
        ends_at = rel.get("ends_at")
        
        # If temporal bounds exist, verify timestamp is within range
        if starts_at is not None:
            assert starts_at <= 300
        if ends_at is not None:
            assert ends_at >= 300


def test_get_active_relationships_with_entity_filter(client: TestClient, sample_temporal_relationships):
    """Test getting active relationships filtered by entity"""
    entity_id = sample_temporal_relationships["entity_id"]
    
    response = client.get(f"/api/v1/relationships/active?time=300&entity_id={entity_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    
    # Should return relationships involving the entity at timestamp 300
    for rel in data["data"]:
        assert entity_id in [rel["subject_id"], rel["object_id"]]


def test_get_overlapping_relationships(client: TestClient, sample_temporal_relationships):
    """Test getting relationships that overlap with a time range"""
    response = client.get("/api/v1/relationships/overlapping?from=200&to=400")
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    
    # Should return relationships that overlap with range 200-400
    assert len(data["data"]) >= 1


def test_get_relationships_between_entities(client: TestClient, sample_temporal_relationships):
    """Test getting relationships between two specific entities"""
    entity1_id = sample_temporal_relationships["entity_id"]
    entity2_id = sample_temporal_relationships["target_id"]
    
    response = client.get(f"/api/v1/relationships/between/{entity1_id}/{entity2_id}")
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    
    # Should return relationships between the two entities
    for rel in data["data"]:
        entities = {rel["subject_id"], rel["object_id"]}
        assert entity1_id in entities
        assert entity2_id in entities


def test_get_relationships_between_entities_with_time(client: TestClient, sample_temporal_relationships):
    """Test getting relationships between entities with temporal filtering"""
    entity1_id = sample_temporal_relationships["entity_id"]
    entity2_id = sample_temporal_relationships["target_id"]
    
    # Test when relationship is active
    response = client.get(f"/api/v1/relationships/between/{entity1_id}/{entity2_id}?time=300")
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["data"]) == 1
    
    # Test when relationship is not active
    response = client.get(f"/api/v1/relationships/between/{entity1_id}/{entity2_id}?time=600")
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["data"]) == 0


def test_get_entity_relationship_graph(client: TestClient, sample_temporal_relationships):
    """Test getting relationship graph for an entity"""
    entity_id = sample_temporal_relationships["entity_id"]
    
    response = client.get(f"/api/v1/relationships/graph/{entity_id}?max_depth=2")
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    
    graph = data["data"]
    assert graph["center_entity"] == entity_id
    assert "relationships" in graph
    assert "entities" in graph
    assert entity_id in graph["entities"]


def test_get_entity_relationship_graph_with_time(client: TestClient, sample_temporal_relationships):
    """Test getting relationship graph with temporal filtering"""
    entity_id = sample_temporal_relationships["entity_id"]
    
    response = client.get(f"/api/v1/relationships/graph/{entity_id}?time=300&max_depth=1")
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    
    graph = data["data"]
    assert graph["timestamp"] == 300
    # Should include temporal filtering


def test_batch_relationship_operations(client: TestClient, sample_entities):
    """Test executing multiple relationship operations in batch"""
    entity1_id = sample_entities[0]["id"]
    entity2_id = sample_entities[1]["id"]
    
    # Create a relationship first for update/delete operations
    create_response = client.post("/api/v1/relationships/", json={
        "source_id": entity1_id,
        "target_id": entity2_id,
        "relation_type": "test_relation",
        "weight": 0.5
    })
    relationship_id = create_response.json()["data"]["id"]
    
    batch_operations = [
        {
            "operation": "create",
            "data": {
                "source_id": entity2_id,
                "target_id": entity1_id,
                "relation_type": "reverse_relation",
                "weight": 0.7
            }
        },
        {
            "operation": "update",
            "relationship_id": relationship_id,
            "data": {
                "weight": 0.9
            }
        },
        {
            "operation": "delete",
            "relationship_id": relationship_id
        }
    ]
    
    response = client.post("/api/v1/relationships/batch", json=batch_operations)
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["data"]) == 3
    
    # Check operation results
    results = data["data"]
    assert results[0]["operation"] == "create"
    assert results[1]["operation"] == "update"
    assert results[2]["operation"] == "delete"


def test_list_relationships_with_pagination(client: TestClient, sample_temporal_relationships):
    """Test listing relationships with pagination"""
    response = client.get("/api/v1/relationships/?limit=10&offset=0")
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert "pagination" in data
    assert data["pagination"]["limit"] == 10
    assert data["pagination"]["offset"] == 0


def test_list_relationships_with_temporal_filter(client: TestClient, sample_temporal_relationships):
    """Test listing relationships with temporal filtering"""
    response = client.get("/api/v1/relationships/?time=300&limit=10")
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    
    # Should only return relationships active at timestamp 300
    for rel in data["data"]:
        starts_at = rel.get("starts_at")
        ends_at = rel.get("ends_at")
        
        if starts_at is not None:
            assert starts_at <= 300
        if ends_at is not None:
            assert ends_at >= 300


def test_list_relationship_types(client: TestClient, sample_relationship):
    """Test getting all unique relationship types"""
    response = client.get("/api/v1/relationships/types/list")
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert isinstance(data["data"], list)
    
    # Should include the type from our sample relationship
    assert "friends_with" in data["data"]


def test_relationship_api_field_mapping(client: TestClient, sample_entities):
    """Test that API properly maps database fields to API fields"""
    entity1_id = sample_entities[0]["id"]
    entity2_id = sample_entities[1]["id"]
    
    # Create relationship
    create_data = {
        "source_id": entity1_id,
        "target_id": entity2_id,
        "relation_type": "mapping_test",
        "weight": 0.6
    }
    
    response = client.post("/api/v1/relationships/", json=create_data)
    data = response.json()["data"]
    
    # Verify API field mapping
    assert data["subject_id"] == entity1_id  # source_id → subject_id
    assert data["object_id"] == entity2_id   # target_id → object_id
    assert data["predicate"] == "mapping_test"  # relation_type → predicate
    
    # Verify fields are consistent across endpoints
    relationship_id = data["id"]
    get_response = client.get(f"/api/v1/relationships/{relationship_id}")
    get_data = get_response.json()["data"]
    
    assert get_data["subject_id"] == data["subject_id"]
    assert get_data["object_id"] == data["object_id"]
    assert get_data["predicate"] == data["predicate"]


def test_temporal_query_edge_cases(client: TestClient, sample_entities):
    """Test temporal queries with edge cases"""
    entity1_id = sample_entities[0]["id"]
    entity2_id = sample_entities[1]["id"]
    
    # Create relationship with only start time
    client.post("/api/v1/relationships/", json={
        "source_id": entity1_id,
        "target_id": entity2_id,
        "relation_type": "ongoing",
        "starts_at": 100
        # No end time
    })
    
    # Should be active at any time >= 100
    response = client.get("/api/v1/relationships/active?time=200")
    assert response.status_code == 200
    
    # Create relationship with only end time
    client.post("/api/v1/relationships/", json={
        "source_id": entity2_id,
        "target_id": entity1_id,
        "relation_type": "historical",
        "ends_at": 300
        # No start time
    })
    
    # Should be active at any time <= 300
    response = client.get("/api/v1/relationships/active?time=200")
    assert response.status_code == 200
    
    # Create relationship with no temporal bounds
    client.post("/api/v1/relationships/", json={
        "source_id": entity1_id,
        "target_id": entity2_id,
        "relation_type": "eternal"
        # No temporal bounds
    })
    
    # Should always be active
    response = client.get("/api/v1/relationships/active?time=1000")
    assert response.status_code == 200


def test_error_handling(client: TestClient):
    """Test error handling for various invalid inputs"""
    # Test missing required fields
    response = client.post("/api/v1/relationships/", json={
        "source_id": str(uuid4())
        # Missing target_id and relation_type
    })
    assert response.status_code == 422
    
    # Test invalid UUID
    response = client.get("/api/v1/relationships/invalid-uuid")
    assert response.status_code == 422
    
    # Test active relationships without timestamp
    response = client.get("/api/v1/relationships/active")
    assert response.status_code == 422


def test_complex_temporal_workflow(client: TestClient, sample_entities):
    """Test a complex workflow with multiple temporal relationships"""
    entity1_id = sample_entities[0]["id"]
    entity2_id = sample_entities[1]["id"]
    
    # Create multiple relationships with different temporal bounds
    relationships = []
    
    # Phase 1: Strangers (no relationship)
    # Phase 2: Acquaintances (100-200)
    rel1 = client.post("/api/v1/relationships/", json={
        "source_id": entity1_id,
        "target_id": entity2_id,
        "relation_type": "acquaintances",
        "starts_at": 100,
        "ends_at": 200,
        "weight": 0.3
    }).json()["data"]
    relationships.append(rel1)
    
    # Phase 3: Friends (200-400)
    rel2 = client.post("/api/v1/relationships/", json={
        "source_id": entity1_id,
        "target_id": entity2_id,
        "relation_type": "friends",
        "starts_at": 200,
        "ends_at": 400,
        "weight": 0.7
    }).json()["data"]
    relationships.append(rel2)
    
    # Phase 4: Best friends (400+)
    rel3 = client.post("/api/v1/relationships/", json={
        "source_id": entity1_id,
        "target_id": entity2_id,
        "relation_type": "best_friends",
        "starts_at": 400,
        "weight": 0.9
    }).json()["data"]
    relationships.append(rel3)
    
    # Test different time periods
    # Time 50: No relationship
    response = client.get(f"/api/v1/relationships/between/{entity1_id}/{entity2_id}?time=50")
    assert len(response.json()["data"]) == 0
    
    # Time 150: Acquaintances
    response = client.get(f"/api/v1/relationships/between/{entity1_id}/{entity2_id}?time=150")
    data = response.json()["data"]
    assert len(data) == 1
    assert data[0]["predicate"] == "acquaintances"
    
    # Time 300: Friends
    response = client.get(f"/api/v1/relationships/between/{entity1_id}/{entity2_id}?time=300")
    data = response.json()["data"]
    assert len(data) == 1
    assert data[0]["predicate"] == "friends"
    
    # Time 500: Best friends
    response = client.get(f"/api/v1/relationships/between/{entity1_id}/{entity2_id}?time=500")
    data = response.json()["data"]
    assert len(data) == 1
    assert data[0]["predicate"] == "best_friends"
    
    # Test overlapping query
    response = client.get("/api/v1/relationships/overlapping?from=150&to=350")
    data = response.json()["data"]
    # Should get both acquaintances and friends relationships
    predicates = {rel["predicate"] for rel in data}
    assert "acquaintances" in predicates
    assert "friends" in predicates
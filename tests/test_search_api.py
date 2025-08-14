"""
Test timeline-aware search and discovery API endpoints.
Covers semantic search, entity search, knowledge search, and complex temporal queries.
"""

import pytest
from uuid import uuid4
from datetime import datetime
from fastapi.testclient import TestClient
from app.main import app
from app.services.database import get_db

client = TestClient(app)


@pytest.fixture
def setup_search_test_data():
    """Create comprehensive test data for search testing"""
    db = get_db()
    
    # Create test entities
    entities_data = [
        {"name": "Alice", "entity_type": "character", "description": "A brave adventurer with magical abilities"},
        {"name": "Bob", "entity_type": "character", "description": "A wise wizard skilled in ancient magic"},
        {"name": "Magic Castle", "entity_type": "location", "description": "An enchanted fortress floating in the clouds"},
        {"name": "Ancient Tome", "entity_type": "artifact", "description": "A mysterious book containing powerful spells"},
        {"name": "Dragon", "entity_type": "character", "description": "A mighty fire-breathing creature guarding treasure"}
    ]
    
    entities = []
    for entity_data in entities_data:
        entity_data["metadata"] = {"test": True}
        result = db.table("entities").insert(entity_data).execute()
        entities.append(result.data[0])
    
    # Create test scenes
    scenes_data = [
        {"title": "The Magic Discovery", "timestamp": 1000, "location_id": entities[2]["id"]},
        {"title": "Dragon Encounter", "timestamp": 2000, "location_id": entities[2]["id"]},
        {"title": "Ancient Wisdom", "timestamp": 3000, "location_id": entities[2]["id"]}
    ]
    
    scenes = []
    for scene_data in scenes_data:
        result = db.table("scenes").insert(scene_data).execute()
        scenes.append(result.data[0])
    
    # Create test scene blocks with content
    blocks_data = [
        {
            "scene_id": scenes[0]["id"],
            "block_type": "prose",
            "order": 1,
            "content": "Alice discovered a magical artifact in the ancient castle",
            "metadata": {}
        },
        {
            "scene_id": scenes[1]["id"],
            "block_type": "dialogue",
            "order": 1,
            "summary": "Bob warns Alice about the dragon's power",
            "lines": {"Bob": "Beware, the dragon is mighty and dangerous!"},
            "metadata": {}
        },
        {
            "scene_id": scenes[2]["id"],
            "block_type": "milestone",
            "order": 1,
            "subject_id": entities[1]["id"],  # Bob
            "verb": "teaches",
            "object_id": entities[0]["id"],  # Alice
            "metadata": {}
        }
    ]
    
    blocks = []
    for block_data in blocks_data:
        result = db.table("scene_blocks").insert(block_data).execute()
        blocks.append(result.data[0])
    
    # Create test relationships
    relationships_data = [
        {
            "subject_id": entities[0]["id"],  # Alice
            "object_id": entities[2]["id"],  # Magic Castle
            "predicate": "located_at",
            "strength": 0.9,
            "starts_at": 1000,
            "ends_at": 2500,
            "metadata": {}
        },
        {
            "subject_id": entities[1]["id"],  # Bob
            "object_id": entities[3]["id"],  # Ancient Tome
            "predicate": "possesses",
            "strength": 0.8,
            "starts_at": 500,
            "ends_at": None,  # Ongoing
            "metadata": {}
        },
        {
            "subject_id": entities[4]["id"],  # Dragon
            "object_id": entities[2]["id"],  # Magic Castle
            "predicate": "guards",
            "strength": 1.0,
            "starts_at": 0,
            "ends_at": None,  # Ongoing
            "metadata": {}
        }
    ]
    
    relationships = []
    for rel_data in relationships_data:
        result = db.table("entity_relationships").insert(rel_data).execute()
        relationships.append(result.data[0])
    
    # Create test knowledge snapshots
    knowledge_data = [
        {
            "entity_id": entities[0]["id"],  # Alice
            "timestamp": 1500,
            "knowledge": {"location": "Magic Castle", "artifact_found": "Ancient Tome", "companion": "Bob"},
            "metadata": {"confidence": 0.9}
        },
        {
            "entity_id": entities[1]["id"],  # Bob
            "timestamp": 2000,
            "knowledge": {"student": "Alice", "magic_level": "intermediate", "dragon_nearby": True},
            "metadata": {"confidence": 0.8}
        }
    ]
    
    knowledge_snapshots = []
    for knowledge in knowledge_data:
        result = db.table("knowledge_snapshots").insert(knowledge).execute()
        knowledge_snapshots.append(result.data[0])
    
    yield {
        "entities": entities,
        "scenes": scenes,
        "blocks": blocks,
        "relationships": relationships,
        "knowledge_snapshots": knowledge_snapshots
    }
    
    # Cleanup
    for item in knowledge_snapshots:
        db.table("knowledge_snapshots").delete().eq("id", item["id"]).execute()
    for item in relationships:
        db.table("entity_relationships").delete().eq("id", item["id"]).execute()
    for item in blocks:
        db.table("scene_blocks").delete().eq("id", item["id"]).execute()
    for item in scenes:
        db.table("scenes").delete().eq("id", item["id"]).execute()
    for item in entities:
        db.table("entities").delete().eq("id", item["id"]).execute()


class TestBasicSearch:
    """Test basic search functionality"""
    
    def test_search_health_check(self):
        """Test search service health check"""
        response = client.get("/api/v1/search/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] == True
        assert data["database_connected"] == True
        assert "services" in data
        assert "semantic_search" in data["services"]
        assert "text_search" in data["services"]
    
    def test_search_statistics(self, setup_search_test_data):
        """Test search statistics endpoint"""
        response = client.get("/api/v1/search/stats")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] == True
        assert "content_counts" in data["data"]
        assert "total_searchable_items" in data["data"]
        assert "searchable_score" in data["data"]
        assert "search_capabilities" in data["data"]
        
        # Should have some content from test data
        assert data["data"]["total_searchable_items"] > 0
    
    def test_semantic_search_fallback(self, setup_search_test_data):
        """Test semantic search (fallback to text search)"""
        search_request = {
            "query": "magic",
            "match_threshold": 0.7,
            "match_count": 10
        }
        
        response = client.post("/api/v1/search/semantic", json=search_request)
        assert response.status_code == 200
        
        data = response.json()
        assert data["query"] == "magic"
        assert data["search_type"] == "semantic_fallback_text"
        assert "results" in data
        assert "execution_time_ms" in data
        
        # Should find magic-related content
        if data["results"]:
            for result in data["results"]:
                assert "magic" in result["title"].lower() or "magic" in (result["content"] or "").lower()
    
    def test_text_search(self, setup_search_test_data):
        """Test full-text search"""
        search_request = {
            "query": "dragon",
            "limit": 20
        }
        
        response = client.post("/api/v1/search/text", json=search_request)
        assert response.status_code == 200
        
        data = response.json()
        assert data["query"] == "dragon"
        assert data["search_type"] == "text_search"
        assert "results" in data
        
        # Should find dragon-related content
        if data["results"]:
            for result in data["results"]:
                assert "dragon" in result["title"].lower() or "dragon" in (result["content"] or "").lower()


class TestEntitySearch:
    """Test entity search with relationship context"""
    
    def test_search_entities_basic(self, setup_search_test_data):
        """Test basic entity search"""
        search_request = {
            "query": "Alice",
            "limit": 10
        }
        
        response = client.post("/api/v1/search/entities", json=search_request)
        assert response.status_code == 200
        
        data = response.json()
        assert data["query"] == "Alice"
        assert data["search_type"] == "entity_search"
        assert len(data["results"]) >= 1
        
        # Should find Alice
        alice_found = any(
            result["title"] == "Alice" and result["content_type"] == "entity"
            for result in data["results"]
        )
        assert alice_found
    
    def test_search_entities_with_type_filter(self, setup_search_test_data):
        """Test entity search with entity type filter"""
        search_request = {
            "query": "magic",
            "entity_types": ["location"],
            "limit": 10
        }
        
        response = client.post("/api/v1/search/entities", json=search_request)
        assert response.status_code == 200
        
        data = response.json()
        assert data["search_type"] == "entity_search"
        
        # All results should be locations
        for result in data["results"]:
            assert result["metadata"]["entity_type"] == "location"
    
    def test_search_entities_with_timestamp(self, setup_search_test_data):
        """Test entity search with timestamp context"""
        search_request = {
            "query": "castle",
            "at_timestamp": 1500,
            "include_related": False,
            "limit": 10
        }
        
        response = client.post("/api/v1/search/entities", json=search_request)
        assert response.status_code == 200
        
        data = response.json()
        assert data["search_type"] == "entity_search"
        assert data["timeline_context"]["at_timestamp"] == 1500


class TestTimelineSearch:
    """Test timeline-aware story world queries"""
    
    def test_timeline_search_basic(self, setup_search_test_data):
        """Test basic timeline search"""
        search_request = {
            "at_timestamp": 1500,
            "include_relationships": True,
            "include_knowledge": True,
            "include_scenes": True
        }
        
        response = client.post("/api/v1/search/timeline", json=search_request)
        assert response.status_code == 200
        
        data = response.json()
        assert data["timestamp"] == 1500
        assert "entities" in data
        assert "relationships" in data
        assert "knowledge_snapshots" in data
        assert "active_scenes" in data
        
        # Should have entities from test data
        assert len(data["entities"]) >= 1
    
    def test_timeline_search_with_entity_filter(self, setup_search_test_data):
        """Test timeline search with specific entities"""
        test_data = setup_search_test_data
        alice_id = test_data["entities"][0]["id"]
        bob_id = test_data["entities"][1]["id"]
        
        search_request = {
            "at_timestamp": 2000,
            "entity_ids": [alice_id, bob_id],
            "include_relationships": True,
            "include_knowledge": True,
            "include_scenes": False
        }
        
        response = client.post("/api/v1/search/timeline", json=search_request)
        assert response.status_code == 200
        
        data = response.json()
        assert len(data["entities"]) == 2
        
        # Should only include specified entities
        entity_ids = [entity["id"] for entity in data["entities"]]
        assert alice_id in entity_ids
        assert bob_id in entity_ids
    
    def test_timeline_search_relationships_temporal_filter(self, setup_search_test_data):
        """Test that timeline search properly filters relationships by timestamp"""
        search_request = {
            "at_timestamp": 3000,  # After Alice leaves castle (ends_at: 2500)
            "include_relationships": True,
            "include_knowledge": False,
            "include_scenes": False
        }
        
        response = client.post("/api/v1/search/timeline", json=search_request)
        assert response.status_code == 200
        
        data = response.json()
        
        # Should not include Alice->Castle relationship (ended at 2500)
        alice_castle_relations = [
            rel for rel in data["relationships"]
            if rel["predicate"] == "located_at" and rel["subject_name"] == "Alice"
        ]
        assert len(alice_castle_relations) == 0


class TestKnowledgeSearch:
    """Test knowledge snapshot search"""
    
    def test_search_knowledge_basic(self, setup_search_test_data):
        """Test basic knowledge search"""
        search_request = {
            "query": "Magic Castle",
            "limit": 10
        }
        
        response = client.post("/api/v1/search/knowledge", json=search_request)
        assert response.status_code == 200
        
        data = response.json()
        assert data["query"] == "Magic Castle"
        assert data["search_type"] == "knowledge_search"
        assert "results" in data
        
        # Should find knowledge containing "Magic Castle"
        if data["results"]:
            for result in data["results"]:
                assert result["content_type"] == "knowledge"
                assert "Magic Castle" in result["content"]
    
    def test_search_knowledge_with_entity_filter(self, setup_search_test_data):
        """Test knowledge search with entity filter"""
        test_data = setup_search_test_data
        alice_id = test_data["entities"][0]["id"]
        
        search_request = {
            "query": "artifact",
            "entity_ids": [alice_id],
            "include_entity_context": True,
            "limit": 10
        }
        
        response = client.post("/api/v1/search/knowledge", json=search_request)
        assert response.status_code == 200
        
        data = response.json()
        assert data["search_type"] == "knowledge_search"
        
        # All results should be for Alice
        for result in data["results"]:
            assert alice_id in result["entity_ids"]
    
    def test_search_knowledge_with_timestamp_range(self, setup_search_test_data):
        """Test knowledge search with timestamp range"""
        search_request = {
            "query": "magic",
            "timestamp_range": [1000, 2000],
            "include_entity_context": False,
            "limit": 10
        }
        
        response = client.post("/api/v1/search/knowledge", json=search_request)
        assert response.status_code == 200
        
        data = response.json()
        assert data["search_type"] == "knowledge_search"
        
        # All results should be within timestamp range
        for result in data["results"]:
            if result["timestamp"] is not None:
                assert 1000 <= result["timestamp"] <= 2000


class TestComplexQueries:
    """Test complex multi-entity temporal queries"""
    
    def test_complex_query_basic(self, setup_search_test_data):
        """Test basic complex query"""
        test_data = setup_search_test_data
        alice_id = test_data["entities"][0]["id"]
        bob_id = test_data["entities"][1]["id"]
        
        query_request = {
            "entities": [alice_id, bob_id],
            "at_timestamp": 1500,
            "include_relationships": True,
            "include_knowledge": True,
            "include_scenes": True,
            "relationship_depth": 1
        }
        
        response = client.post("/api/v1/search/complex", json=query_request)
        assert response.status_code == 200
        
        data = response.json()
        assert data["search_type"] == "complex_query"
        assert "results" in data
        assert "timeline_context" in data
        
        # Should include both base entities
        base_entities = [
            result for result in data["results"]
            if result["content_type"] == "entity" and result["metadata"].get("is_base_entity")
        ]
        assert len(base_entities) == 2
    
    def test_complex_query_with_relationships(self, setup_search_test_data):
        """Test complex query including relationships"""
        test_data = setup_search_test_data
        alice_id = test_data["entities"][0]["id"]
        castle_id = test_data["entities"][2]["id"]
        
        query_request = {
            "entities": [alice_id, castle_id],
            "at_timestamp": 1200,  # When Alice is at castle
            "include_relationships": True,
            "include_knowledge": False,
            "include_scenes": False,
            "relationship_depth": 1
        }
        
        response = client.post("/api/v1/search/complex", json=query_request)
        assert response.status_code == 200
        
        data = response.json()
        
        # Should include relationship results
        relationship_results = [
            result for result in data["results"]
            if result["content_type"] == "relationship"
        ]
        
        if relationship_results:
            # Check timeline context
            assert data["timeline_context"]["relationships_count"] >= 1
            assert data["timeline_context"]["at_timestamp"] == 1200


class TestSearchUtilities:
    """Test search utility endpoints"""
    
    def test_get_search_predicates(self, setup_search_test_data):
        """Test getting unique relationship predicates for search filtering"""
        response = client.get("/api/v1/search/predicates")
        assert response.status_code == 200
        
        predicates = response.json()
        assert isinstance(predicates, list)
        
        # Should include predicates from test data
        expected_predicates = ["located_at", "possesses", "guards"]
        for predicate in expected_predicates:
            assert predicate in predicates
    
    def test_get_entity_types(self, setup_search_test_data):
        """Test getting unique entity types for search filtering"""
        response = client.get("/api/v1/search/entity-types")
        assert response.status_code == 200
        
        entity_types = response.json()
        assert isinstance(entity_types, list)
        
        # Should include entity types from test data
        expected_types = ["character", "location", "artifact"]
        for entity_type in expected_types:
            assert entity_type in entity_types


class TestSearchPerformance:
    """Test search performance and response times"""
    
    def test_search_response_times(self, setup_search_test_data):
        """Test that searches complete within reasonable time limits"""
        search_requests = [
            ("semantic", {"query": "magic", "match_count": 10}),
            ("text", {"query": "dragon", "limit": 20}),
            ("entities", {"query": "Alice", "limit": 10}),
            ("knowledge", {"query": "castle", "limit": 10})
        ]
        
        for endpoint, request_data in search_requests:
            response = client.post(f"/api/v1/search/{endpoint}", json=request_data)
            assert response.status_code == 200
            
            data = response.json()
            if "execution_time_ms" in data:
                # Should complete within 2 seconds (2000ms) for test data
                assert data["execution_time_ms"] < 2000
    
    def test_timeline_search_performance(self, setup_search_test_data):
        """Test timeline search performance"""
        search_request = {
            "at_timestamp": 1500,
            "include_relationships": True,
            "include_knowledge": True,
            "include_scenes": True
        }
        
        import time
        start_time = time.time()
        
        response = client.post("/api/v1/search/timeline", json=search_request)
        
        end_time = time.time()
        execution_time = (end_time - start_time) * 1000
        
        assert response.status_code == 200
        # Timeline search should complete within 3 seconds for test data
        assert execution_time < 3000
    
    def test_complex_query_performance(self, setup_search_test_data):
        """Test complex query performance"""
        test_data = setup_search_test_data
        alice_id = test_data["entities"][0]["id"]
        bob_id = test_data["entities"][1]["id"]
        castle_id = test_data["entities"][2]["id"]
        
        query_request = {
            "entities": [alice_id, bob_id, castle_id],
            "at_timestamp": 1500,
            "include_relationships": True,
            "include_knowledge": True,
            "include_scenes": True,
            "relationship_depth": 2
        }
        
        response = client.post("/api/v1/search/complex", json=query_request)
        assert response.status_code == 200
        
        data = response.json()
        if "timeline_context" in data and "execution_time_ms" in data["timeline_context"]:
            # Complex queries should complete within 5 seconds for test data
            assert data["timeline_context"]["execution_time_ms"] < 5000


class TestSearchErrorHandling:
    """Test error handling in search endpoints"""
    
    def test_search_with_invalid_data(self):
        """Test search endpoints with invalid request data"""
        # Test invalid semantic search
        invalid_requests = [
            ("/api/v1/search/semantic", {"query": ""}),  # Empty query
            ("/api/v1/search/entities", {"query": "test", "limit": -1}),  # Invalid limit
            ("/api/v1/search/timeline", {"at_timestamp": "invalid"}),  # Invalid timestamp
            ("/api/v1/search/knowledge", {"timestamp_range": [2000, 1000]})  # Invalid range
        ]
        
        for endpoint, request_data in invalid_requests:
            response = client.post(endpoint, json=request_data)
            # Should return validation error (422) or handle gracefully (200 with empty results)
            assert response.status_code in [200, 422]
    
    def test_search_with_nonexistent_entities(self, setup_search_test_data):
        """Test search with nonexistent entity IDs"""
        fake_uuid = "00000000-0000-0000-0000-000000000000"
        
        # Timeline search with nonexistent entity
        search_request = {
            "at_timestamp": 1500,
            "entity_ids": [fake_uuid],
            "include_relationships": True,
            "include_knowledge": True,
            "include_scenes": False
        }
        
        response = client.post("/api/v1/search/timeline", json=search_request)
        assert response.status_code == 200
        
        data = response.json()
        # Should return empty or minimal results
        assert len(data["entities"]) == 0
        
        # Complex query with nonexistent entities
        query_request = {
            "entities": [fake_uuid],
            "include_relationships": True,
            "include_knowledge": True,
            "include_scenes": True
        }
        
        response = client.post("/api/v1/search/complex", json=query_request)
        assert response.status_code == 200
        
        data = response.json()
        # Should handle gracefully
        assert len(data["results"]) == 0
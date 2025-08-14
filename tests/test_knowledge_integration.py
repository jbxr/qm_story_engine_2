"""
Integration tests for knowledge snapshot system with other components
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.services.database import get_db

client = TestClient(app)


class TestKnowledgeIntegration:
    """Test integration of knowledge system with other components"""

    def test_health_endpoint_includes_knowledge_count(self):
        """Test that health endpoint includes knowledge snapshot count"""
        response = client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["status"] == "healthy"
        assert data["database"] == "connected"
        assert "entity_count" in data
        assert "knowledge_snapshot_count" in data
        assert isinstance(data["knowledge_snapshot_count"], int)

    def test_knowledge_routes_in_docs(self):
        """Test that knowledge routes appear in OpenAPI docs"""
        response = client.get("/docs")
        assert response.status_code == 200
        
        # Test that OpenAPI spec includes knowledge endpoints
        openapi_response = client.get("/openapi.json")
        assert openapi_response.status_code == 200
        
        openapi_data = openapi_response.json()
        paths = openapi_data.get("paths", {})
        
        # Check that knowledge snapshot endpoints are documented
        knowledge_paths = [path for path in paths.keys() if "/knowledge/" in path]
        assert len(knowledge_paths) >= 4  # Should have at least 4 unique knowledge endpoint paths
        
        # Check specific endpoints exist
        expected_paths = [
            "/api/v1/knowledge/snapshots",
            "/api/v1/knowledge/snapshots/{snapshot_id}",
            "/api/v1/knowledge/snapshots/character/{character_id}",
            "/api/v1/knowledge/snapshots/scene/{scene_id}"
        ]
        
        for expected_path in expected_paths:
            assert expected_path in paths, f"Expected path {expected_path} not found in OpenAPI spec"

    def test_knowledge_api_tags(self):
        """Test that knowledge endpoints are properly tagged"""
        openapi_response = client.get("/openapi.json")
        openapi_data = openapi_response.json()
        
        # Check that knowledge tag exists
        tags = openapi_data.get("tags", [])
        knowledge_tag_found = any(tag.get("name") == "knowledge" for tag in tags)
        
        # If not in tags list, check paths have knowledge tag
        if not knowledge_tag_found:
            paths = openapi_data.get("paths", {})
            for path, methods in paths.items():
                if "/knowledge/" in path:
                    for method, details in methods.items():
                        if isinstance(details, dict):
                            tags = details.get("tags", [])
                            assert "knowledge" in tags, f"Knowledge endpoint {path} missing 'knowledge' tag"

    def test_server_startup_with_knowledge_routes(self):
        """Test that server starts properly with knowledge routes"""
        # This test verifies the server can start and serve requests
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert data["message"] == "QuantumMateria Story Engine API"
        assert data["status"] == "running"


class TestKnowledgeSystemComplete:
    """End-to-end tests for complete knowledge snapshot functionality"""

    def setup_method(self):
        """Setup test data"""
        self.db = get_db()
        
        # Create test character
        character_data = {
            "name": "End-to-End Test Character",
            "entity_type": "character"
        }
        result = self.db.table("entities").insert(character_data).execute()
        self.character_id = result.data[0]["id"]
        
        # Create test scene with timestamp
        scene_data = {
            "title": "End-to-End Test Scene",
            "timestamp": 5000
        }
        result = self.db.table("scenes").insert(scene_data).execute()
        self.scene_id = result.data[0]["id"]

    def teardown_method(self):
        """Clean up test data"""
        try:
            self.db.table("knowledge_snapshots").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
            self.db.table("scenes").delete().eq("id", self.scene_id).execute()
            self.db.table("entities").delete().eq("id", self.character_id).execute()
        except Exception:
            pass

    def test_complete_knowledge_workflow(self):
        """Test complete workflow: create character → create scene → add knowledge → query knowledge"""
        
        # Step 1: Verify character exists
        response = client.get(f"/api/v1/entities/{self.character_id}")
        assert response.status_code == 200
        character = response.json()["data"]["entity"]
        assert character["name"] == "End-to-End Test Character"
        
        # Step 2: Verify scene exists
        response = client.get(f"/api/v1/scenes/{self.scene_id}")
        assert response.status_code == 200
        scene = response.json()["data"]["scene"]
        assert scene["title"] == "End-to-End Test Scene"
        assert scene["timestamp"] == 5000
        
        # Step 3: Create knowledge snapshot linked to scene timestamp
        snapshot_data = {
            "entity_id": self.character_id,
            "timestamp": 5000,  # Same as scene
            "knowledge": {
                "discovered_secret": "The ancient artifact is hidden in the tower",
                "trust_level_alice": 85,
                "knows_password": True,
                "relationships": {
                    "allies": ["Alice", "Bob"],
                    "enemies": ["Dark Lord"]
                }
            },
            "metadata": {
                "source_scene_id": self.scene_id,
                "event_type": "revelation",
                "importance": "high"
            }
        }
        
        response = client.post("/api/v1/knowledge/snapshots", json=snapshot_data)
        assert response.status_code == 200
        created_snapshot = response.json()["data"]["snapshot"]
        snapshot_id = created_snapshot["id"]
        
        # Step 4: Retrieve snapshot and verify all data
        response = client.get(f"/api/v1/knowledge/snapshots/{snapshot_id}")
        assert response.status_code == 200
        
        snapshot = response.json()["data"]["snapshot"]
        assert snapshot["entity_id"] == self.character_id
        assert snapshot["timestamp"] == 5000
        assert snapshot["knowledge"]["discovered_secret"] == "The ancient artifact is hidden in the tower"
        assert snapshot["knowledge"]["trust_level_alice"] == 85
        assert snapshot["knowledge"]["relationships"]["allies"] == ["Alice", "Bob"]
        assert snapshot["metadata"]["source_scene_id"] == self.scene_id
        assert snapshot["entity_name"] == "End-to-End Test Character"
        
        # Step 5: Query character's knowledge timeline
        response = client.get(f"/api/v1/knowledge/snapshots/character/{self.character_id}")
        assert response.status_code == 200
        
        snapshots = response.json()["data"]["snapshots"]
        assert len(snapshots) == 1
        assert snapshots[0]["id"] == snapshot_id
        
        # Step 6: Query scene's knowledge state
        response = client.get(f"/api/v1/knowledge/snapshots/scene/{self.scene_id}")
        assert response.status_code == 200
        
        scene_snapshots = response.json()["data"]["snapshots"]
        assert len(scene_snapshots) == 1
        assert scene_snapshots[0]["id"] == snapshot_id
        
        # Step 7: Update knowledge with new information
        update_data = {
            "knowledge": {
                "discovered_secret": "The ancient artifact is hidden in the tower",
                "trust_level_alice": 90,  # Updated trust level
                "knows_password": True,
                "learned_spell": "Fireball",  # New knowledge
                "relationships": {
                    "allies": ["Alice", "Bob", "Carol"],  # Added new ally
                    "enemies": ["Dark Lord"]
                }
            },
            "metadata": {
                "source_scene_id": self.scene_id,
                "event_type": "revelation",
                "importance": "high",
                "last_updated": "after_dialogue_with_alice"
            }
        }
        
        response = client.put(f"/api/v1/knowledge/snapshots/{snapshot_id}", json=update_data)
        assert response.status_code == 200
        
        updated_snapshot = response.json()["data"]["snapshot"]
        assert updated_snapshot["knowledge"]["trust_level_alice"] == 90
        assert updated_snapshot["knowledge"]["learned_spell"] == "Fireball"
        assert "Carol" in updated_snapshot["knowledge"]["relationships"]["allies"]
        assert updated_snapshot["metadata"]["last_updated"] == "after_dialogue_with_alice"
        
        # Step 8: Verify the update persisted
        response = client.get(f"/api/v1/knowledge/snapshots/{snapshot_id}")
        assert response.status_code == 200
        
        final_snapshot = response.json()["data"]["snapshot"]
        assert final_snapshot["knowledge"]["trust_level_alice"] == 90
        assert final_snapshot["knowledge"]["learned_spell"] == "Fireball"

    def test_temporal_knowledge_queries(self):
        """Test temporal queries across multiple timestamps"""
        
        # Create knowledge snapshots at different timestamps
        timestamps_and_knowledge = [
            (1000, {"knows_secret": False, "trust_alice": 50}),
            (3000, {"knows_secret": True, "trust_alice": 75, "has_key": True}),
            (5000, {"knows_secret": True, "trust_alice": 90, "has_key": True, "learned_magic": True})
        ]
        
        snapshot_ids = []
        for timestamp, knowledge in timestamps_and_knowledge:
            snapshot_data = {
                "entity_id": self.character_id,
                "timestamp": timestamp,
                "knowledge": knowledge
            }
            
            response = client.post("/api/v1/knowledge/snapshots", json=snapshot_data)
            assert response.status_code == 200
            snapshot_ids.append(response.json()["data"]["snapshot"]["id"])
        
        # Query all snapshots for character (should be ordered by timestamp desc)
        response = client.get(f"/api/v1/knowledge/snapshots/character/{self.character_id}")
        assert response.status_code == 200
        
        all_snapshots = response.json()["data"]["snapshots"]
        assert len(all_snapshots) == 3
        
        # Should be ordered by timestamp descending
        assert all_snapshots[0]["timestamp"] == 5000
        assert all_snapshots[1]["timestamp"] == 3000
        assert all_snapshots[2]["timestamp"] == 1000
        
        # Verify knowledge evolution
        assert all_snapshots[2]["knowledge"]["knows_secret"] is False  # timestamp 1000
        assert all_snapshots[1]["knowledge"]["knows_secret"] is True   # timestamp 3000
        assert all_snapshots[0]["knowledge"]["learned_magic"] is True  # timestamp 5000
        
        # Query specific timestamp
        response = client.get(f"/api/v1/knowledge/snapshots/character/{self.character_id}?timestamp=3000")
        assert response.status_code == 200
        
        specific_snapshots = response.json()["data"]["snapshots"]
        assert len(specific_snapshots) == 1
        assert specific_snapshots[0]["timestamp"] == 3000
        assert specific_snapshots[0]["knowledge"]["has_key"] is True
        assert "learned_magic" not in specific_snapshots[0]["knowledge"]
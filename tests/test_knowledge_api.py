"""
Comprehensive test suite for knowledge snapshot API endpoints
Following Phase 2 testing patterns
"""
import pytest
from fastapi.testclient import TestClient
from uuid import uuid4
import json

from app.main import app
from app.services.database import get_db

client = TestClient(app)


class TestKnowledgeSnapshots:
    """Test suite for knowledge snapshot operations"""

    def setup_method(self):
        """Setup test data before each test"""
        self.db = get_db()
        
        # Create test character
        character_data = {
            "name": "Test Character",
            "entity_type": "character",
            "description": "Character for knowledge testing"
        }
        
        result = self.db.table("entities").insert(character_data).execute()
        self.character_id = result.data[0]["id"]
        
        # Create test scene
        scene_data = {
            "title": "Test Scene",
            "timestamp": 1000
        }
        
        result = self.db.table("scenes").insert(scene_data).execute()
        self.scene_id = result.data[0]["id"]

    def teardown_method(self):
        """Clean up test data after each test"""
        try:
            # Clean up knowledge snapshots
            self.db.table("knowledge_snapshots").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
            
            # Clean up entities and scenes
            self.db.table("entities").delete().eq("id", self.character_id).execute()
            self.db.table("scenes").delete().eq("id", self.scene_id).execute()
        except Exception:
            pass  # Ignore cleanup errors

    def test_create_knowledge_snapshot(self):
        """Test creating a knowledge snapshot"""
        snapshot_data = {
            "entity_id": self.character_id,
            "timestamp": 1000,
            "knowledge": {
                "knows_secret": True,
                "location_of_artifact": "hidden chamber",
                "trust_level": 85
            },
            "metadata": {
                "source": "test",
                "confidence": "high"
            }
        }
        
        response = client.post("/api/v1/knowledge/snapshots", json=snapshot_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "snapshot" in data["data"]
        
        snapshot = data["data"]["snapshot"]
        assert snapshot["entity_id"] == self.character_id
        assert snapshot["timestamp"] == 1000
        assert snapshot["knowledge"]["knows_secret"] is True
        assert snapshot["knowledge"]["location_of_artifact"] == "hidden chamber"
        assert snapshot["metadata"]["source"] == "test"

    def test_get_knowledge_snapshot(self):
        """Test retrieving a specific knowledge snapshot"""
        # First create a snapshot
        snapshot_data = {
            "entity_id": self.character_id,
            "timestamp": 1001,
            "knowledge": {"test_fact": "test_value"}
        }
        
        create_response = client.post("/api/v1/knowledge/snapshots", json=snapshot_data)
        created_snapshot = create_response.json()["data"]["snapshot"]
        snapshot_id = created_snapshot["id"]
        
        # Now retrieve it
        response = client.get(f"/api/v1/knowledge/snapshots/{snapshot_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "snapshot" in data["data"]
        
        snapshot = data["data"]["snapshot"]
        assert snapshot["id"] == snapshot_id
        assert snapshot["entity_id"] == self.character_id
        assert snapshot["timestamp"] == 1001
        assert snapshot["knowledge"]["test_fact"] == "test_value"

    def test_get_nonexistent_snapshot(self):
        """Test retrieving a non-existent snapshot"""
        fake_id = str(uuid4())
        response = client.get(f"/api/v1/knowledge/snapshots/{fake_id}")
        
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False

    def test_get_character_knowledge_snapshots(self):
        """Test retrieving knowledge snapshots for a character"""
        # Create multiple snapshots for the character
        snapshots_data = [
            {
                "entity_id": self.character_id,
                "timestamp": 1000,
                "knowledge": {"fact1": "value1"}
            },
            {
                "entity_id": self.character_id,
                "timestamp": 1500,
                "knowledge": {"fact2": "value2"}
            },
            {
                "entity_id": self.character_id,
                "timestamp": 2000,
                "knowledge": {"fact3": "value3"}
            }
        ]
        
        for snapshot_data in snapshots_data:
            client.post("/api/v1/knowledge/snapshots", json=snapshot_data)
        
        # Retrieve all snapshots for character
        response = client.get(f"/api/v1/knowledge/snapshots/character/{self.character_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "snapshots" in data["data"]
        
        snapshots = data["data"]["snapshots"]
        assert len(snapshots) == 3
        
        # Should be ordered by timestamp descending
        assert snapshots[0]["timestamp"] == 2000
        assert snapshots[1]["timestamp"] == 1500
        assert snapshots[2]["timestamp"] == 1000

    def test_get_character_knowledge_snapshots_with_timestamp_filter(self):
        """Test retrieving knowledge snapshots for a character with timestamp filter"""
        # Create snapshots with different timestamps
        snapshots_data = [
            {
                "entity_id": self.character_id,
                "timestamp": 1000,
                "knowledge": {"fact1": "value1"}
            },
            {
                "entity_id": self.character_id,
                "timestamp": 1500,
                "knowledge": {"fact2": "value2"}
            }
        ]
        
        for snapshot_data in snapshots_data:
            client.post("/api/v1/knowledge/snapshots", json=snapshot_data)
        
        # Filter by specific timestamp
        response = client.get(f"/api/v1/knowledge/snapshots/character/{self.character_id}?timestamp=1000")
        
        assert response.status_code == 200
        data = response.json()
        snapshots = data["data"]["snapshots"]
        
        # Should only return snapshot with timestamp 1000
        assert len(snapshots) == 1
        assert snapshots[0]["timestamp"] == 1000

    def test_get_scene_knowledge_snapshots(self):
        """Test retrieving knowledge snapshots linked to a scene"""
        # Create snapshot with scene's timestamp
        snapshot_data = {
            "entity_id": self.character_id,
            "timestamp": 1000,  # Same as scene timestamp
            "knowledge": {"scene_knowledge": "scene_value"}
        }
        
        client.post("/api/v1/knowledge/snapshots", json=snapshot_data)
        
        # Retrieve snapshots for scene
        response = client.get(f"/api/v1/knowledge/snapshots/scene/{self.scene_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        snapshots = data["data"]["snapshots"]
        assert len(snapshots) == 1
        assert snapshots[0]["timestamp"] == 1000
        assert snapshots[0]["knowledge"]["scene_knowledge"] == "scene_value"

    def test_get_scene_knowledge_snapshots_with_character_filter(self):
        """Test retrieving scene knowledge snapshots filtered by character"""
        # Create another character
        other_character_data = {
            "name": "Other Character",
            "entity_type": "character"
        }
        result = self.db.table("entities").insert(other_character_data).execute()
        other_character_id = result.data[0]["id"]
        
        try:
            # Create snapshots for both characters at scene timestamp
            snapshots_data = [
                {
                    "entity_id": self.character_id,
                    "timestamp": 1000,
                    "knowledge": {"character1_knowledge": "value1"}
                },
                {
                    "entity_id": other_character_id,
                    "timestamp": 1000,
                    "knowledge": {"character2_knowledge": "value2"}
                }
            ]
            
            for snapshot_data in snapshots_data:
                client.post("/api/v1/knowledge/snapshots", json=snapshot_data)
            
            # Filter by specific character
            response = client.get(f"/api/v1/knowledge/snapshots/scene/{self.scene_id}?character_id={self.character_id}")
            
            assert response.status_code == 200
            data = response.json()
            snapshots = data["data"]["snapshots"]
            
            # Should only return snapshot for the specified character
            assert len(snapshots) == 1
            assert snapshots[0]["entity_id"] == self.character_id
            
        finally:
            # Clean up knowledge snapshots first, then other character
            self.db.table("knowledge_snapshots").delete().eq("entity_id", other_character_id).execute()
            self.db.table("entities").delete().eq("id", other_character_id).execute()

    def test_update_knowledge_snapshot(self):
        """Test updating a knowledge snapshot"""
        # Create snapshot
        snapshot_data = {
            "entity_id": self.character_id,
            "timestamp": 1000,
            "knowledge": {"original_fact": "original_value"}
        }
        
        create_response = client.post("/api/v1/knowledge/snapshots", json=snapshot_data)
        snapshot_id = create_response.json()["data"]["snapshot"]["id"]
        
        # Update snapshot
        update_data = {
            "timestamp": 1500,
            "knowledge": {
                "original_fact": "updated_value",
                "new_fact": "new_value"
            },
            "metadata": {"updated": True}
        }
        
        response = client.put(f"/api/v1/knowledge/snapshots/{snapshot_id}", json=update_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        snapshot = data["data"]["snapshot"]
        assert snapshot["timestamp"] == 1500
        assert snapshot["knowledge"]["original_fact"] == "updated_value"
        assert snapshot["knowledge"]["new_fact"] == "new_value"
        assert snapshot["metadata"]["updated"] is True

    def test_update_nonexistent_snapshot(self):
        """Test updating a non-existent snapshot"""
        fake_id = str(uuid4())
        update_data = {"knowledge": {"test": "value"}}
        
        response = client.put(f"/api/v1/knowledge/snapshots/{fake_id}", json=update_data)
        
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False

    def test_delete_knowledge_snapshot(self):
        """Test deleting a knowledge snapshot"""
        # Create snapshot
        snapshot_data = {
            "entity_id": self.character_id,
            "timestamp": 1000,
            "knowledge": {"to_delete": "value"}
        }
        
        create_response = client.post("/api/v1/knowledge/snapshots", json=snapshot_data)
        snapshot_id = create_response.json()["data"]["snapshot"]["id"]
        
        # Delete snapshot
        response = client.delete(f"/api/v1/knowledge/snapshots/{snapshot_id}")
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        # Verify it's deleted
        get_response = client.get(f"/api/v1/knowledge/snapshots/{snapshot_id}")
        assert get_response.status_code == 404

    def test_delete_nonexistent_snapshot(self):
        """Test deleting a non-existent snapshot"""
        fake_id = str(uuid4())
        response = client.delete(f"/api/v1/knowledge/snapshots/{fake_id}")
        
        assert response.status_code == 404
        data = response.json()
        assert data["success"] is False

    def test_create_snapshot_without_timestamp(self):
        """Test creating a snapshot without timestamp (should work)"""
        snapshot_data = {
            "entity_id": self.character_id,
            "knowledge": {"timeless_fact": "timeless_value"}
        }
        
        response = client.post("/api/v1/knowledge/snapshots", json=snapshot_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        snapshot = data["data"]["snapshot"]
        # Should allow null timestamp
        assert snapshot["knowledge"]["timeless_fact"] == "timeless_value"

    def test_knowledge_snapshot_validation(self):
        """Test validation of knowledge snapshot data"""
        # Test with invalid entity_id
        invalid_data = {
            "entity_id": "invalid-uuid",
            "knowledge": {"test": "value"}
        }
        
        response = client.post("/api/v1/knowledge/snapshots", json=invalid_data)
        assert response.status_code == 422  # Validation error

    def test_empty_knowledge_object(self):
        """Test creating snapshot with empty knowledge object"""
        snapshot_data = {
            "entity_id": self.character_id,
            "timestamp": 1000,
            "knowledge": {}
        }
        
        response = client.post("/api/v1/knowledge/snapshots", json=snapshot_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        
        snapshot = data["data"]["snapshot"]
        assert snapshot["knowledge"] == {}


class TestKnowledgeSnapshotIntegration:
    """Integration tests for knowledge snapshots with other systems"""

    def setup_method(self):
        """Setup test data"""
        self.db = get_db()
        
        # Create test character
        character_data = {
            "name": "Integration Test Character",
            "entity_type": "character"
        }
        result = self.db.table("entities").insert(character_data).execute()
        self.character_id = result.data[0]["id"]

    def teardown_method(self):
        """Clean up test data"""
        try:
            self.db.table("knowledge_snapshots").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
            self.db.table("entities").delete().eq("id", self.character_id).execute()
        except Exception:
            pass

    def test_knowledge_snapshot_with_character_name_resolution(self):
        """Test that snapshots include resolved character names"""
        snapshot_data = {
            "entity_id": self.character_id,
            "timestamp": 1000,
            "knowledge": {"test_fact": "test_value"}
        }
        
        create_response = client.post("/api/v1/knowledge/snapshots", json=snapshot_data)
        snapshot_id = create_response.json()["data"]["snapshot"]["id"]
        
        # Retrieve snapshot
        response = client.get(f"/api/v1/knowledge/snapshots/{snapshot_id}")
        
        assert response.status_code == 200
        data = response.json()
        snapshot = data["data"]["snapshot"]
        
        # Should include resolved entity name
        assert snapshot.get("entity_name") == "Integration Test Character"

    def test_multiple_snapshots_ordering(self):
        """Test that multiple snapshots are properly ordered by timestamp"""
        # Create snapshots in random order
        timestamps = [3000, 1000, 2000, 1500, 2500]
        
        for i, timestamp in enumerate(timestamps):
            snapshot_data = {
                "entity_id": self.character_id,
                "timestamp": timestamp,
                "knowledge": {f"fact_{i}": f"value_{i}"}
            }
            client.post("/api/v1/knowledge/snapshots", json=snapshot_data)
        
        # Retrieve all snapshots
        response = client.get(f"/api/v1/knowledge/snapshots/character/{self.character_id}")
        
        assert response.status_code == 200
        data = response.json()
        snapshots = data["data"]["snapshots"]
        
        # Should be ordered by timestamp descending
        assert len(snapshots) == 5
        timestamps_returned = [s["timestamp"] for s in snapshots]
        assert timestamps_returned == [3000, 2500, 2000, 1500, 1000]
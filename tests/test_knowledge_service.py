"""
Test suite for knowledge service business logic
Testing temporal knowledge computation and advanced features
"""
import pytest
from uuid import uuid4

from app.services.knowledge_service import KnowledgeService
from app.services.database import get_db
from app.models.api_models import KnowledgeSnapshotCreate, KnowledgeSnapshotUpdate


class TestKnowledgeService:
    """Test suite for KnowledgeService business logic"""

    def setup_method(self):
        """Setup test data before each test"""
        self.db = get_db()
        self.service = KnowledgeService()
        
        # Create test character
        character_data = {
            "name": "Test Character",
            "entity_type": "character",
            "description": "Character for service testing"
        }
        result = self.db.table("entities").insert(character_data).execute()
        self.character_id = result.data[0]["id"]
        
        # Create test scene
        scene_data = {
            "title": "Test Scene",
            "timestamp": 2000
        }
        result = self.db.table("scenes").insert(scene_data).execute()
        self.scene_id = result.data[0]["id"]

    def teardown_method(self):
        """Clean up test data after each test"""
        try:
            # Clean up in reverse order due to foreign keys
            self.db.table("knowledge_snapshots").delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
            self.db.table("scenes").delete().eq("id", self.scene_id).execute()
            self.db.table("entities").delete().eq("id", self.character_id).execute()
        except Exception:
            pass  # Ignore cleanup errors

    def test_create_knowledge_snapshot(self):
        """Test creating a knowledge snapshot via service"""
        snapshot_data = KnowledgeSnapshotCreate(
            entity_id=self.character_id,
            timestamp=1000,
            knowledge={"knows_location": True, "trust_level": 75},
            metadata={"source": "dialogue", "confidence": "high"}
        )
        
        result = self.service.create_knowledge_snapshot(snapshot_data)
        
        assert result is not None
        assert result["entity_id"] == str(self.character_id)
        assert result["timestamp"] == 1000
        assert result["knowledge"]["knows_location"] is True
        assert result["knowledge"]["trust_level"] == 75
        assert result["metadata"]["source"] == "dialogue"

    def test_get_knowledge_snapshot(self):
        """Test retrieving a knowledge snapshot by ID"""
        # Create snapshot first
        snapshot_data = KnowledgeSnapshotCreate(
            entity_id=self.character_id,
            timestamp=1500,
            knowledge={"secret_revealed": True}
        )
        created = self.service.create_knowledge_snapshot(snapshot_data)
        snapshot_id = created["id"]
        
        # Retrieve it
        result = self.service.get_knowledge_snapshot(snapshot_id)
        
        assert result is not None
        assert result["id"] == snapshot_id
        assert result["entity_id"] == str(self.character_id)
        assert result["timestamp"] == 1500
        assert result["knowledge"]["secret_revealed"] is True
        
        # Should include entity name
        assert result.get("entity_name") == "Test Character"

    def test_get_nonexistent_snapshot(self):
        """Test retrieving a non-existent snapshot"""
        fake_id = str(uuid4())
        result = self.service.get_knowledge_snapshot(fake_id)
        assert result is None

    def test_get_character_knowledge_snapshots(self):
        """Test retrieving all snapshots for a character"""
        # Create multiple snapshots
        snapshots_data = [
            KnowledgeSnapshotCreate(
                entity_id=self.character_id,
                timestamp=1000,
                knowledge={"fact1": "value1"}
            ),
            KnowledgeSnapshotCreate(
                entity_id=self.character_id,
                timestamp=2000,
                knowledge={"fact2": "value2"}
            ),
            KnowledgeSnapshotCreate(
                entity_id=self.character_id,
                timestamp=1500,
                knowledge={"fact3": "value3"}
            )
        ]
        
        for snapshot_data in snapshots_data:
            self.service.create_knowledge_snapshot(snapshot_data)
        
        # Retrieve all snapshots
        result = self.service.get_character_knowledge_snapshots(str(self.character_id))
        
        assert len(result) == 3
        
        # Should be ordered by timestamp descending
        assert result[0]["timestamp"] == 2000
        assert result[1]["timestamp"] == 1500
        assert result[2]["timestamp"] == 1000
        
        # All should have entity name
        for snapshot in result:
            assert snapshot.get("entity_name") == "Test Character"

    def test_get_character_knowledge_snapshots_with_timestamp_filter(self):
        """Test retrieving snapshots with timestamp filter"""
        # Create snapshots with different timestamps
        timestamps = [1000, 1500, 2000]
        for timestamp in timestamps:
            snapshot_data = KnowledgeSnapshotCreate(
                entity_id=self.character_id,
                timestamp=timestamp,
                knowledge={f"fact_{timestamp}": f"value_{timestamp}"}
            )
            self.service.create_knowledge_snapshot(snapshot_data)
        
        # Filter by specific timestamp
        result = self.service.get_character_knowledge_snapshots(
            str(self.character_id), 
            timestamp=1500
        )
        
        assert len(result) == 1
        assert result[0]["timestamp"] == 1500

    def test_get_scene_knowledge_snapshots(self):
        """Test retrieving snapshots linked to a scene"""
        # Create snapshot with scene's timestamp
        snapshot_data = KnowledgeSnapshotCreate(
            entity_id=self.character_id,
            timestamp=2000,  # Same as scene timestamp
            knowledge={"scene_knowledge": "scene_value"}
        )
        self.service.create_knowledge_snapshot(snapshot_data)
        
        # Retrieve snapshots for scene
        result = self.service.get_scene_knowledge_snapshots(str(self.scene_id))
        
        assert len(result) == 1
        assert result[0]["timestamp"] == 2000
        assert result[0]["knowledge"]["scene_knowledge"] == "scene_value"

    def test_get_scene_knowledge_snapshots_with_character_filter(self):
        """Test retrieving scene snapshots filtered by character"""
        # Create another character
        other_character_data = {
            "name": "Other Character",
            "entity_type": "character"
        }
        result = self.db.table("entities").insert(other_character_data).execute()
        other_character_id = result.data[0]["id"]
        
        try:
            # Create snapshots for both characters at scene timestamp
            snapshot1 = KnowledgeSnapshotCreate(
                entity_id=self.character_id,
                timestamp=2000,
                knowledge={"character1_knowledge": "value1"}
            )
            snapshot2 = KnowledgeSnapshotCreate(
                entity_id=other_character_id,
                timestamp=2000,
                knowledge={"character2_knowledge": "value2"}
            )
            
            self.service.create_knowledge_snapshot(snapshot1)
            self.service.create_knowledge_snapshot(snapshot2)
            
            # Filter by specific character
            result = self.service.get_scene_knowledge_snapshots(
                str(self.scene_id), 
                str(self.character_id)
            )
            
            assert len(result) == 1
            assert result[0]["entity_id"] == str(self.character_id)
            
        finally:
            # Clean up knowledge snapshots first, then other character
            self.db.table("knowledge_snapshots").delete().eq("entity_id", other_character_id).execute()
            self.db.table("entities").delete().eq("id", other_character_id).execute()

    def test_update_knowledge_snapshot(self):
        """Test updating a knowledge snapshot"""
        # Create snapshot
        snapshot_data = KnowledgeSnapshotCreate(
            entity_id=self.character_id,
            timestamp=1000,
            knowledge={"original": "value"},
            metadata={"version": 1}
        )
        created = self.service.create_knowledge_snapshot(snapshot_data)
        snapshot_id = created["id"]
        
        # Update snapshot
        update_data = KnowledgeSnapshotUpdate(
            timestamp=1500,
            knowledge={"original": "updated_value", "new": "new_value"},
            metadata={"version": 2}
        )
        
        result = self.service.update_knowledge_snapshot(snapshot_id, update_data)
        
        assert result is not None
        assert result["timestamp"] == 1500
        assert result["knowledge"]["original"] == "updated_value"
        assert result["knowledge"]["new"] == "new_value"
        assert result["metadata"]["version"] == 2

    def test_update_nonexistent_snapshot(self):
        """Test updating a non-existent snapshot"""
        fake_id = str(uuid4())
        update_data = KnowledgeSnapshotUpdate(knowledge={"test": "value"})
        
        result = self.service.update_knowledge_snapshot(fake_id, update_data)
        assert result is None

    def test_delete_knowledge_snapshot(self):
        """Test deleting a knowledge snapshot"""
        # Create snapshot
        snapshot_data = KnowledgeSnapshotCreate(
            entity_id=self.character_id,
            timestamp=1000,
            knowledge={"to_delete": "value"}
        )
        created = self.service.create_knowledge_snapshot(snapshot_data)
        snapshot_id = created["id"]
        
        # Delete snapshot
        success = self.service.delete_knowledge_snapshot(snapshot_id)
        assert success is True
        
        # Verify it's deleted
        result = self.service.get_knowledge_snapshot(snapshot_id)
        assert result is None

    def test_delete_nonexistent_snapshot(self):
        """Test deleting a non-existent snapshot"""
        fake_id = str(uuid4())
        success = self.service.delete_knowledge_snapshot(fake_id)
        assert success is False

    def test_compute_knowledge_at_timestamp(self):
        """Test computing knowledge state at a specific timestamp"""
        # Create snapshots at different times
        snapshots_data = [
            KnowledgeSnapshotCreate(
                entity_id=self.character_id,
                timestamp=1000,
                knowledge={"fact1": "early_value", "fact2": "value2"}
            ),
            KnowledgeSnapshotCreate(
                entity_id=self.character_id,
                timestamp=2000,
                knowledge={"fact1": "later_value", "fact3": "value3"}
            )
        ]
        
        for snapshot_data in snapshots_data:
            self.service.create_knowledge_snapshot(snapshot_data)
        
        # Compute knowledge at timestamp 1500 (between the two snapshots)
        result = self.service.compute_knowledge_at_timestamp(str(self.character_id), 1500)
        
        assert result["timestamp"] == 1500
        # Should use the most recent snapshot before timestamp 1500
        assert result["knowledge"]["fact1"] == "early_value"
        assert result["knowledge"]["fact2"] == "value2"
        assert "fact3" not in result["knowledge"]  # This was added later

    def test_compute_knowledge_no_snapshots(self):
        """Test computing knowledge when no snapshots exist"""
        result = self.service.compute_knowledge_at_timestamp(str(self.character_id), 1000)
        
        assert result["timestamp"] == 1000
        assert result["knowledge"] == {}

    def test_create_snapshot_from_scene(self):
        """Test creating a snapshot linked to a scene"""
        # First create a base knowledge snapshot
        base_snapshot = KnowledgeSnapshotCreate(
            entity_id=self.character_id,
            timestamp=1000,
            knowledge={"existing_fact": "existing_value"}
        )
        self.service.create_knowledge_snapshot(base_snapshot)
        
        # Create snapshot from scene with knowledge updates
        knowledge_updates = {
            "existing_fact": "updated_value",  # Override existing
            "new_scene_fact": "new_value"      # Add new
        }
        
        result = self.service.create_snapshot_from_scene(
            str(self.character_id),
            str(self.scene_id),
            knowledge_updates
        )
        
        assert result is not None
        assert result["timestamp"] == 2000  # Scene timestamp
        assert result["knowledge"]["existing_fact"] == "updated_value"
        assert result["knowledge"]["new_scene_fact"] == "new_value"
        assert result["metadata"]["source_scene_id"] == str(self.scene_id)

    def test_check_character_knowledge(self):
        """Test checking if character knows specific facts"""
        # Create snapshot with knowledge
        snapshot_data = KnowledgeSnapshotCreate(
            entity_id=self.character_id,
            timestamp=1000,
            knowledge={
                "secret_location": "hidden chamber",
                "ally_trustworthy": True,
                "magic_level": 75
            }
        )
        self.service.create_knowledge_snapshot(snapshot_data)
        
        # Check known fact
        result = self.service.check_character_knowledge(
            str(self.character_id), 
            "secret_location",
            1000
        )
        
        assert result["knows"] is True
        assert result["value"] == "hidden chamber"
        assert result["timestamp"] == 1000
        
        # Check unknown fact
        result = self.service.check_character_knowledge(
            str(self.character_id), 
            "unknown_fact",
            1000
        )
        
        assert result["knows"] is False
        assert result["value"] is None
        assert result["timestamp"] == 1000

    def test_check_character_knowledge_without_timestamp(self):
        """Test checking character knowledge without specifying timestamp"""
        # Create multiple snapshots
        snapshots = [
            KnowledgeSnapshotCreate(
                entity_id=self.character_id,
                timestamp=1000,
                knowledge={"fact1": "old_value"}
            ),
            KnowledgeSnapshotCreate(
                entity_id=self.character_id,
                timestamp=2000,
                knowledge={"fact1": "new_value"}
            )
        ]
        
        for snapshot in snapshots:
            self.service.create_knowledge_snapshot(snapshot)
        
        # Check without timestamp - should use latest
        result = self.service.check_character_knowledge(
            str(self.character_id), 
            "fact1"
        )
        
        assert result["knows"] is True
        assert result["value"] == "new_value"
        assert result["timestamp"] == 2000

    def test_scene_with_no_timestamp(self):
        """Test handling scene with no timestamp"""
        # Create scene without timestamp
        scene_data = {"title": "Scene Without Timestamp"}
        result = self.db.table("scenes").insert(scene_data).execute()
        scene_without_timestamp = result.data[0]["id"]
        
        try:
            # Should return empty list for scene without timestamp
            result = self.service.get_scene_knowledge_snapshots(str(scene_without_timestamp))
            assert result == []
            
        finally:
            self.db.table("scenes").delete().eq("id", scene_without_timestamp).execute()

    def test_knowledge_snapshot_with_complex_data(self):
        """Test knowledge snapshots with complex nested data"""
        complex_knowledge = {
            "relationships": {
                "allies": ["Alice", "Bob"],
                "enemies": ["Carol", "Dave"]
            },
            "locations": {
                "visited": ["castle", "forest", "town"],
                "secret_passages": {
                    "castle": ["basement", "tower"],
                    "forest": ["cave"]
                }
            },
            "quests": {
                "active": [
                    {"name": "Find artifact", "progress": 75},
                    {"name": "Rescue princess", "progress": 25}
                ],
                "completed": ["Slay dragon", "Gather herbs"]
            }
        }
        
        snapshot_data = KnowledgeSnapshotCreate(
            entity_id=self.character_id,
            timestamp=1000,
            knowledge=complex_knowledge
        )
        
        result = self.service.create_knowledge_snapshot(snapshot_data)
        
        assert result is not None
        assert result["knowledge"]["relationships"]["allies"] == ["Alice", "Bob"]
        assert result["knowledge"]["locations"]["secret_passages"]["castle"] == ["basement", "tower"]
        assert result["knowledge"]["quests"]["active"][0]["progress"] == 75
        
        # Verify we can retrieve it correctly
        retrieved = self.service.get_knowledge_snapshot(result["id"])
        assert retrieved["knowledge"] == complex_knowledge
"""Test API model validation and schema compliance"""

import pytest
from uuid import uuid4
from datetime import datetime
from typing import Dict, Any

from pydantic import ValidationError

from app.models.api_models import (
    EntityCreate, EntityUpdate, EntityResponse,
    SceneCreate, SceneUpdate, SceneResponse,
    SceneBlockCreate, SceneBlockUpdate, SceneBlockResponse,
    MilestoneCreate, MilestoneUpdate, MilestoneResponse,
    StoryGoalCreate, StoryGoalUpdate, StoryGoalResponse
)
from app.models.entities import EntityType


class TestEntityModels:
    """Test Entity API model validation"""
    
    def test_entity_create_valid(self):
        """Test EntityCreate with valid data"""
        entity_data = {
            "name": "Test Character",
            "entity_type": "character",
            "description": "A test character",
            "metadata": {
                "role": "protagonist",
                "age": 25,
                "skills": ["sword fighting", "magic"]
            }
        }
        
        entity = EntityCreate(**entity_data)
        assert entity.name == "Test Character"
        assert entity.entity_type == EntityType.CHARACTER
        assert entity.description == "A test character"
        assert entity.metadata["role"] == "protagonist"
        assert entity.metadata["age"] == 25
        assert isinstance(entity.metadata["skills"], list)
    
    def test_entity_create_minimal(self):
        """Test EntityCreate with minimal required fields"""
        entity_data = {
            "name": "Minimal Entity",
            "entity_type": "location"
        }
        
        entity = EntityCreate(**entity_data)
        assert entity.name == "Minimal Entity"
        assert entity.entity_type == EntityType.LOCATION
        assert entity.description is None
        assert entity.metadata is None
    
    def test_entity_create_invalid_type(self):
        """Test EntityCreate with invalid entity type"""
        entity_data = {
            "name": "Test Entity",
            "entity_type": "invalid_type"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            EntityCreate(**entity_data)
        
        error = exc_info.value.errors()[0]
        assert "Input should be" in str(error["msg"])
    
    def test_entity_create_empty_name(self):
        """Test EntityCreate with empty name"""
        entity_data = {
            "name": "",
            "entity_type": "character"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            EntityCreate(**entity_data)
        
        error = exc_info.value.errors()[0]
        assert error["type"] == "string_too_short"
    
    def test_entity_create_long_name(self):
        """Test EntityCreate with name exceeding max length"""
        entity_data = {
            "name": "A" * 256,  # Exceeds 255 character limit
            "entity_type": "character"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            EntityCreate(**entity_data)
        
        error = exc_info.value.errors()[0]
        assert error["type"] == "string_too_long"
    
    def test_entity_update_partial(self):
        """Test EntityUpdate with partial data"""
        update_data = {
            "name": "Updated Name",
            "metadata": {"new_field": "new_value"}
        }
        
        entity_update = EntityUpdate(**update_data)
        assert entity_update.name == "Updated Name"
        assert entity_update.entity_type is None  # Optional field
        assert entity_update.description is None
        assert entity_update.metadata["new_field"] == "new_value"
    
    def test_entity_response_structure(self):
        """Test EntityResponse structure"""
        response_data = {
            "id": str(uuid4()),
            "name": "Response Entity",
            "entity_type": "artifact",
            "description": "Test description",
            "metadata": {"test": "value"},
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        entity_response = EntityResponse(**response_data)
        assert str(entity_response.id) == response_data["id"]
        assert entity_response.name == "Response Entity"
        assert entity_response.entity_type == EntityType.ARTIFACT
        assert entity_response.metadata["test"] == "value"
        assert entity_response.created_at is not None
        assert entity_response.updated_at is not None


class TestSceneModels:
    """Test Scene API model validation"""
    
    def test_scene_create_valid(self):
        """Test SceneCreate with valid data"""
        scene_data = {
            "title": "Test Scene",
            "location_id": str(uuid4()),
            "timestamp": 150
        }
        
        scene = SceneCreate(**scene_data)
        assert scene.title == "Test Scene"
        assert scene.location_id is not None
        assert scene.timestamp == 150
    
    def test_scene_create_minimal(self):
        """Test SceneCreate with minimal required fields"""
        scene_data = {
            "title": "Minimal Scene"
        }
        
        scene = SceneCreate(**scene_data)
        assert scene.title == "Minimal Scene"
        assert scene.location_id is None
        assert scene.timestamp is None
    
    def test_scene_create_negative_timestamp(self):
        """Test SceneCreate with negative timestamp (should be valid)"""
        scene_data = {
            "title": "Pre-story Scene",
            "timestamp": -100
        }
        
        scene = SceneCreate(**scene_data)
        assert scene.timestamp == -100  # Should accept negative timestamps
    
    def test_scene_create_invalid_location_uuid(self):
        """Test SceneCreate with invalid UUID format"""
        scene_data = {
            "title": "Test Scene",
            "location_id": "not-a-valid-uuid"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            SceneCreate(**scene_data)
        
        error = exc_info.value.errors()[0]
        assert "Input should be a valid UUID" in str(error["msg"])
    
    def test_scene_update_partial(self):
        """Test SceneUpdate with partial data"""
        update_data = {
            "title": "Updated Scene Title",
            "timestamp": 200
        }
        
        scene_update = SceneUpdate(**update_data)
        assert scene_update.title == "Updated Scene Title"
        assert scene_update.location_id is None
        assert scene_update.timestamp == 200
    
    def test_scene_response_structure(self):
        """Test SceneResponse structure"""
        response_data = {
            "id": str(uuid4()),
            "title": "Response Scene",
            "location_id": str(uuid4()),
            "timestamp": 100,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        scene_response = SceneResponse(**response_data)
        assert str(scene_response.id) == response_data["id"]
        assert scene_response.title == "Response Scene"
        assert scene_response.timestamp == 100
        assert scene_response.created_at is not None


class TestSceneBlockModels:
    """Test Scene Block API model validation"""
    
    def test_scene_block_create_prose(self):
        """Test SceneBlockCreate for prose block"""
        block_data = {
            "block_type": "prose",
            "content": "This is prose content describing the scene.",
            "sort_order": 1
        }
        
        block = SceneBlockCreate(**block_data)
        assert block.block_type == "prose"
        assert block.content == "This is prose content describing the scene."
        assert block.sort_order == 1
        assert block.speaker_id is None
        assert block.listener_ids is None
        assert block.emotion is None
        assert block.milestone_id is None
    
    def test_scene_block_create_dialogue(self):
        """Test SceneBlockCreate for dialogue block"""
        speaker_id = uuid4()
        listener_ids = [uuid4(), uuid4()]
        
        block_data = {
            "block_type": "dialogue",
            "content": "Hello, how are you?",
            "sort_order": 2,
            "speaker_id": str(speaker_id),
            "listener_ids": [str(lid) for lid in listener_ids],
            "emotion": "friendly"
        }
        
        block = SceneBlockCreate(**block_data)
        assert block.block_type == "dialogue"
        assert block.content == "Hello, how are you?"
        assert block.speaker_id == speaker_id
        assert len(block.listener_ids) == 2
        assert block.emotion == "friendly"
    
    def test_scene_block_create_milestone(self):
        """Test SceneBlockCreate for milestone block"""
        milestone_id = uuid4()
        
        block_data = {
            "block_type": "milestone",
            "content": "The hero obtains the magical sword.",
            "sort_order": 3,
            "milestone_id": str(milestone_id)
        }
        
        block = SceneBlockCreate(**block_data)
        assert block.block_type == "milestone"
        assert block.content == "The hero obtains the magical sword."
        assert block.milestone_id == milestone_id
    
    def test_scene_block_create_invalid_type(self):
        """Test SceneBlockCreate with invalid block type"""
        block_data = {
            "block_type": "invalid_type",
            "content": "This should fail",
            "sort_order": 1
        }
        
        with pytest.raises(ValidationError) as exc_info:
            SceneBlockCreate(**block_data)
        
        error = exc_info.value.errors()[0]
        assert "Input should be" in str(error["msg"])
    
    def test_scene_block_update_content_only(self):
        """Test SceneBlockUpdate with content change only"""
        update_data = {
            "content": "Updated block content"
        }
        
        block_update = SceneBlockUpdate(**update_data)
        assert block_update.content == "Updated block content"
        assert block_update.sort_order is None
        assert block_update.speaker_id is None
    
    def test_scene_block_response_structure(self):
        """Test SceneBlockResponse structure"""
        response_data = {
            "id": str(uuid4()),
            "scene_id": str(uuid4()),
            "block_type": "dialogue",
            "content": "Response dialogue content",
            "sort_order": 5,
            "speaker_id": str(uuid4()),
            "listener_ids": [str(uuid4())],
            "emotion": "excited",
            "milestone_id": None,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        block_response = SceneBlockResponse(**response_data)
        assert str(block_response.id) == response_data["id"]
        assert str(block_response.scene_id) == response_data["scene_id"]
        assert block_response.block_type == "dialogue"
        assert block_response.sort_order == 5
        assert block_response.emotion == "excited"


class TestMilestoneModels:
    """Test Milestone API model validation (first-class entities)"""
    
    def test_milestone_create_valid(self):
        """Test MilestoneCreate with valid data"""
        subject_id = uuid4()
        object_id = uuid4()
        
        milestone_data = {
            "subject_id": str(subject_id),
            "verb": "defeats",
            "object_id": str(object_id),
            "description": "Hero defeats the villain in epic battle",
            "timestamp": 300,
            "significance": "critical"
        }
        
        milestone = MilestoneCreate(**milestone_data)
        assert milestone.subject_id == subject_id
        assert milestone.verb == "defeats"
        assert milestone.object_id == object_id
        assert milestone.description == "Hero defeats the villain in epic battle"
        assert milestone.timestamp == 300
        assert milestone.significance == "critical"
    
    def test_milestone_create_minimal(self):
        """Test MilestoneCreate with minimal required fields"""
        milestone_data = {
            "subject_id": str(uuid4()),
            "verb": "obtains",
            "object_id": str(uuid4()),
            "timestamp": 150
        }
        
        milestone = MilestoneCreate(**milestone_data)
        assert milestone.verb == "obtains"
        assert milestone.timestamp == 150
        assert milestone.description is None
        assert milestone.significance is None
    
    def test_milestone_create_invalid_uuids(self):
        """Test MilestoneCreate with invalid UUID formats"""
        milestone_data = {
            "subject_id": "not-a-uuid",
            "verb": "action",
            "object_id": "also-not-a-uuid",
            "timestamp": 100
        }
        
        with pytest.raises(ValidationError) as exc_info:
            MilestoneCreate(**milestone_data)
        
        errors = exc_info.value.errors()
        assert len(errors) >= 2  # Both subject_id and object_id should fail
        assert all("Input should be a valid UUID" in str(error["msg"]) for error in errors)
    
    def test_milestone_update_partial(self):
        """Test MilestoneUpdate with partial data"""
        update_data = {
            "description": "Updated milestone description",
            "significance": "major"
        }
        
        milestone_update = MilestoneUpdate(**update_data)
        assert milestone_update.description == "Updated milestone description"
        assert milestone_update.significance == "major"
        assert milestone_update.timestamp is None
    
    def test_milestone_response_structure(self):
        """Test MilestoneResponse structure"""
        response_data = {
            "id": str(uuid4()),
            "subject_id": str(uuid4()),
            "verb": "discovers",
            "object_id": str(uuid4()),
            "description": "Character discovers hidden truth",
            "timestamp": 250,
            "significance": "major",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        milestone_response = MilestoneResponse(**response_data)
        assert str(milestone_response.id) == response_data["id"]
        assert milestone_response.verb == "discovers"
        assert milestone_response.timestamp == 250
        assert milestone_response.significance == "major"


class TestStoryGoalModels:
    """Test Story Goal API model validation"""
    
    def test_story_goal_create_valid(self):
        """Test StoryGoalCreate with valid data"""
        subject_id = uuid4()
        object_id = uuid4()
        
        goal_data = {
            "subject_id": str(subject_id),
            "verb": "rescue",
            "object_id": str(object_id),
            "description": "Hero must rescue the captive princess",
            "status": "active",
            "priority": "high"
        }
        
        goal = StoryGoalCreate(**goal_data)
        assert goal.subject_id == subject_id
        assert goal.verb == "rescue"
        assert goal.object_id == object_id
        assert goal.description == "Hero must rescue the captive princess"
        assert goal.status == "active"
        assert goal.priority == "high"
    
    def test_story_goal_create_minimal(self):
        """Test StoryGoalCreate with minimal required fields"""
        goal_data = {
            "subject_id": str(uuid4()),
            "verb": "complete",
            "object_id": str(uuid4())
        }
        
        goal = StoryGoalCreate(**goal_data)
        assert goal.verb == "complete"
        assert goal.description is None
        assert goal.status is None
        assert goal.priority is None
    
    def test_story_goal_update_status(self):
        """Test StoryGoalUpdate for status changes"""
        update_data = {
            "status": "completed",
            "priority": "low"
        }
        
        goal_update = StoryGoalUpdate(**update_data)
        assert goal_update.status == "completed"
        assert goal_update.priority == "low"
        assert goal_update.description is None
    
    def test_story_goal_response_structure(self):
        """Test StoryGoalResponse structure"""
        response_data = {
            "id": str(uuid4()),
            "subject_id": str(uuid4()),
            "verb": "protect",
            "object_id": str(uuid4()),
            "description": "Protect the village from invasion",
            "status": "active",
            "priority": "critical",
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }
        
        goal_response = StoryGoalResponse(**response_data)
        assert str(goal_response.id) == response_data["id"]
        assert goal_response.verb == "protect"
        assert goal_response.status == "active"
        assert goal_response.priority == "critical"


class TestModelValidationEdgeCases:
    """Test edge cases and validation scenarios"""
    
    def test_uuid_field_validation(self):
        """Test UUID field validation across models"""
        # Test invalid UUID in EntityCreate
        with pytest.raises(ValidationError):
            EntityCreate(name="Test", entity_type="character")
        
        # Test valid UUID parsing
        valid_uuid = str(uuid4())
        scene = SceneCreate(title="Test", location_id=valid_uuid)
        assert str(scene.location_id) == valid_uuid
    
    def test_optional_fields_none_handling(self):
        """Test handling of None values for optional fields"""
        # Entity with None metadata
        entity = EntityCreate(name="Test", entity_type="character", metadata=None)
        assert entity.metadata is None
        
        # Scene with None timestamp
        scene = SceneCreate(title="Test", timestamp=None)
        assert scene.timestamp is None
        
        # Block with None optional fields
        block = SceneBlockCreate(
            block_type="prose",
            content="Test",
            sort_order=1,
            speaker_id=None,
            listener_ids=None
        )
        assert block.speaker_id is None
        assert block.listener_ids is None
    
    def test_list_field_validation(self):
        """Test validation of list fields"""
        # Valid listener_ids list
        listener_ids = [str(uuid4()), str(uuid4())]
        block = SceneBlockCreate(
            block_type="dialogue",
            content="Test dialogue",
            sort_order=1,
            speaker_id=str(uuid4()),
            listener_ids=listener_ids
        )
        assert len(block.listener_ids) == 2
        
        # Empty list should be valid
        block_empty = SceneBlockCreate(
            block_type="dialogue",
            content="Test dialogue",
            sort_order=1,
            speaker_id=str(uuid4()),
            listener_ids=[]
        )
        assert block_empty.listener_ids == []
    
    def test_metadata_flexibility(self):
        """Test metadata field flexibility (JSONB equivalent)"""
        # Complex nested metadata
        complex_metadata = {
            "character_stats": {
                "strength": 15,
                "intelligence": 18,
                "charisma": 12
            },
            "inventory": [
                {"item": "sword", "enchantment": "fire"},
                {"item": "potion", "effect": "healing"}
            ],
            "relationships": {
                "allies": ["friend1", "friend2"],
                "enemies": ["villain1"],
                "neutral": []
            },
            "flags": {
                "has_seen_dragon": True,
                "completed_tutorial": False
            }
        }
        
        entity = EntityCreate(
            name="Complex Character",
            entity_type="character",
            metadata=complex_metadata
        )
        
        assert entity.metadata["character_stats"]["strength"] == 15
        assert len(entity.metadata["inventory"]) == 2
        assert entity.metadata["flags"]["has_seen_dragon"] is True
    
    def test_string_length_validation(self):
        """Test string length constraints"""
        # Test max length for entity name (should be 255)
        max_name = "A" * 255
        entity = EntityCreate(name=max_name, entity_type="character")
        assert len(entity.name) == 255
        
        # Test exceeding max length
        with pytest.raises(ValidationError):
            EntityCreate(name="A" * 256, entity_type="character")
    
    def test_timestamp_validation(self):
        """Test timestamp field validation (INT type)"""
        # Positive timestamps
        scene_positive = SceneCreate(title="Future Scene", timestamp=1000)
        assert scene_positive.timestamp == 1000
        
        # Zero timestamp
        scene_zero = SceneCreate(title="Origin Scene", timestamp=0)
        assert scene_zero.timestamp == 0
        
        # Negative timestamps (prehistory)
        scene_negative = SceneCreate(title="Past Scene", timestamp=-500)
        assert scene_negative.timestamp == -500
        
        # Large timestamps
        scene_large = SceneCreate(title="Far Future", timestamp=999999)
        assert scene_large.timestamp == 999999
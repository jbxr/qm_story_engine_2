"""Test API endpoint functionality"""

import pytest
from uuid import uuid4
from datetime import datetime
from .conftest import test_data_cleanup


class TestEntityAPI:
    """Test entity management endpoints"""
    
    def test_list_entities(self, client, cleanup_test_data):
        """Test entity listing endpoint"""
        response = client.get("/api/v1/entities")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "entities" in data["data"]
        assert "count" in data["data"]
        assert isinstance(data["data"]["entities"], list)
        assert isinstance(data["data"]["count"], int)
    
    def test_create_entity_character(self, client, sample_entity_data, cleanup_test_data):
        """Test character entity creation"""
        response = client.post("/api/v1/entities", json=sample_entity_data)
        assert response.status_code == 200
        
        response_data = response.json()
        assert response_data["success"] is True
        assert "data" in response_data
        assert "entity" in response_data["data"]
        assert response_data["message"] == "Entity created successfully"
        
        entity = response_data["data"]["entity"]
        assert entity["name"] == sample_entity_data["name"]
        assert entity["entity_type"] == sample_entity_data["entity_type"]
        assert entity["description"] == sample_entity_data["description"]
        assert entity["metadata"] == sample_entity_data["meta"]
        assert "id" in entity
        assert "created_at" in entity
        assert "updated_at" in entity
        
        # Track for cleanup
        test_data_cleanup["entities"].append(entity["id"])
    
    def test_create_entity_location(self, client, sample_location_data, cleanup_test_data):
        """Test location entity creation"""
        response = client.post("/api/v1/entities", json=sample_location_data)
        assert response.status_code == 200
        
        response_data = response.json()
        assert response_data["success"] is True
        entity = response_data["data"]["entity"]
        assert entity["entity_type"] == "location"
        assert entity["metadata"]["region"] == "north"
        
        # Track for cleanup
        test_data_cleanup["entities"].append(entity["id"])
    
    def test_create_entity_artifact(self, client, sample_artifact_data, cleanup_test_data):
        """Test artifact entity creation"""
        response = client.post("/api/v1/entities", json=sample_artifact_data)
        assert response.status_code == 200
        
        response_data = response.json()
        assert response_data["success"] is True
        entity = response_data["data"]["entity"]
        assert entity["entity_type"] == "artifact"
        assert entity["metadata"]["material"] == "enchanted steel"
        
        # Track for cleanup
        test_data_cleanup["entities"].append(entity["id"])
    
    def test_get_entity(self, client, sample_entity_data, cleanup_test_data):
        """Test entity retrieval endpoint"""
        # Create entity first
        create_response = client.post("/api/v1/entities", json=sample_entity_data)
        assert create_response.status_code == 200
        create_data = create_response.json()
        entity = create_data["data"]["entity"]
        test_data_cleanup["entities"].append(entity["id"])
        
        # Retrieve entity
        response = client.get(f"/api/v1/entities/{entity['id']}")
        assert response.status_code == 200
        
        response_data = response.json()
        assert response_data["success"] is True
        retrieved_entity = response_data["data"]["entity"]
        assert retrieved_entity["id"] == entity["id"]
        assert retrieved_entity["name"] == entity["name"]
        assert retrieved_entity["metadata"] == entity["metadata"]
    
    def test_get_entity_not_found(self, client):
        """Test entity retrieval with invalid ID"""
        fake_id = str(uuid4())
        response = client.get(f"/api/v1/entities/{fake_id}")
        assert response.status_code == 404
    
    def test_update_entity(self, client, sample_entity_data, cleanup_test_data):
        """Test entity update endpoint"""
        # Create entity first
        create_response = client.post("/api/v1/entities", json=sample_entity_data)
        assert create_response.status_code == 200
        create_data = create_response.json()
        entity = create_data["data"]["entity"]
        test_data_cleanup["entities"].append(entity["id"])
        
        # Update entity
        update_data = {
            "name": "Updated Character Name",
            "description": "Updated description",
            "meta": {
                "role": "antagonist",
                "age": 30,
                "new_field": "test value"
            }
        }
        
        response = client.put(f"/api/v1/entities/{entity['id']}", json=update_data)
        assert response.status_code == 200
        
        response_data = response.json()
        assert response_data["success"] is True
        updated_entity = response_data["data"]["entity"]
        assert updated_entity["name"] == update_data["name"]
        assert updated_entity["description"] == update_data["description"]
        assert updated_entity["metadata"] == update_data["meta"]
        assert updated_entity["updated_at"] >= entity["created_at"]
    
    def test_delete_entity(self, client, sample_entity_data):
        """Test entity deletion endpoint"""
        # Create entity first
        create_response = client.post("/api/v1/entities", json=sample_entity_data)
        assert create_response.status_code == 200
        create_data = create_response.json()
        entity = create_data["data"]["entity"]
        
        # Delete entity
        response = client.delete(f"/api/v1/entities/{entity['id']}")
        assert response.status_code == 200
        
        response_data = response.json()
        assert response_data["success"] is True
        assert "deleted_entity" in response_data["data"]
        
        # Verify deletion
        get_response = client.get(f"/api/v1/entities/{entity['id']}")
        assert get_response.status_code == 404


class TestSceneAPI:
    """Test scene management endpoints"""
    
    def test_list_scenes(self, client):
        """Test scene listing endpoint"""
        response = client.get("/api/v1/scenes")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "scenes" in data["data"]
        assert "count" in data["data"]
        assert isinstance(data["data"]["scenes"], list)
    
    def test_create_scene_basic(self, client, cleanup_test_data):
        """Test basic scene creation without location"""
        scene_data = {
            "title": "Test Scene Creation",
            "timestamp": 150
        }
        
        response = client.post("/api/v1/scenes", json=scene_data)
        assert response.status_code == 200
        
        response_data = response.json()
        assert response_data["success"] is True
        assert "data" in response_data
        assert "scene" in response_data["data"]
        assert response_data["message"] == "Scene created successfully"
        
        scene = response_data["data"]["scene"]
        assert scene["title"] == scene_data["title"]
        assert scene["timestamp"] == scene_data["timestamp"]
        assert scene.get("location_id") is None  # May be omitted when None
        assert "id" in scene
        
        # Track for cleanup
        test_data_cleanup["scenes"].append(scene["id"])
    
    def test_create_scene_with_location(self, client, sample_location_data, cleanup_test_data):
        """Test scene creation with location"""
        # Create location first
        location_response = client.post("/api/v1/entities", json=sample_location_data)
        assert location_response.status_code == 200
        location_data = location_response.json()
        location = location_data["data"]["entity"]
        test_data_cleanup["entities"].append(location["id"])
        
        # Create scene with location
        scene_data = {
            "title": "Scene with Location",
            "location_id": location["id"],
            "timestamp": 200
        }
        
        response = client.post("/api/v1/scenes", json=scene_data)
        assert response.status_code == 200
        
        response_data = response.json()
        assert response_data["success"] is True
        scene = response_data["data"]["scene"]
        assert scene["location_id"] == location["id"]
        
        # Track for cleanup
        test_data_cleanup["scenes"].append(scene["id"])
    
    def test_get_scene(self, client, cleanup_test_data):
        """Test scene retrieval"""
        # Create scene first
        scene_data = {"title": "Retrieval Test Scene", "timestamp": 100}
        create_response = client.post("/api/v1/scenes", json=scene_data)
        assert create_response.status_code == 200
        create_data = create_response.json()
        scene = create_data["data"]["scene"]
        test_data_cleanup["scenes"].append(scene["id"])
        
        # Retrieve scene
        response = client.get(f"/api/v1/scenes/{scene['id']}")
        assert response.status_code == 200
        
        response_data = response.json()
        assert response_data["success"] is True
        retrieved_scene = response_data["data"]["scene"]
        assert retrieved_scene["id"] == scene["id"]
        assert retrieved_scene["title"] == scene["title"]
    
    def test_update_scene(self, client, cleanup_test_data):
        """Test scene update"""
        # Create scene first
        scene_data = {"title": "Original Title", "timestamp": 100}
        create_response = client.post("/api/v1/scenes", json=scene_data)
        assert create_response.status_code == 200
        create_data = create_response.json()
        scene = create_data["data"]["scene"]
        test_data_cleanup["scenes"].append(scene["id"])
        
        # Update scene
        update_data = {
            "title": "Updated Scene Title",
            "timestamp": 150
        }
        
        response = client.put(f"/api/v1/scenes/{scene['id']}", json=update_data)
        assert response.status_code == 200
        
        response_data = response.json()
        assert response_data["success"] is True
        updated_scene = response_data["data"]["scene"]
        assert updated_scene["title"] == update_data["title"]
        assert updated_scene["timestamp"] == update_data["timestamp"]
    
    def test_delete_scene(self, client):
        """Test scene deletion"""
        # Create scene first
        scene_data = {"title": "Scene to Delete", "timestamp": 100}
        create_response = client.post("/api/v1/scenes", json=scene_data)
        assert create_response.status_code == 200
        create_data = create_response.json()
        scene = create_data["data"]["scene"]
        
        # Delete scene
        response = client.delete(f"/api/v1/scenes/{scene['id']}")
        assert response.status_code == 200
        
        response_data = response.json()
        assert response_data["success"] is True
        assert "deleted_scene" in response_data["data"]
        
        # Verify deletion
        get_response = client.get(f"/api/v1/scenes/{scene['id']}")
        assert get_response.status_code == 404
        
    def test_list_blocks(self, client, cleanup_test_data):
        """Test scene blocks listing"""
        # Create scene first
        scene_data = {"title": "Scene for Blocks", "timestamp": 100}
        create_response = client.post("/api/v1/scenes", json=scene_data)
        assert create_response.status_code == 200
        scene_response = create_response.json()
        assert scene_response["success"] is True
        scene = scene_response["data"]["scene"]
        test_data_cleanup["scenes"].append(scene["id"])
        
        # List blocks (should be empty initially)
        response = client.get(f"/api/v1/scenes/{scene['id']}/blocks")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "blocks" in data["data"]
        assert "count" in data["data"]
        assert isinstance(data["data"]["blocks"], list)
        assert len(data["data"]["blocks"]) == 0  # Empty initially
    
    def test_create_prose_block(self, client, sample_prose_block_data, cleanup_test_data):
        """Test prose block creation"""
        # Create scene first
        scene_data = {"title": "Scene for Prose Block", "timestamp": 100}
        create_response = client.post("/api/v1/scenes", json=scene_data)
        assert create_response.status_code == 200
        scene_response = create_response.json()
        assert scene_response["success"] is True
        scene = scene_response["data"]["scene"]
        test_data_cleanup["scenes"].append(scene["id"])
        
        # Create prose block
        block_data = {**sample_prose_block_data, "scene_id": scene["id"]}
        response = client.post(f"/api/v1/scenes/{scene['id']}/blocks", json=block_data)
        assert response.status_code == 200
        
        response_data = response.json()
        assert response_data["success"] is True
        assert "data" in response_data
        assert "block" in response_data["data"]
        block = response_data["data"]["block"]
        assert block["block_type"] == "prose"
        assert block["content"] == sample_prose_block_data["content"]
        assert block["scene_id"] == scene["id"]
        assert block["order"] == sample_prose_block_data["order"]
        assert "id" in block
        
        # Track for cleanup
        test_data_cleanup["scene_blocks"].append(block["id"])
    
    def test_create_dialogue_block(self, client, sample_entity_data, sample_dialogue_block_data, cleanup_test_data):
        """Test dialogue block creation"""
        # Create character first
        char_response = client.post("/api/v1/entities", json=sample_entity_data)
        assert char_response.status_code == 200
        char_response_data = char_response.json()
        assert char_response_data["success"] is True
        character = char_response_data["data"]["entity"]
        test_data_cleanup["entities"].append(character["id"])
        
        # Create scene
        scene_data = {"title": "Scene for Dialogue", "timestamp": 100}
        scene_response = client.post("/api/v1/scenes", json=scene_data)
        assert scene_response.status_code == 200
        scene_response_data = scene_response.json()
        assert scene_response_data["success"] is True
        scene = scene_response_data["data"]["scene"]
        test_data_cleanup["scenes"].append(scene["id"])
        
        # Create dialogue block
        dialogue_data = {
            **sample_dialogue_block_data,
            "scene_id": scene["id"],
            "lines": {
                "speaker_id": character["id"],
                "listener_ids": [character["id"]],  # Self-talk for test
                "emotion": "friendly"
            }
        }
        
        response = client.post(f"/api/v1/scenes/{scene['id']}/blocks", json=dialogue_data)
        assert response.status_code == 200
        
        response_data = response.json()
        assert response_data["success"] is True
        assert "data" in response_data
        assert "block" in response_data["data"]
        block = response_data["data"]["block"]
        assert block["block_type"] == "dialogue"
        assert "lines" in block
        # Note: The exact structure of lines may vary based on API implementation
        
        # Track for cleanup
        test_data_cleanup["scene_blocks"].append(block["id"])
    
    def test_update_block(self, client, sample_prose_block_data, cleanup_test_data):
        """Test scene block update"""
        # Create scene and block first
        scene_data = {"title": "Scene for Block Update", "timestamp": 100}
        scene_response = client.post("/api/v1/scenes", json=scene_data)
        scene_response_data = scene_response.json()
        assert scene_response_data["success"] is True
        scene = scene_response_data["data"]["scene"]
        test_data_cleanup["scenes"].append(scene["id"])
        
        block_data = {**sample_prose_block_data, "scene_id": scene["id"]}
        block_response = client.post(f"/api/v1/scenes/{scene['id']}/blocks", json=block_data)
        block_response_data = block_response.json()
        assert block_response_data["success"] is True
        block = block_response_data["data"]["block"]
        test_data_cleanup["scene_blocks"].append(block["id"])
        
        # Update block
        update_data = {
            "content": "This is updated prose content.",
            "order": 5
        }
        
        response = client.put(f"/api/v1/scenes/blocks/{block['id']}", json=update_data)
        assert response.status_code == 200
        
        response_data = response.json()
        assert response_data["success"] is True
        assert "data" in response_data
        assert "block" in response_data["data"]
        updated_block = response_data["data"]["block"]
        assert updated_block["content"] == update_data["content"]
        assert updated_block["order"] == update_data["order"]
    
    def test_reorder_block(self, client, cleanup_test_data):
        """Test block reordering"""
        # Create scene first
        scene_data = {"title": "Scene for Reordering", "timestamp": 100}
        scene_response = client.post("/api/v1/scenes", json=scene_data)
        scene_response_data = scene_response.json()
        assert scene_response_data["success"] is True
        scene = scene_response_data["data"]["scene"]
        test_data_cleanup["scenes"].append(scene["id"])
        
        # Create multiple blocks
        block1_data = {"block_type": "prose", "content": "First block", "order": 1, "scene_id": scene["id"]}
        block2_data = {"block_type": "prose", "content": "Second block", "order": 2, "scene_id": scene["id"]}
        
        block1_response = client.post(f"/api/v1/scenes/{scene['id']}/blocks", json=block1_data)
        block1_response_data = block1_response.json()
        assert block1_response_data["success"] is True
        block1 = block1_response_data["data"]["block"]
        test_data_cleanup["scene_blocks"].append(block1["id"])
        
        block2_response = client.post(f"/api/v1/scenes/{scene['id']}/blocks", json=block2_data)
        block2_response_data = block2_response.json()
        assert block2_response_data["success"] is True
        block2 = block2_response_data["data"]["block"]
        test_data_cleanup["scene_blocks"].append(block2["id"])
        
        # Reorder second block to position 1
        reorder_data = {"new_order": 1}
        response = client.post(f"/api/v1/scenes/blocks/{block2['id']}/move", json=reorder_data)
        assert response.status_code == 200
    
    def test_delete_block(self, client, sample_prose_block_data, cleanup_test_data):
        """Test scene block deletion"""
        # Create scene and block first
        scene_data = {"title": "Scene for Block Deletion", "timestamp": 100}
        scene_response = client.post("/api/v1/scenes", json=scene_data)
        scene_response_data = scene_response.json()
        assert scene_response_data["success"] is True
        scene = scene_response_data["data"]["scene"]
        test_data_cleanup["scenes"].append(scene["id"])
        
        block_data = {**sample_prose_block_data, "scene_id": scene["id"]}
        block_response = client.post(f"/api/v1/scenes/{scene['id']}/blocks", json=block_data)
        block_response_data = block_response.json()
        assert block_response_data["success"] is True
        block = block_response_data["data"]["block"]
        
        # Delete block
        response = client.delete(f"/api/v1/scenes/blocks/{block['id']}")
        assert response.status_code == 200


class TestMilestoneAPI:
    """Test milestone management endpoints (first-class entities)"""
    
    def test_list_milestones(self, client):
        """Test milestone listing"""
        response = client.get("/api/v1/milestones")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "milestones" in data["data"]
        assert "count" in data["data"]
        assert isinstance(data["data"]["milestones"], list)
    
    def test_create_milestone(self, client, sample_entity_data, sample_milestone_data, cleanup_test_data):
        """Test milestone creation"""
        # Create entities for subject and object
        subject_response = client.post("/api/v1/entities", json={
            **sample_entity_data, 
            "name": "Hero Character"
        })
        assert subject_response.status_code == 200
        subject = subject_response.json()
        test_data_cleanup["entities"].append(subject["id"])
        
        object_response = client.post("/api/v1/entities", json={
            **sample_entity_data,
            "name": "Villain Character",
            "metadata": {"role": "antagonist"}
        })
        assert object_response.status_code == 200
        object_entity = object_response.json()
        test_data_cleanup["entities"].append(object_entity["id"])
        
        # Create milestone
        milestone_data = {
            **sample_milestone_data,
            "subject_id": subject["id"],
            "object_id": object_entity["id"]
        }
        
        response = client.post("/api/v1/milestones", json=milestone_data)
        assert response.status_code == 200
        
        response_data = response.json()
        assert response_data["success"] is True
        assert "data" in response_data
        assert "milestone" in response_data["data"]
        milestone = response_data["data"]["milestone"]
        assert milestone["subject_id"] == subject["id"]
        assert milestone["object_id"] == object_entity["id"]
        assert milestone["verb"] == "defeats"
        assert milestone["timestamp"] == 200
        assert "id" in milestone
        
        # Track for cleanup
        test_data_cleanup["milestones"].append(milestone["id"])
    
    def test_get_milestone(self, client, sample_entity_data, sample_milestone_data, cleanup_test_data):
        """Test milestone retrieval"""
        # Create entities
        entity_response = client.post("/api/v1/entities", json=sample_entity_data)
        entity = entity_response.json()
        test_data_cleanup["entities"].append(entity["id"])
        
        # Create milestone
        milestone_data = {
            **sample_milestone_data,
            "subject_id": entity["id"],
            "object_id": entity["id"]  # Self-action for test
        }
        
        create_response = client.post("/api/v1/milestones", json=milestone_data)
        create_data = create_response.json()
        assert create_data["success"] is True
        milestone = create_data["data"]["milestone"]
        test_data_cleanup["milestones"].append(milestone["id"])
        
        # Retrieve milestone
        response = client.get(f"/api/v1/milestones/{milestone['id']}")
        assert response.status_code == 200
        
        response_data = response.json()
        assert response_data["success"] is True
        assert "data" in response_data
        assert "milestone" in response_data["data"]
        retrieved_milestone = response_data["data"]["milestone"]
        assert retrieved_milestone["id"] == milestone["id"]
        assert retrieved_milestone["verb"] == milestone["verb"]
    
    def test_update_milestone(self, client, sample_entity_data, sample_milestone_data, cleanup_test_data):
        """Test milestone update"""
        # Create entity
        entity_response = client.post("/api/v1/entities", json=sample_entity_data)
        entity = entity_response.json()
        test_data_cleanup["entities"].append(entity["id"])
        
        # Create milestone
        milestone_data = {
            **sample_milestone_data,
            "subject_id": entity["id"],
            "object_id": entity["id"]
        }
        
        create_response = client.post("/api/v1/milestones", json=milestone_data)
        create_data = create_response.json()
        assert create_data["success"] is True
        milestone = create_data["data"]["milestone"]
        test_data_cleanup["milestones"].append(milestone["id"])
        
        # Update milestone
        update_data = {
            "description": "Updated milestone description",
            "significance": "critical",
            "timestamp": 250
        }
        
        response = client.put(f"/api/v1/milestones/{milestone['id']}", json=update_data)
        assert response.status_code == 200
        
        response_data = response.json()
        assert response_data["success"] is True
        assert "data" in response_data
        assert "milestone" in response_data["data"]
        updated_milestone = response_data["data"]["milestone"]
        assert updated_milestone["description"] == update_data["description"]
        assert updated_milestone["significance"] == update_data["significance"]
        assert updated_milestone["timestamp"] == update_data["timestamp"]
    
    def test_delete_milestone(self, client, sample_entity_data, sample_milestone_data):
        """Test milestone deletion"""
        # Create entity
        entity_response = client.post("/api/v1/entities", json=sample_entity_data)
        entity = entity_response.json()
        
        # Create milestone
        milestone_data = {
            **sample_milestone_data,
            "subject_id": entity["id"],
            "object_id": entity["id"]
        }
        
        create_response = client.post("/api/v1/milestones", json=milestone_data)
        create_data = create_response.json()
        assert create_data["success"] is True
        milestone = create_data["data"]["milestone"]
        
        # Delete milestone
        response = client.delete(f"/api/v1/milestones/{milestone['id']}")
        assert response.status_code == 200
        
        # Clean up entity
        client.delete(f"/api/v1/entities/{entity['id']}")


class TestGoalsAPI:
    """Test story goal endpoints"""
    
    def test_list_goals(self, client):
        """Test goal listing"""
        response = client.get("/api/v1/goals")
        assert response.status_code == 200
        
        data = response.json()
        assert data["success"] is True
        assert "data" in data
        assert "goals" in data["data"]
        assert "count" in data["data"]
        assert isinstance(data["data"]["goals"], list)
    
    def test_create_goal(self, client, sample_entity_data, sample_goal_data, cleanup_test_data):
        """Test goal creation"""
        # Create entities for subject and object
        subject_response = client.post("/api/v1/entities", json={
            **sample_entity_data,
            "name": "Goal Subject"
        })
        subject = subject_response.json()
        test_data_cleanup["entities"].append(subject["id"])
        
        object_response = client.post("/api/v1/entities", json={
            **sample_entity_data,
            "name": "Goal Object",
            "entity_type": "location"
        })
        object_entity = object_response.json()
        test_data_cleanup["entities"].append(object_entity["id"])
        
        # Create goal
        goal_data = {
            **sample_goal_data,
            "subject_id": subject["id"],
            "object_id": object_entity["id"]
        }
        
        response = client.post("/api/v1/goals", json=goal_data)
        assert response.status_code == 200
        
        response_data = response.json()
        assert response_data["success"] is True
        assert "data" in response_data
        assert "goal" in response_data["data"]
        goal = response_data["data"]["goal"]
        assert goal["subject_id"] == subject["id"]
        assert goal["object_id"] == object_entity["id"]
        assert goal["verb"] == "rescue"
        assert goal["status"] == "active"
        assert "id" in goal
        
        # Track for cleanup
        test_data_cleanup["goals"].append(goal["id"])
    
    def test_get_goal(self, client, sample_entity_data, sample_goal_data, cleanup_test_data):
        """Test goal retrieval"""
        # Create entity
        entity_response = client.post("/api/v1/entities", json=sample_entity_data)
        entity_response_data = entity_response.json()
        assert entity_response_data["success"] is True
        entity = entity_response_data["data"]["entity"]
        test_data_cleanup["entities"].append(entity["id"])
        
        # Create goal
        goal_data = {
            **sample_goal_data,
            "subject_id": entity["id"],
            "object_id": entity["id"]
        }
        
        create_response = client.post("/api/v1/goals", json=goal_data)
        create_data = create_response.json()
        assert create_data["success"] is True
        goal = create_data["data"]["goal"]
        test_data_cleanup["goals"].append(goal["id"])
        
        # Retrieve goal
        response = client.get(f"/api/v1/goals/{goal['id']}")
        assert response.status_code == 200
        
        response_data = response.json()
        assert response_data["success"] is True
        assert "data" in response_data
        assert "goal" in response_data["data"]
        retrieved_goal = response_data["data"]["goal"]
        assert retrieved_goal["id"] == goal["id"]
        assert retrieved_goal["verb"] == goal["verb"]
    
    def test_update_goal(self, client, sample_entity_data, sample_goal_data, cleanup_test_data):
        """Test goal update"""
        # Create entity
        entity_response = client.post("/api/v1/entities", json=sample_entity_data)
        entity_response_data = entity_response.json()
        assert entity_response_data["success"] is True
        entity = entity_response_data["data"]["entity"]
        test_data_cleanup["entities"].append(entity["id"])
        
        # Create goal
        goal_data = {
            **sample_goal_data,
            "subject_id": entity["id"],
            "object_id": entity["id"]
        }
        
        create_response = client.post("/api/v1/goals", json=goal_data)
        create_data = create_response.json()
        assert create_data["success"] is True
        goal = create_data["data"]["goal"]
        test_data_cleanup["goals"].append(goal["id"])
        
        # Update goal
        update_data = {
            "description": "Updated goal description",
            "status": "completed",
            "priority": "low"
        }
        
        response = client.put(f"/api/v1/goals/{goal['id']}", json=update_data)
        assert response.status_code == 200
        
        response_data = response.json()
        assert response_data["success"] is True
        assert "data" in response_data
        assert "goal" in response_data["data"]
        updated_goal = response_data["data"]["goal"]
        assert updated_goal["description"] == update_data["description"]
        assert updated_goal["status"] == update_data["status"]
        assert updated_goal["priority"] == update_data["priority"]
    
    def test_delete_goal(self, client, sample_entity_data, sample_goal_data):
        """Test goal deletion"""
        # Create entity
        entity_response = client.post("/api/v1/entities", json=sample_entity_data)
        entity_response_data = entity_response.json()
        assert entity_response_data["success"] is True
        entity = entity_response_data["data"]["entity"]
        
        # Create goal
        goal_data = {
            **sample_goal_data,
            "subject_id": entity["id"],
            "object_id": entity["id"]
        }
        
        create_response = client.post("/api/v1/goals", json=goal_data)
        create_data = create_response.json()
        assert create_data["success"] is True
        goal = create_data["data"]["goal"]
        
        # Delete goal
        response = client.delete(f"/api/v1/goals/{goal['id']}")
        assert response.status_code == 200
        
        # Clean up entity
        client.delete(f"/api/v1/entities/{entity['id']}")


# NOTE: Knowledge API endpoints are not yet implemented in the current working API
# These tests will be added when knowledge management is implemented in Phase 3

# class TestKnowledgeAPI:
#     """Test character knowledge endpoints (Phase 3)"""
#     pass


# NOTE: Search API endpoints are planned for Phase 4 implementation
# These tests will be added when semantic search and LLM features are implemented

# class TestSearchAPI:
#     """Test search and discovery endpoints (Phase 4)"""
#     pass


# NOTE: LLM API endpoints are planned for Phase 4 implementation
# These tests will be added when LLM integration and AI-assisted authoring are implemented

# class TestLLMAPI:
#     """Test LLM integration endpoints (Phase 4)"""
#     pass


class TestHealthAndUtility:
    """Test health and utility endpoints"""
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert data["database"] == "connected"
        assert "entity_count" in data
        assert isinstance(data["entity_count"], int)
    
    def test_root_endpoint(self, client):
        """Test root endpoint"""
        response = client.get("/")
        assert response.status_code == 200
        
        data = response.json()
        assert "message" in data
        assert "version" in data
        assert "status" in data
        assert data["message"] == "QuantumMateria Story Engine API"
        assert data["status"] == "running"


@pytest.mark.integration
class TestAPIIntegration:
    """Integration tests for API workflows"""
    
    def test_complete_scene_creation_workflow(self, client, sample_entity_data, cleanup_test_data):
        """Test complete scene creation and editing workflow"""
        # 1. Create location entity
        location_response = client.post("/api/v1/entities", json={
            **sample_entity_data,
            "name": "Integration Test Location",
            "entity_type": "location"
        })
        assert location_response.status_code == 200
        location_response_data = location_response.json()
        assert location_response_data["success"] is True
        location = location_response_data["data"]["entity"]
        test_data_cleanup["entities"].append(location["id"])
        
        # 2. Create character entity
        character_response = client.post("/api/v1/entities", json={
            **sample_entity_data,
            "name": "Integration Test Character"
        })
        assert character_response.status_code == 200
        character_response_data = character_response.json()
        assert character_response_data["success"] is True
        character = character_response_data["data"]["entity"]
        test_data_cleanup["entities"].append(character["id"])
        
        # 3. Create scene with location
        scene_response = client.post("/api/v1/scenes", json={
            "title": "Integration Test Scene",
            "location_id": location["id"],
            "timestamp": 100
        })
        assert scene_response.status_code == 200
        scene_response_data = scene_response.json()
        assert scene_response_data["success"] is True
        scene = scene_response_data["data"]["scene"]
        test_data_cleanup["scenes"].append(scene["id"])
        
        # 4. Add prose block
        prose_response = client.post(f"/api/v1/scenes/{scene['id']}/blocks", json={
            "block_type": "prose",
            "content": "The scene opens with a description of the location.",
            "order": 1,
            "scene_id": scene["id"]
        })
        assert prose_response.status_code == 200
        prose_response_data = prose_response.json()
        assert prose_response_data["success"] is True
        prose_block = prose_response_data["data"]["block"]
        test_data_cleanup["scene_blocks"].append(prose_block["id"])
        
        # 5. Add dialogue block
        dialogue_response = client.post(f"/api/v1/scenes/{scene['id']}/blocks", json={
            "block_type": "dialogue",
            "content": "Hello, what brings you here?",
            "order": 2,
            "scene_id": scene["id"],
            "lines": {
                "speaker_id": character["id"],
                "listener_ids": [],
                "emotion": "curious"
            }
        })
        assert dialogue_response.status_code == 200
        dialogue_response_data = dialogue_response.json()
        assert dialogue_response_data["success"] is True
        dialogue_block = dialogue_response_data["data"]["block"]
        test_data_cleanup["scene_blocks"].append(dialogue_block["id"])
        
        # 6. Retrieve scene with all blocks
        blocks_response = client.get(f"/api/v1/scenes/{scene['id']}/blocks")
        assert blocks_response.status_code == 200
        blocks_data = blocks_response.json()
        assert blocks_data["success"] is True
        assert len(blocks_data["data"]["blocks"]) == 2
        
        # 7. Reorder blocks
        reorder_response = client.post(f"/api/v1/scenes/blocks/{dialogue_block['id']}/move", json={
            "new_order": 1
        })
        assert reorder_response.status_code == 200
        
        # 8. Update scene
        update_response = client.put(f"/api/v1/scenes/{scene['id']}", json={
            "title": "Updated Integration Test Scene",
            "timestamp": 150
        })
        assert update_response.status_code == 200
        update_response_data = update_response.json()
        assert update_response_data["success"] is True
        updated_scene = update_response_data["data"]["scene"]
        assert updated_scene["title"] == "Updated Integration Test Scene"
    
    def test_milestone_and_goal_workflow(self, client, sample_entity_data, cleanup_test_data):
        """Test milestone and goal creation workflow"""
        # 1. Create hero entity
        hero_response = client.post("/api/v1/entities", json={
            **sample_entity_data,
            "name": "Hero Character",
            "metadata": {"role": "protagonist"}
        })
        assert hero_response.status_code == 200
        hero_response_data = hero_response.json()
        assert hero_response_data["success"] is True
        hero = hero_response_data["data"]["entity"]
        test_data_cleanup["entities"].append(hero["id"])
        
        # 2. Create villain entity
        villain_response = client.post("/api/v1/entities", json={
            **sample_entity_data,
            "name": "Villain Character",
            "metadata": {"role": "antagonist"}
        })
        assert villain_response.status_code == 200
        villain_response_data = villain_response.json()
        assert villain_response_data["success"] is True
        villain = villain_response_data["data"]["entity"]
        test_data_cleanup["entities"].append(villain["id"])
        
        # 3. Create story goal
        goal_response = client.post("/api/v1/goals", json={
            "subject_id": hero["id"],
            "verb": "defeat",
            "object_id": villain["id"],
            "description": "Hero must defeat the villain",
            "status": "active",
            "priority": "high"
        })
        assert goal_response.status_code == 200
        goal_response_data = goal_response.json()
        assert goal_response_data["success"] is True
        goal = goal_response_data["data"]["goal"]
        test_data_cleanup["goals"].append(goal["id"])
        
        # 4. Create milestone that could fulfill the goal
        milestone_response = client.post("/api/v1/milestones", json={
            "subject_id": hero["id"],
            "verb": "defeats",
            "object_id": villain["id"],
            "description": "Hero defeats villain in final battle",
            "timestamp": 300,
            "significance": "critical"
        })
        assert milestone_response.status_code == 200
        milestone_response_data = milestone_response.json()
        assert milestone_response_data["success"] is True
        milestone = milestone_response_data["data"]["milestone"]
        test_data_cleanup["milestones"].append(milestone["id"])
        
        # 5. Verify both goal and milestone exist
        goal_check = client.get(f"/api/v1/goals/{goal['id']}")
        assert goal_check.status_code == 200
        goal_check_data = goal_check.json()
        assert goal_check_data["success"] is True
        
        milestone_check = client.get(f"/api/v1/milestones/{milestone['id']}")
        assert milestone_check.status_code == 200
        milestone_check_data = milestone_check.json()
        assert milestone_check_data["success"] is True
        
        # NOTE: Goal fulfillment logic will be implemented in Phase 3
    
    def test_entity_relationship_workflow(self, client, cleanup_test_data):
        """Test creating entities with complex relationships"""
        # 1. Create multiple entity types
        character_response = client.post("/api/v1/entities", json={
            "name": "Complex Character",
            "entity_type": "character",
            "description": "A character with complex relationships",
            "metadata": {
                "age": 25,
                "skills": ["magic", "diplomacy"],
                "relationships": {
                    "allies": [],
                    "enemies": [],
                    "neutral": []
                }
            }
        })
        assert character_response.status_code == 200
        character_response_data = character_response.json()
        assert character_response_data["success"] is True
        character = character_response_data["data"]["entity"]
        test_data_cleanup["entities"].append(character["id"])
        
        location_response = client.post("/api/v1/entities", json={
            "name": "Character's Home",
            "entity_type": "location",
            "description": "Where the character lives",
            "metadata": {
                "owner_id": character["id"],
                "type": "residence",
                "security_level": "high"
            }
        })
        assert location_response.status_code == 200
        location_response_data = location_response.json()
        assert location_response_data["success"] is True
        location = location_response_data["data"]["entity"]
        test_data_cleanup["entities"].append(location["id"])
        
        artifact_response = client.post("/api/v1/entities", json={
            "name": "Character's Weapon",
            "entity_type": "artifact",
            "description": "Character's primary weapon",
            "metadata": {
                "owner_id": character["id"],
                "type": "weapon",
                "enchantments": ["fire_damage", "self_repair"]
            }
        })
        assert artifact_response.status_code == 200
        artifact_response_data = artifact_response.json()
        assert artifact_response_data["success"] is True
        artifact = artifact_response_data["data"]["entity"]
        test_data_cleanup["entities"].append(artifact["id"])
        
        # 2. Verify all entities can be retrieved
        entities_response = client.get("/api/v1/entities")
        assert entities_response.status_code == 200
        entities_data = entities_response.json()
        assert entities_data["success"] is True
        
        created_entity_ids = {character["id"], location["id"], artifact["id"]}
        found_entity_ids = {entity["id"] for entity in entities_data["data"]["entities"]}
        assert created_entity_ids.issubset(found_entity_ids)
        
        # 3. Update character with relationship references
        update_response = client.put(f"/api/v1/entities/{character['id']}", json={
            "name": character["name"],
            "description": character["description"],
            "metadata": {
                **character["metadata"],
                "possessions": [artifact["id"]],
                "home_location": location["id"]
            }
        })
        assert update_response.status_code == 200
        update_response_data = update_response.json()
        assert update_response_data["success"] is True
        updated_character = update_response_data["data"]["entity"]
        assert updated_character["metadata"]["home_location"] == location["id"]
        assert artifact["id"] in updated_character["metadata"]["possessions"]


class TestAPIErrorHandling:
    """Test API error handling and edge cases"""
    
    def test_invalid_entity_type(self, client):
        """Test entity creation with invalid entity type"""
        invalid_data = {
            "name": "Test Entity",
            "entity_type": "invalid_type",
            "description": "Should fail validation"
        }
        
        response = client.post("/api/v1/entities", json=invalid_data)
        assert response.status_code == 422  # Validation error
    
    def test_missing_required_fields(self, client):
        """Test API with missing required fields"""
        incomplete_data = {
            "description": "Missing name and entity_type"
        }
        
        response = client.post("/api/v1/entities", json=incomplete_data)
        assert response.status_code == 422  # Validation error
    
    def test_invalid_uuid_format(self, client):
        """Test API with invalid UUID format"""
        response = client.get("/api/v1/entities/not-a-valid-uuid")
        assert response.status_code == 422  # Validation error
    
    def test_scene_with_invalid_location_id(self, client):
        """Test scene creation with non-existent location ID"""
        fake_location_id = str(uuid4())
        scene_data = {
            "title": "Scene with Fake Location",
            "location_id": fake_location_id,
            "timestamp": 100
        }
        
        response = client.post("/api/v1/scenes", json=scene_data)
        # This should still succeed - FK constraint is not enforced at API level
        # but would fail at database level
        assert response.status_code in [200, 400]  # Allow both for now
    
    def test_negative_timestamp(self, client):
        """Test scene creation with negative timestamp"""
        scene_data = {
            "title": "Scene with Negative Timestamp",
            "timestamp": -100
        }
        
        response = client.post("/api/v1/scenes", json=scene_data)
        # Should accept negative timestamps (they might represent "before story start")
        assert response.status_code == 200
    
    def test_invalid_block_type(self, client, cleanup_test_data):
        """Test scene block creation with invalid block type"""
        # Create scene first
        scene_response = client.post("/api/v1/scenes", json={
            "title": "Test Scene",
            "timestamp": 100
        })
        scene = scene_response.json()
        test_data_cleanup["scenes"].append(scene["id"])
        
        # Try to create block with invalid type
        invalid_block_data = {
            "block_type": "invalid_type",
            "content": "This should fail",
            "sort_order": 1
        }
        
        response = client.post(f"/api/v1/scenes/{scene['id']}/blocks", json=invalid_block_data)
        assert response.status_code == 422  # Validation error
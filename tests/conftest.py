"""Pytest configuration and fixtures"""

import pytest
import asyncio
import uuid
from typing import AsyncGenerator, Dict, Any
from fastapi.testclient import TestClient
from datetime import datetime

import os
from dotenv import load_dotenv
from supabase import create_client, Client

# Load environment variables
load_dotenv()

# Import working FastAPI app
from app.main import app
from app.services.database import get_db


# Test configuration
TEST_DB_PREFIX = "test_"
TEST_UUID_NAMESPACE = uuid.uuid4()  # Consistent UUIDs for tests

# Test data cleanup tracking
test_data_cleanup = {
    "entities": [],
    "scenes": [],
    "milestones": [],
    "goals": [],
    "scene_blocks": [],
    "relationships": []
}


def extract_api_data(response_json):
    """
    Extract data from standardized API response format for test compatibility.
    
    Handles both old format and new standardized format:
    Old: {"entities": [...], "count": N}
    New: {"success": true, "data": {"entities": [...], "count": N}}
    """
    if "success" in response_json and "data" in response_json:
        # New standardized format
        data = response_json["data"]
        if isinstance(data, dict):
            return data
        else:
            # Single item response like {"success": true, "data": {"entity": {...}}}
            return data
    else:
        # Old format - return as-is
        return response_json


@pytest.fixture
def supabase_client():
    """Create Supabase client for testing"""
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    
    if not url or not key:
        pytest.skip("SUPABASE_URL and SUPABASE_KEY required for database tests")
    
    client: Client = create_client(url, key)
    return client


@pytest.fixture
def client():
    """Create FastAPI test client"""
    return TestClient(app)


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def test_engine():
    """Create test database engine with in-memory SQLite"""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    return engine


@pytest.fixture
def test_session(test_engine):
    """Create test database session"""
    # TODO: Create tables in test database
    # This will be implemented by rapid-prototyper agent
    # For now, return mock session
    
    session = Session(test_engine)
    yield session
    session.close()


@pytest.fixture(scope="function")
def cleanup_test_data(supabase_client):
    """Cleanup test data after each test"""
    yield
    
    # Clean up test data in reverse dependency order
    try:
        # Clean scene blocks first
        for block_id in test_data_cleanup["scene_blocks"]:
            supabase_client.table("scene_blocks").delete().eq("id", block_id).execute()
        
        # Clean scenes
        for scene_id in test_data_cleanup["scenes"]:
            supabase_client.table("scenes").delete().eq("id", scene_id).execute()
        
        # Clean milestones
        for milestone_id in test_data_cleanup["milestones"]:
            supabase_client.table("milestones").delete().eq("id", milestone_id).execute()
        
        # Clean goals
        for goal_id in test_data_cleanup["goals"]:
            supabase_client.table("story_goals").delete().eq("id", goal_id).execute()
        
        # Clean relationships
        for relationship_id in test_data_cleanup["relationships"]:
            supabase_client.table("relationships").delete().eq("id", relationship_id).execute()
        
        # Clean entities last
        for entity_id in test_data_cleanup["entities"]:
            supabase_client.table("entities").delete().eq("id", entity_id).execute()
            
    except Exception as e:
        print(f"Warning: Test cleanup failed: {e}")
    
    # Reset cleanup tracking
    for key in test_data_cleanup:
        test_data_cleanup[key].clear()


# Database fixtures
@pytest.fixture
def sample_entity_data():
    """Sample entity data for testing"""
    return {
        "name": "Test Character",
        "entity_type": "character",
        "description": "A test character for unit testing",
        "meta": {
            "role": "protagonist",
            "age": 25,
            "skills": ["sword fighting", "magic"]
        }
    }


@pytest.fixture
def sample_location_data():
    """Sample location entity data for testing"""
    return {
        "name": "Test Castle",
        "entity_type": "location",
        "description": "A mysterious castle for testing",
        "meta": {
            "region": "north",
            "climate": "cold",
            "inhabitants": ["guards", "servants"]
        }
    }


@pytest.fixture
def sample_artifact_data():
    """Sample artifact entity data for testing"""
    return {
        "name": "Test Sword",
        "entity_type": "artifact",
        "description": "A magical sword for testing",
        "meta": {
            "material": "enchanted steel",
            "power_level": 8,
            "abilities": ["fire_damage", "light_emission"]
        }
    }


@pytest.fixture
def sample_scene_data():
    """Sample scene data for testing"""
    return {
        "title": "Test Scene",
        "location_id": None,  # Will be set to actual location ID in tests
        "timestamp": 100  # INT timestamp as per new schema
    }


@pytest.fixture
def sample_prose_block_data():
    """Sample prose block data for testing"""
    return {
        "block_type": "prose",
        "content": "This is test prose content describing the scene.",
        "order": 1
        # Note: scene_id will be added in tests
    }


@pytest.fixture
def sample_dialogue_block_data():
    """Sample dialogue block data for testing"""
    return {
        "block_type": "dialogue",
        "content": "Hello, how are you today?",
        "order": 2,
        "lines": {
            "speaker_id": None,  # Will be set to actual character ID in tests
            "listener_ids": [],  # Will be set to actual character IDs in tests
            "emotion": "friendly"
        }
        # Note: scene_id will be added in tests
    }


@pytest.fixture
def sample_milestone_block_data():
    """Sample milestone block data for testing"""
    return {
        "block_type": "milestone",
        "content": "The hero obtains the magical sword.",
        "order": 3,
        "subject_id": None,  # Will be set to actual entity ID in tests
        "verb": "obtains",
        "object_id": None    # Will be set to actual entity ID in tests
        # Note: scene_id will be added in tests
    }


@pytest.fixture
def sample_milestone_data():
    """Sample milestone data for testing (first-class entity)"""
    return {
        "subject_id": None,  # Will be set to actual entity ID
        "verb": "defeats",
        "object_id": None,   # Will be set to actual entity ID
        "description": "The hero defeats the villain",
        "timestamp": 200,
        "significance": "major"
    }


@pytest.fixture
def sample_goal_data():
    """Sample story goal data for testing"""
    return {
        "subject_id": None,  # Will be set to actual entity ID in tests
        "verb": "rescue",
        "object_id": None,   # Will be set to actual entity ID in tests
        "description": "Test goal for unit testing",
        "status": "active",
        "priority": "high"
    }


@pytest.fixture
def sample_knowledge_data():
    """Sample knowledge assertion data for testing"""
    return {
        "character_id": None,  # Will be set to actual character ID in tests
        "predicate": "knows",
        "fact_subject": "the villain",
        "fact_verb": "lives in",
        "fact_object": "the castle",
        "timestamp": 150,  # INT timestamp
        "certainty": "true",
        "source": "direct_observation"
    }

@pytest.fixture
def sample_relationship_data():
    """Sample relationship data for testing"""
    return {
        "source_id": None,  # Will be set to actual entity ID in tests
        "target_id": None,  # Will be set to actual entity ID in tests
        "relation_type": "friends_with",
        "weight": 0.8,
        "starts_at": 100,
        "ends_at": 500,
        "meta": {"intensity": "high"}
    }


@pytest.fixture
def sample_entities(client, cleanup_test_data):
    """Create sample entities for relationship testing"""
    entities = []
    
    # Create first entity
    entity1_data = {
        "name": "Alice",
        "entity_type": "character",
        "description": "First test character"
    }
    response = client.post("/api/v1/entities", json=entity1_data)
    if response.status_code == 200:
        entity1 = response.json()["data"]["entity"]
        entities.append(entity1)
        test_data_cleanup["entities"].append(entity1["id"])
    
    # Create second entity
    entity2_data = {
        "name": "Bob", 
        "entity_type": "character",
        "description": "Second test character"
    }
    response = client.post("/api/v1/entities", json=entity2_data)
    if response.status_code == 200:
        entity2 = response.json()["data"]["entity"]
        entities.append(entity2)
        test_data_cleanup["entities"].append(entity2["id"])
    
    return entities


@pytest.fixture
def sample_relationship(client, sample_entities, cleanup_test_data):
    """Create a sample relationship for testing"""
    if len(sample_entities) < 2:
        pytest.skip("Need at least 2 entities for relationship tests")
    
    relationship_data = {
        "source_id": sample_entities[0]["id"],
        "target_id": sample_entities[1]["id"],
        "relation_type": "friends_with",
        "weight": 0.8,
        "starts_at": 100,
        "ends_at": 500,
        "meta": {"intensity": "high"}
    }
    
    response = client.post("/api/v1/relationships/", json=relationship_data)
    if response.status_code == 200:
        relationship = response.json()["data"]
        test_data_cleanup.setdefault("relationships", []).append(relationship["id"])
        return relationship
    return None


@pytest.fixture  
def sample_temporal_relationships(client, sample_entities, cleanup_test_data):
    """Create temporal relationships for testing temporal queries"""
    if len(sample_entities) < 2:
        pytest.skip("Need at least 2 entities for relationship tests")
    
    entity_id = sample_entities[0]["id"]
    target_id = sample_entities[1]["id"]
    
    # Create a relationship with temporal bounds (200-400)
    relationship_data = {
        "source_id": entity_id,
        "target_id": target_id,
        "relation_type": "temporal_test",
        "weight": 0.7,
        "starts_at": 200,
        "ends_at": 400,
        "meta": {"test": "temporal"}
    }
    
    response = client.post("/api/v1/relationships/", json=relationship_data)
    if response.status_code == 200:
        relationship = response.json()["data"]
        test_data_cleanup.setdefault("relationships", []).append(relationship["id"])
        
        return {
            "relationship": relationship,
            "entity_id": entity_id,
            "target_id": target_id
        }
    return None


# Integration test fixtures
@pytest.fixture
def test_entities(client, supabase_client, sample_entity_data, sample_location_data, sample_artifact_data, cleanup_test_data):
    """Create test entities for integration tests"""
    entities = {}
    
    # Create character
    response = client.post("/api/v1/entities", json=sample_entity_data)
    if response.status_code == 200:
        character = response.json()
        entities["character"] = character
        test_data_cleanup["entities"].append(character["id"])
    
    # Create location  
    response = client.post("/api/v1/entities", json=sample_location_data)
    if response.status_code == 200:
        location = response.json()
        entities["location"] = location
        test_data_cleanup["entities"].append(location["id"])
    
    # Create artifact
    response = client.post("/api/v1/entities", json=sample_artifact_data)
    if response.status_code == 200:
        artifact = response.json()
        entities["artifact"] = artifact
        test_data_cleanup["entities"].append(artifact["id"])
    
    return entities


@pytest.fixture
def test_scene(client, test_entities, cleanup_test_data):
    """Create test scene with location"""
    scene_data = {
        "title": "Integration Test Scene",
        "location_id": test_entities["location"]["id"] if "location" in test_entities else None,
        "timestamp": 100
    }
    
    response = client.post("/api/v1/scenes", json=scene_data)
    if response.status_code == 200:
        scene = response.json()
        test_data_cleanup["scenes"].append(scene["id"])
        return scene
    return None


# Mock fixtures for external services
@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing"""
    class MockOpenAIClient:
        def embeddings_create(self, **kwargs):
            return {
                "data": [{"embedding": [0.1] * 1536}]  # Mock embedding vector
            }
    
    return MockOpenAIClient()


@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client for testing"""
    class MockSupabaseClient:
        def table(self, table_name):
            return MockTable()
    
    class MockTable:
        def select(self, *args, **kwargs):
            return self
        
        def insert(self, data):
            return MockResult([{**data, "id": "test-id"}])
        
        def update(self, data):
            return self
        
        def delete(self):
            return self
        
        def eq(self, column, value):
            return self
        
        def execute(self):
            return MockResult([])
    
    class MockResult:
        def __init__(self, data):
            self.data = data
            self.count = len(data)
    
    return MockSupabaseClient()


# Pytest configuration
def pytest_configure(config):
    """Configure pytest"""
    config.addinivalue_line(
        "markers", "integration: mark test as integration test"
    )
    config.addinivalue_line(
        "markers", "unit: mark test as unit test"
    )
    config.addinivalue_line(
        "markers", "slow: mark test as slow running"
    )
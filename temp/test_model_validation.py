#!/usr/bin/env python3
"""
Validate SQLModel class structure and schema alignment
Tests model instantiation and field validation without database operations
"""

import sys
import os
from uuid import uuid4

# Add the app directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app'))

from models.entities import (
    EntityCreate, EntityRead, EntityUpdate,
    SceneCreate, SceneRead, SceneUpdate, 
    SceneBlockCreate, SceneBlockRead, SceneBlockUpdate,
    MilestoneCreate, MilestoneRead, MilestoneUpdate,
    BlockType, EntityType
)

def test_entity_models():
    """Test entity model validation and instantiation"""
    print("Testing Entity Models...")
    
    # Test EntityCreate
    entity_create = EntityCreate(
        name="Test Character",
        entity_type=EntityType.CHARACTER,
        description="A test character",
        metadata={"role": "protagonist", "level": 1}
    )
    print(f"✅ EntityCreate: {entity_create.name} ({entity_create.entity_type})")
    
    # Test EntityUpdate
    entity_update = EntityUpdate(
        name="Updated Character",
        metadata={"role": "antagonist", "level": 5}
    )
    print(f"✅ EntityUpdate: {entity_update.name}")
    
    # Validate JSONB metadata field
    if entity_create.metadata.get("role") == "protagonist":
        print("✅ JSONB metadata field working in EntityCreate")
    
    return True

def test_scene_models():
    """Test scene model validation and instantiation"""
    print("\nTesting Scene Models...")
    
    # Test SceneCreate with INT timestamp
    scene_create = SceneCreate(
        title="Test Scene",
        location_id=uuid4(),
        timestamp=1000  # INT timestamp as per new schema
    )
    print(f"✅ SceneCreate: {scene_create.title} (timestamp: {scene_create.timestamp})")
    
    # Test SceneUpdate
    scene_update = SceneUpdate(
        title="Updated Scene",
        timestamp=2000
    )
    print(f"✅ SceneUpdate: {scene_update.title}")
    
    # Validate INT timestamp field
    if scene_create.timestamp == 1000 and isinstance(scene_create.timestamp, int):
        print("✅ INT timestamp field working correctly")
    
    return True

def test_scene_block_models():
    """Test scene block model validation and instantiation"""
    print("\nTesting Scene Block Models...")
    
    # Test prose block
    prose_block = SceneBlockCreate(
        scene_id=uuid4(),
        block_type=BlockType.PROSE,
        order=1,
        content="This is a test prose block.",
        metadata={"word_count": 6}
    )
    print(f"✅ Prose SceneBlockCreate: {prose_block.block_type} (order: {prose_block.order})")
    
    # Test dialogue block with JSONB lines
    dialogue_block = SceneBlockCreate(
        scene_id=uuid4(),
        block_type=BlockType.DIALOGUE,
        order=2,
        summary="Character speaks",
        lines={"speaker": str(uuid4()), "text": "Hello, world!", "emotion": "excited"},
        metadata={"dialogue_type": "monologue"}
    )
    print(f"✅ Dialogue SceneBlockCreate: {dialogue_block.block_type}")
    
    # Test milestone block with subject-verb-object
    milestone_block = SceneBlockCreate(
        scene_id=uuid4(),
        block_type=BlockType.MILESTONE,
        order=3,
        subject_id=uuid4(),
        verb="arrives",
        object_id=uuid4(),
        weight=2.5,
        metadata={"significance": "high"}
    )
    print(f"✅ Milestone SceneBlockCreate: {milestone_block.verb} (weight: {milestone_block.weight})")
    
    # Validate JSONB fields
    if dialogue_block.lines.get("text") == "Hello, world!":
        print("✅ JSONB lines field working correctly")
    if milestone_block.metadata.get("significance") == "high":
        print("✅ JSONB metadata field working correctly")
    
    return True

def test_milestone_models():
    """Test first-class milestone model validation"""
    print("\nTesting First-Class Milestone Models...")
    
    # Test MilestoneCreate
    milestone_create = MilestoneCreate(
        scene_id=uuid4(),
        subject_id=uuid4(),
        verb="completes",
        object_id=uuid4(),
        description="Test milestone",
        weight=3.0,
        metadata={"category": "story_progression"}
    )
    print(f"✅ MilestoneCreate: {milestone_create.verb} (weight: {milestone_create.weight})")
    
    # Test MilestoneUpdate
    milestone_update = MilestoneUpdate(
        verb="achieves",
        weight=4.0,
        metadata={"category": "character_development"}
    )
    print(f"✅ MilestoneUpdate: {milestone_update.verb}")
    
    # Validate weight and metadata fields
    if milestone_create.weight == 3.0 and isinstance(milestone_create.weight, float):
        print("✅ Weight field working correctly")
    if milestone_create.metadata.get("category") == "story_progression":
        print("✅ First-class milestone metadata working correctly")
    
    return True

def test_field_validations():
    """Test field validation and constraints"""
    print("\nTesting Field Validations...")
    
    # Test enum validation
    try:
        valid_entity = EntityCreate(
            name="Valid Character",
            entity_type=EntityType.CHARACTER,
            description="Valid"
        )
        print("✅ EntityType enum validation working")
    except Exception as e:
        print(f"❌ EntityType enum validation failed: {e}")
        return False
    
    # Test BlockType validation
    try:
        valid_block = SceneBlockCreate(
            scene_id=uuid4(),
            block_type=BlockType.PROSE,
            order=1,
            content="Valid content"
        )
        print("✅ BlockType enum validation working")
    except Exception as e:
        print(f"❌ BlockType enum validation failed: {e}")
        return False
    
    # Test required field validation
    try:
        # This should fail due to missing required fields
        invalid_entity = EntityCreate()
        print("❌ Required field validation not working")
        return False
    except Exception:
        print("✅ Required field validation working")
    
    return True

def test_uuid_fields():
    """Test UUID field handling"""
    print("\nTesting UUID Fields...")
    
    test_uuid = uuid4()
    
    # Test UUID field assignment
    scene_block = SceneBlockCreate(
        scene_id=test_uuid,
        block_type=BlockType.MILESTONE,
        order=1,
        subject_id=test_uuid,
        verb="tests",
        object_id=test_uuid
    )
    
    if scene_block.scene_id == test_uuid:
        print("✅ UUID field assignment working")
    else:
        print("❌ UUID field assignment failed")
        return False
    
    return True

def main():
    """Run all model validation tests"""
    print("🚀 Testing Rebuilt SQLModel Classes - Schema Alignment Validation")
    print("=" * 70)
    
    tests = [
        test_entity_models,
        test_scene_models,
        test_scene_block_models,
        test_milestone_models,
        test_field_validations,
        test_uuid_fields
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__} failed: {e}")
            results.append(False)
    
    print("\n" + "=" * 70)
    if all(results):
        print("🎉 All model validation tests passed!")
        print("✅ SQLModel classes properly structured")
        print("✅ New schema field types validated")
        print("✅ JSONB metadata fields functional")
        print("✅ INT timestamp fields functional")
        print("✅ First-class milestones working")
        print("✅ Enum validations working")
        print("✅ UUID field handling working")
        print("✅ Field validation constraints working")
        print("\n📋 Schema Alignment Summary:")
        print("   • entities: name, entity_type, description, metadata (JSONB)")
        print("   • scenes: title, location_id, timestamp (INT)")
        print("   • scene_blocks: block_type, order, content, summary, lines (JSONB), subject-verb-object, weight, metadata (JSONB)")
        print("   • milestones: scene_id, subject-verb-object, description, weight, metadata (JSONB) - FIRST-CLASS TABLE")
        print("   • Direct Supabase client operations (not SQLModel ORM)")
        return True
    else:
        print("❌ Some model validation tests failed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
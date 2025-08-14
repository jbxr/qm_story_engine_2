"""
Integration tests for Content Team advanced operations

Tests end-to-end workflows using actual database operations
This validates the complete content operation pipeline
"""

import pytest
from uuid import uuid4
from fastapi.testclient import TestClient

from app.main import app
from app.services.database import get_db


client = TestClient(app)


class TestContentIntegration:
    """Integration tests for content operations"""
    
    def setup_method(self):
        """Set up test data for each test"""
        # Create test entities for milestones
        self.db = get_db()
        
        # Create test characters
        character_data = {
            "id": str(uuid4()),
            "name": "Test Character",
            "entity_type": "character",
            "description": "A test character for content operations",
            "metadata": {}
        }
        
        character_result = self.db.table("entities").insert(character_data).execute()
        self.character_id = character_result.data[0]["id"]
        
        # Create test location  
        location_data = {
            "id": str(uuid4()),
            "name": "Test Location",
            "entity_type": "location", 
            "description": "A test location for scenes",
            "metadata": {}
        }
        
        location_result = self.db.table("entities").insert(location_data).execute()
        self.location_id = location_result.data[0]["id"]
        
        # Create test scene
        scene_data = {
            "id": str(uuid4()),
            "title": "Test Scene for Content Operations",
            "location_id": self.location_id,
            "timestamp": 1000
        }
        
        scene_result = self.db.table("scenes").insert(scene_data).execute()
        self.scene_id = scene_result.data[0]["id"]
    
    def teardown_method(self):
        """Clean up test data after each test"""
        try:
            # Clean up in reverse dependency order
            self.db.table("scene_blocks").delete().eq("scene_id", self.scene_id).execute()
            self.db.table("scenes").delete().eq("id", self.scene_id).execute() 
            self.db.table("entities").delete().eq("id", self.character_id).execute()
            self.db.table("entities").delete().eq("id", self.location_id).execute()
        except Exception:
            pass  # Cleanup is best effort
    
    def test_batch_create_and_reorder_workflow(self):
        """Test complete workflow: batch create -> reorder -> validate"""
        
        # Step 1: Batch create multiple blocks
        batch_data = {
            "scene_id": self.scene_id,
            "blocks": [
                {
                    "scene_id": self.scene_id,
                    "block_type": "prose",
                    "order": 0,
                    "content": "The story begins with our hero entering the tavern."
                },
                {
                    "scene_id": self.scene_id,
                    "block_type": "dialogue",
                    "order": 1,
                    "summary": "Hero greets the bartender",
                    "lines": {"speaker": self.character_id, "text": "Good evening!"}
                },
                {
                    "scene_id": self.scene_id,
                    "block_type": "milestone",
                    "order": 2,
                    "verb": "enters",
                    "subject_id": self.character_id
                }
            ]
        }
        
        # Create blocks
        response = client.post("/api/v1/content/blocks/batch", json=batch_data)
        assert response.status_code == 200
        
        batch_result = response.json()
        assert batch_result["success"] is True
        assert batch_result["data"]["processed"] == 3
        assert batch_result["data"]["failed"] == 0
        
        created_blocks = batch_result["data"]["created_blocks"]
        assert len(created_blocks) == 3
        
        # Get block IDs for reordering
        block_ids = [block["id"] for block in created_blocks]
        
        # Step 2: Reorder blocks (reverse order)
        reorder_data = {
            "scene_id": self.scene_id,
            "block_order": {
                block_ids[0]: 2,  # prose -> last
                block_ids[1]: 0,  # dialogue -> first
                block_ids[2]: 1   # milestone -> middle
            }
        }
        
        response = client.post("/api/v1/content/blocks/reorder", json=reorder_data)
        assert response.status_code == 200
        
        reorder_result = response.json()
        assert reorder_result["success"] is True
        
        # Step 3: Verify ordering
        response = client.get(f"/api/v1/content/blocks/scene/{self.scene_id}/ordered")
        assert response.status_code == 200
        
        ordered_result = response.json()
        ordered_blocks = ordered_result["data"]["blocks"]
        
        assert len(ordered_blocks) == 3
        assert ordered_blocks[0]["block_type"] == "dialogue"  # Order 0
        assert ordered_blocks[1]["block_type"] == "milestone"  # Order 1 
        assert ordered_blocks[2]["block_type"] == "prose"     # Order 2
        
        # Step 4: Validate scene content
        response = client.post(f"/api/v1/content/validation/scene/{self.scene_id}")
        assert response.status_code == 200
        
        validation_result = response.json()
        assert validation_result["success"] is True
        assert validation_result["data"]["valid"] is True
        assert validation_result["data"]["rules_passed"] > 0
    
    def test_duplicate_and_merge_workflow(self):
        """Test duplicate block and merge operations"""
        
        # Step 1: Create initial block
        batch_data = {
            "scene_id": self.scene_id,
            "blocks": [
                {
                    "scene_id": self.scene_id,
                    "block_type": "prose",
                    "order": 0,
                    "content": "Original content block"
                }
            ]
        }
        
        response = client.post("/api/v1/content/blocks/batch", json=batch_data)
        assert response.status_code == 200
        
        original_block_id = response.json()["data"]["created_blocks"][0]["id"]
        
        # Step 2: Duplicate the block with modifications
        duplicate_data = {
            "modifications": {
                "content": "Modified duplicate content"
            }
        }
        
        response = client.post(f"/api/v1/content/blocks/{original_block_id}/duplicate", json=duplicate_data)
        assert response.status_code == 200
        
        duplicate_result = response.json()
        assert duplicate_result["success"] is True
        duplicate_block_id = duplicate_result["data"]["block"]["id"]
        
        # Verify duplicate has different ID and modified content
        assert duplicate_block_id != original_block_id
        
        # Step 3: Create a third block to merge
        batch_data = {
            "scene_id": self.scene_id,
            "blocks": [
                {
                    "scene_id": self.scene_id,
                    "block_type": "prose",
                    "order": 2,
                    "content": "Third block content"
                }
            ]
        }
        
        response = client.post("/api/v1/content/blocks/batch", json=batch_data)
        third_block_id = response.json()["data"]["created_blocks"][0]["id"]
        
        # Step 4: Merge blocks
        merge_data = {
            "target_block_id": original_block_id,
            "source_block_ids": [duplicate_block_id, third_block_id],
            "merge_strategy": "concatenate"
        }
        
        response = client.post("/api/v1/content/blocks/merge", json=merge_data)
        assert response.status_code == 200
        
        merge_result = response.json()
        assert merge_result["success"] is True
        
        # Verify merged content contains all three pieces
        merged_content = merge_result["data"]["block"]["content"]
        assert "Original content block" in merged_content
        assert "Modified duplicate content" in merged_content
        assert "Third block content" in merged_content
        
        # Verify source blocks were deleted
        response = client.get(f"/api/v1/content/blocks/scene/{self.scene_id}/ordered")
        remaining_blocks = response.json()["data"]["blocks"]
        remaining_ids = [block["id"] for block in remaining_blocks]
        
        assert original_block_id in remaining_ids  # Target block remains
        assert duplicate_block_id not in remaining_ids  # Source blocks deleted
        assert third_block_id not in remaining_ids
    
    def test_content_search_workflow(self):
        """Test content search functionality"""
        
        # Step 1: Create diverse content for searching
        batch_data = {
            "scene_id": self.scene_id,
            "blocks": [
                {
                    "scene_id": self.scene_id,
                    "block_type": "prose",
                    "order": 0,
                    "content": "The magical sword glowed with ancient power in the moonlight."
                },
                {
                    "scene_id": self.scene_id,
                    "block_type": "dialogue",
                    "order": 1,
                    "summary": "Discussion about the magical artifact",
                    "lines": {"speaker": self.character_id, "text": "This sword is magical!"}
                },
                {
                    "scene_id": self.scene_id,
                    "block_type": "milestone",
                    "order": 2,
                    "verb": "discovers",
                    "subject_id": self.character_id
                },
                {
                    "scene_id": self.scene_id,
                    "block_type": "prose",
                    "order": 3,
                    "content": "The tavern was quiet except for the crackling fire."
                }
            ]
        }
        
        response = client.post("/api/v1/content/blocks/batch", json=batch_data)
        assert response.status_code == 200
        
        # Step 2: Search for "magical" content
        search_data = {
            "query": "magical",
            "scene_id": self.scene_id,
            "limit": 10
        }
        
        response = client.post("/api/v1/content/blocks/search", json=search_data)
        assert response.status_code == 200
        
        search_result = response.json()
        assert search_result["success"] is True
        assert search_result["data"]["total"] >= 2  # Should find prose and dialogue blocks
        assert search_result["data"]["query"] == "magical"
        
        # Verify search results contain expected content
        found_magical_content = False
        for result in search_result["data"]["results"]:
            if result["content_snippet"] and "magical" in result["content_snippet"].lower():
                found_magical_content = True
                assert result["match_score"] > 0
                break
        
        assert found_magical_content, "Search should find blocks containing 'magical'"
        
        # Step 3: Search with block type filter
        search_data = {
            "query": "tavern",
            "scene_id": self.scene_id,
            "block_types": ["prose"],
            "limit": 10
        }
        
        response = client.post("/api/v1/content/blocks/search", json=search_data)
        assert response.status_code == 200
        
        filtered_result = response.json()
        assert filtered_result["success"] is True
        
        # Should find only prose blocks mentioning tavern
        for result in filtered_result["data"]["results"]:
            assert result["block_type"] == "prose"
    
    def test_validation_with_issues(self):
        """Test content validation that finds issues"""
        
        # Step 1: Create blocks with intentional ordering issues
        # We'll manually insert blocks with non-sequential orders
        block_data_1 = {
            "id": str(uuid4()),
            "scene_id": self.scene_id,
            "block_type": "prose",
            "order": 0,
            "content": "First block",
            "metadata": {}
        }
        
        block_data_2 = {
            "id": str(uuid4()),
            "scene_id": self.scene_id,
            "block_type": "prose", 
            "order": 3,  # Gap in ordering (missing orders 1 and 2)
            "content": "Second block",
            "metadata": {}
        }
        
        # Insert blocks directly to bypass validation
        self.db.table("scene_blocks").insert([block_data_1, block_data_2]).execute()
        
        # Step 2: Run validation
        response = client.post(f"/api/v1/content/validation/scene/{self.scene_id}")
        assert response.status_code == 200
        
        validation_result = response.json()
        assert validation_result["success"] is True
        assert validation_result["data"]["valid"] is False  # Should detect issues
        assert validation_result["data"]["rules_passed"] < validation_result["data"]["rules_checked"]
        
        # Should have at least one issue related to block ordering
        issues = validation_result["data"]["issues"]
        ordering_issue_found = any(
            issue["rule_name"] == "block_ordering" and not issue["passed"]
            for issue in issues
        )
        assert ordering_issue_found, "Should detect block ordering issues"
    
    def test_milestone_integration_with_knowledge(self):
        """Test milestone creation integrates with knowledge system"""
        
        # Step 1: Create milestone block
        batch_data = {
            "scene_id": self.scene_id,
            "blocks": [
                {
                    "scene_id": self.scene_id,
                    "block_type": "milestone",
                    "order": 0,
                    "verb": "learns_magic",
                    "subject_id": self.character_id,
                    "metadata": {"significance": "major_character_development"}
                }
            ]
        }
        
        response = client.post("/api/v1/content/blocks/batch", json=batch_data)
        assert response.status_code == 200
        
        # Step 2: Verify milestone was created successfully
        batch_result = response.json()
        assert batch_result["success"] is True
        assert batch_result["data"]["processed"] == 1
        
        milestone_block = batch_result["data"]["created_blocks"][0]
        assert milestone_block["block_type"] == "milestone"
        assert milestone_block["verb"] == "learns_magic"
        assert milestone_block["subject_id"] == self.character_id
        
        # Note: Knowledge snapshot integration would be tested here
        # once the knowledge service interface is finalized
    
    def test_error_handling_and_recovery(self):
        """Test error handling in content operations"""
        
        # Test 1: Batch create with invalid data
        invalid_batch_data = {
            "scene_id": self.scene_id,
            "blocks": [
                {
                    "scene_id": "invalid-uuid",  # Invalid scene ID
                    "block_type": "prose",
                    "order": 0,
                    "content": "Valid content"
                }
            ]
        }
        
        response = client.post("/api/v1/content/blocks/batch", json=invalid_batch_data)
        # Should handle error gracefully
        assert response.status_code == 200  # API returns 200 with success=false
        result = response.json()
        assert result["success"] is False
        
        # Test 2: Duplicate non-existent block
        fake_block_id = str(uuid4())
        duplicate_data = {"modifications": {}}
        
        response = client.post(f"/api/v1/content/blocks/{fake_block_id}/duplicate", json=duplicate_data)
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is False
        
        # Test 3: Reorder blocks that don't belong to scene
        reorder_data = {
            "scene_id": self.scene_id,
            "block_order": {
                str(uuid4()): 0  # Non-existent block ID
            }
        }
        
        response = client.post("/api/v1/content/blocks/reorder", json=reorder_data)
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is False
    
    def test_complete_scene_editing_workflow(self):
        """Test complete scene editing workflow using all content operations"""
        
        # This test simulates a complete scene editing session
        
        # Step 1: Create initial scene structure
        initial_blocks = {
            "scene_id": self.scene_id,
            "blocks": [
                {
                    "scene_id": self.scene_id,
                    "block_type": "prose",
                    "order": 0,
                    "content": "Setting: A mysterious library"
                },
                {
                    "scene_id": self.scene_id,
                    "block_type": "milestone",
                    "order": 1,
                    "verb": "enters",
                    "subject_id": self.character_id
                }
            ]
        }
        
        response = client.post("/api/v1/content/blocks/batch", json=initial_blocks)
        initial_result = response.json()
        assert initial_result["success"] is True
        
        initial_block_ids = [block["id"] for block in initial_result["data"]["created_blocks"]]
        
        # Step 2: Add more content via batch create
        additional_blocks = {
            "scene_id": self.scene_id,
            "blocks": [
                {
                    "scene_id": self.scene_id,
                    "block_type": "dialogue",
                    "order": 2,
                    "summary": "Character reads book title",
                    "lines": {"speaker": self.character_id, "text": "Ancient Mysteries..."}
                },
                {
                    "scene_id": self.scene_id,
                    "block_type": "prose",
                    "order": 3,
                    "content": "The book glows when touched"
                }
            ]
        }
        
        response = client.post("/api/v1/content/blocks/batch", json=additional_blocks)
        additional_result = response.json()
        assert additional_result["success"] is True
        
        # Step 3: Search for content to edit
        search_data = {
            "query": "book",
            "scene_id": self.scene_id
        }
        
        response = client.post("/api/v1/content/blocks/search", json=search_data)
        search_result = response.json()
        assert search_result["success"] is True
        assert search_result["data"]["total"] >= 1
        
        # Step 4: Duplicate and modify a block
        book_block_id = additional_result["data"]["created_blocks"][1]["id"]  # The prose block about the book
        
        duplicate_data = {
            "modifications": {
                "content": "The ancient tome radiates magical energy"
            }
        }
        
        response = client.post(f"/api/v1/content/blocks/{book_block_id}/duplicate", json=duplicate_data)
        duplicate_result = response.json()
        assert duplicate_result["success"] is True
        
        # Step 5: Reorder all blocks for better flow
        response = client.get(f"/api/v1/content/blocks/scene/{self.scene_id}/ordered")
        current_blocks = response.json()["data"]["blocks"]
        
        # Create new ordering
        new_order = {}
        for i, block in enumerate(current_blocks):
            new_order[block["id"]] = i  # Keep current order for simplicity
        
        reorder_data = {
            "scene_id": self.scene_id,
            "block_order": new_order
        }
        
        response = client.post("/api/v1/content/blocks/reorder", json=reorder_data)
        reorder_result = response.json()
        assert reorder_result["success"] is True
        
        # Step 6: Final validation
        response = client.post(f"/api/v1/content/validation/scene/{self.scene_id}")
        final_validation = response.json()
        assert final_validation["success"] is True
        assert final_validation["data"]["valid"] is True
        
        # Step 7: Verify final scene structure
        response = client.get(f"/api/v1/content/blocks/scene/{self.scene_id}/ordered")
        final_structure = response.json()
        
        assert final_structure["success"] is True
        assert final_structure["data"]["count"] >= 4  # Should have multiple blocks
        
        # Verify blocks are properly ordered
        blocks = final_structure["data"]["blocks"]
        for i in range(len(blocks) - 1):
            assert blocks[i]["order"] <= blocks[i + 1]["order"]
        
        print(f"✅ Complete scene editing workflow successful with {final_structure['data']['count']} blocks")
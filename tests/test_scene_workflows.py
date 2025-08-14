"""
Test Scene Workflows - End-to-End Integration Tests

Comprehensive workflow testing that validates complete user journeys through the API:
- Scene creation and management workflows
- Scene block creation and ordering workflows  
- Entity relationship workflows
- Milestone and goal workflows
- Complex multi-step story authoring workflows

These tests ensure that all API components work together correctly for real-world usage.
"""

import pytest
from uuid import uuid4
from datetime import datetime

from .conftest import test_data_cleanup


class TestBasicSceneWorkflow:
    """Test basic scene creation and management workflows"""
    
    def test_complete_scene_creation_workflow(self, client, cleanup_test_data):
        """Test the complete scene creation workflow from start to finish"""
        # Step 1: Create a location entity for the scene
        location_data = {
            "name": "Mysterious Castle",
            "entity_type": "location",
            "description": "An ancient castle shrouded in mystery",
            "metadata": {
                "region": "northern mountains",
                "climate": "cold and misty",
                "danger_level": "high"
            }
        }
        
        location_response = client.post("/api/v1/entities", json=location_data)
        assert location_response.status_code == 200
        location_response_data = location_response.json()
        assert location_response_data["success"] is True
        location = location_response_data["data"]["entity"]
        test_data_cleanup["entities"].append(location["id"])
        
        # Step 2: Create characters for the scene
        hero_data = {
            "name": "Sir Galahad",
            "entity_type": "character", 
            "description": "A brave knight on a quest",
            "metadata": {
                "role": "protagonist",
                "class": "paladin",
                "level": 10,
                "equipment": ["enchanted sword", "holy armor"]
            }
        }
        
        hero_response = client.post("/api/v1/entities", json=hero_data)
        assert hero_response.status_code == 200
        hero_response_data = hero_response.json()
        assert hero_response_data["success"] is True
        hero = hero_response_data["data"]["entity"]
        test_data_cleanup["entities"].append(hero["id"])
        
        companion_data = {
            "name": "Merlin the Wise",
            "entity_type": "character",
            "description": "An ancient wizard and mentor",
            "metadata": {
                "role": "mentor",
                "class": "wizard",
                "specialties": ["divination", "enchantment"],
                "age": 1000
            }
        }
        
        companion_response = client.post("/api/v1/entities", json=companion_data)
        assert companion_response.status_code == 200
        companion_response_data = companion_response.json()
        assert companion_response_data["success"] is True
        companion = companion_response_data["data"]["entity"]
        test_data_cleanup["entities"].append(companion["id"])
        
        # Step 3: Create the scene with location
        scene_data = {
            "title": "Arrival at the Mysterious Castle",
            "location_id": str(location["id"]),
            "timestamp": 100
        }
        
        scene_response = client.post("/api/v1/scenes", json=scene_data)
        if scene_response.status_code != 200:
            print(f"Scene creation failed: {scene_response.status_code}")
            print(f"Response: {scene_response.json()}")
        assert scene_response.status_code == 200
        scene_response_data = scene_response.json()
        assert scene_response_data["success"] is True
        scene = scene_response_data["data"]["scene"]
        test_data_cleanup["scenes"].append(scene["id"])
        
        assert scene["title"] == "Arrival at the Mysterious Castle"
        assert scene["location_id"] == location["id"]
        assert scene["timestamp"] == 100
        
        # Step 4: Add prose block to set the scene
        prose_block_data = {
            "block_type": "prose",
            "content": "The ancient castle loomed before them, its towers disappearing into the swirling mist. Sir Galahad and Merlin approached the massive gates, their footsteps echoing on the stone bridge.",
            "order": 1,
            "scene_id": scene["id"]
        }
        
        prose_response = client.post(f"/api/v1/scenes/{scene['id']}/blocks", json=prose_block_data)
        assert prose_response.status_code == 200
        prose_response_data = prose_response.json()
        assert prose_response_data["success"] is True
        prose_block = prose_response_data["data"]["block"]
        test_data_cleanup["scene_blocks"].append(prose_block["id"])
        
        # Step 5: Add dialogue between characters
        dialogue_block_data = {
            "block_type": "dialogue", 
            "content": "This place emanates dark magic. We must be cautious, young knight.",
            "order": 2,
            "scene_id": scene["id"],
            "lines": {
                "speaker_id": companion["id"],
                "listener_ids": [hero["id"]],
                "emotion": "concerned"
            }
        }
        
        dialogue_response = client.post(f"/api/v1/scenes/{scene['id']}/blocks", json=dialogue_block_data)
        assert dialogue_response.status_code == 200
        dialogue_response_data = dialogue_response.json()
        assert dialogue_response_data["success"] is True
        dialogue_block = dialogue_response_data["data"]["block"]
        test_data_cleanup["scene_blocks"].append(dialogue_block["id"])
        
        # Step 6: Add hero's response
        hero_dialogue_data = {
            "block_type": "dialogue",
            "content": "I feel it too, Merlin. But we must press on - the quest depends on it.",
            "order": 3,
            "scene_id": scene["id"],
            "lines": {
                "speaker_id": hero["id"],
                "listener_ids": [companion["id"]],
                "emotion": "determined"
            }
        }
        
        hero_response = client.post(f"/api/v1/scenes/{scene['id']}/blocks", json=hero_dialogue_data)
        assert hero_response.status_code == 200
        hero_response_data = hero_response.json()
        assert hero_response_data["success"] is True
        hero_dialogue = hero_response_data["data"]["block"]
        test_data_cleanup["scene_blocks"].append(hero_dialogue["id"])
        
        # Step 7: Verify all blocks are in correct order
        blocks_response = client.get(f"/api/v1/scenes/{scene['id']}/blocks")
        assert blocks_response.status_code == 200
        blocks_data = blocks_response.json()
        assert blocks_data["success"] is True
        
        assert len(blocks_data["data"]["blocks"]) == 3
        blocks = sorted(blocks_data["data"]["blocks"], key=lambda x: x["order"])
        
        assert blocks[0]["block_type"] == "prose"
        assert blocks[1]["block_type"] == "dialogue"
        assert blocks[1]["lines"]["speaker_id"] == companion["id"]
        assert blocks[2]["block_type"] == "dialogue"
        assert blocks[2]["lines"]["speaker_id"] == hero["id"]
        
        # Step 8: Test scene retrieval with all data
        scene_detail_response = client.get(f"/api/v1/scenes/{scene['id']}")
        assert scene_detail_response.status_code == 200
        scene_detail_response_data = scene_detail_response.json()
        assert scene_detail_response_data["success"] is True
        scene_detail = scene_detail_response_data["data"]["scene"]
        
        assert scene_detail["id"] == scene["id"]
        assert scene_detail["title"] == scene["title"]
        assert scene_detail["location_id"] == location["id"]
        
        print(f"✅ Complete scene workflow successful: Scene '{scene['title']}' with {len(blocks)} blocks")
    
    def test_scene_block_reordering_workflow(self, client, cleanup_test_data):
        """Test reordering scene blocks workflow"""
        # Create scene
        scene_response = client.post("/api/v1/scenes", json={
            "title": "Block Reordering Test Scene",
            "timestamp": 200
        })
        scene_response_data = scene_response.json()
        assert scene_response_data["success"] is True
        scene = scene_response_data["data"]["scene"]
        test_data_cleanup["scenes"].append(scene["id"])
        
        # Create multiple blocks
        blocks_data = [
            {"block_type": "prose", "content": "Opening description", "order": 1},
            {"block_type": "prose", "content": "Middle description", "order": 2},
            {"block_type": "prose", "content": "Closing description", "order": 3}
        ]
        
        created_blocks = []
        for block_data in blocks_data:
            response = client.post(f"/api/v1/scenes/{scene['id']}/blocks", json=block_data)
            assert response.status_code == 200
            response_data = response.json()
            assert response_data["success"] is True
            block = response_data["data"]["block"]
            created_blocks.append(block)
            test_data_cleanup["scene_blocks"].append(block["id"])
        
        # Verify initial order
        blocks_response = client.get(f"/api/v1/scenes/{scene['id']}/blocks")
        blocks_response_data = blocks_response.json()
        assert blocks_response_data["success"] is True
        blocks = sorted(blocks_response_data["data"]["blocks"], key=lambda x: x["order"])
        assert [b["content"] for b in blocks] == ["Opening description", "Middle description", "Closing description"]
        
        # Move middle block to end (order 2 → order 1, so it comes first)
        middle_block = created_blocks[1]
        reorder_response = client.post(f"/api/v1/scenes/blocks/{middle_block['id']}/move", json={
            "new_order": 1
        })
        assert reorder_response.status_code == 200
        
        # Verify new order
        blocks_response = client.get(f"/api/v1/scenes/{scene['id']}/blocks")
        blocks_response_data = blocks_response.json()
        assert blocks_response_data["success"] is True
        blocks = sorted(blocks_response_data["data"]["blocks"], key=lambda x: x["order"])
        
        # The middle block should now be first
        assert blocks[0]["id"] == middle_block["id"]
        assert blocks[0]["content"] == "Middle description"
        
        print("✅ Block reordering workflow successful")


class TestEntityRelationshipWorkflow:
    """Test workflows involving entity relationships and complex metadata"""
    
    def test_character_possession_workflow(self, client, cleanup_test_data):
        """Test workflow where character acquires artifacts"""
        # Create character
        character_data = {
            "name": "Lyra the Adventurer",
            "entity_type": "character",
            "description": "A skilled treasure hunter",
            "metadata": {
                "inventory": [],
                "gold": 100,
                "reputation": "unknown"
            }
        }
        
        char_response = client.post("/api/v1/entities", json=character_data)
        character = char_response.json()
        test_data_cleanup["entities"].append(character["id"])
        
        # Create artifacts to be acquired
        artifacts_data = [
            {
                "name": "Ancient Key",
                "entity_type": "artifact", 
                "description": "A key that opens ancient locks",
                "metadata": {"material": "gold", "power": "unlocking", "owner": None}
            },
            {
                "name": "Crystal Amulet",
                "entity_type": "artifact",
                "description": "An amulet that glows with inner light",
                "metadata": {"material": "crystal", "power": "light", "owner": None}
            }
        ]
        
        artifacts = []
        for artifact_data in artifacts_data:
            response = client.post("/api/v1/entities", json=artifact_data)
            artifact = response.json()
            artifacts.append(artifact)
            test_data_cleanup["entities"].append(artifact["id"])
        
        # Create scene where character finds artifacts
        scene_response = client.post("/api/v1/scenes", json={
            "title": "The Hidden Treasure Chamber",
            "timestamp": 300
        })
        scene = scene_response.json()
        test_data_cleanup["scenes"].append(scene["id"])
        
        # Add blocks documenting the discovery
        prose_response = client.post(f"/api/v1/scenes/{scene['id']}/blocks", json={
            "block_type": "prose",
            "content": "Lyra's torch illuminated the dusty chamber, revealing ancient treasures scattered across stone pedestals.",
            "order": 1,
            "scene_id": scene["id"]
        })
        prose_block = prose_response.json()
        test_data_cleanup["scene_blocks"].append(prose_block["id"])
        
        # Create milestones for each artifact acquisition
        for i, artifact in enumerate(artifacts):
            milestone_data = {
                "subject_id": character["id"],
                "verb": "obtains",
                "object_id": artifact["id"],
                "description": f"Lyra obtains the {artifact['name']}",
                "timestamp": 300 + i + 1,
                "significance": "minor"
            }
            
            milestone_response = client.post("/api/v1/milestones", json=milestone_data)
            assert milestone_response.status_code == 200
            milestone = milestone_response.json()
            test_data_cleanup["milestones"].append(milestone["id"])
            
            # Update artifact to show new ownership
            artifact_update = {
                "metadata": {
                    **artifact["metadata"],
                    "owner": character["id"]
                }
            }
            
            update_response = client.put(f"/api/v1/entities/{artifact['id']}", json=artifact_update)
            assert update_response.status_code == 200
        
        # Update character's inventory
        character_update = {
            "metadata": {
                **character["metadata"],
                "inventory": [artifact["id"] for artifact in artifacts],
                "reputation": "treasure finder"
            }
        }
        
        update_response = client.put(f"/api/v1/entities/{character['id']}", json=character_update)
        assert update_response.status_code == 200
        updated_character = update_response.json()
        
        # Verify the relationships are established
        assert len(updated_character["metadata"]["inventory"]) == 2
        assert updated_character["metadata"]["reputation"] == "treasure finder"
        
        # Verify milestones were created
        milestones_response = client.get("/api/v1/milestones")
        milestones_data = milestones_response.json()
        
        character_milestones = [
            m for m in milestones_data["milestones"]
            if m["subject_id"] == character["id"] and m["verb"] == "obtains"
        ]
        assert len(character_milestones) >= 2  # At least our 2 milestones
        
        print("✅ Character possession workflow successful")
    
    def test_location_inhabitants_workflow(self, client, cleanup_test_data):
        """Test workflow for managing location inhabitants"""
        # Create location
        location_data = {
            "name": "The Village of Millhaven",
            "entity_type": "location",
            "description": "A peaceful farming village",
            "metadata": {
                "population": 0,
                "inhabitants": [],
                "prosperity": "moderate",
                "defenses": "wooden palisade"
            }
        }
        
        location_response = client.post("/api/v1/entities", json=location_data)
        location = location_response.json()
        test_data_cleanup["entities"].append(location["id"])
        
        # Create inhabitants
        inhabitants_data = [
            {
                "name": "Mayor Thompson",
                "entity_type": "character",
                "description": "The village mayor",
                "metadata": {"role": "leader", "home": location["id"]}
            },
            {
                "name": "Blacksmith Jonas",
                "entity_type": "character", 
                "description": "The village blacksmith",
                "metadata": {"role": "craftsman", "home": location["id"]}
            },
            {
                "name": "Healer Elena",
                "entity_type": "character",
                "description": "The village healer",
                "metadata": {"role": "healer", "home": location["id"]}
            }
        ]
        
        inhabitants = []
        for inhabitant_data in inhabitants_data:
            response = client.post("/api/v1/entities", json=inhabitant_data)
            inhabitant = response.json()
            inhabitants.append(inhabitant)
            test_data_cleanup["entities"].append(inhabitant["id"])
        
        # Update location with inhabitants
        location_update = {
            "metadata": {
                **location["metadata"],
                "population": len(inhabitants),
                "inhabitants": [inh["id"] for inh in inhabitants]
            }
        }
        
        update_response = client.put(f"/api/v1/entities/{location['id']}", json=location_update)
        assert update_response.status_code == 200
        updated_location = update_response.json()
        
        # Verify relationships
        assert updated_location["metadata"]["population"] == 3
        assert len(updated_location["metadata"]["inhabitants"]) == 3
        
        # Create scene in the location
        scene_response = client.post("/api/v1/scenes", json={
            "title": "Visiting Millhaven",
            "location_id": location["id"],
            "timestamp": 400
        })
        scene = scene_response.json()
        test_data_cleanup["scenes"].append(scene["id"])
        
        # Add dialogue with inhabitants
        dialogue_data = {
            "block_type": "dialogue",
            "content": "Welcome to Millhaven, traveler! What brings you to our humble village?",
            "order": 1,
            "speaker_id": inhabitants[0]["id"],  # Mayor Thompson
            "listener_ids": [],
            "emotion": "welcoming"
        }
        
        dialogue_response = client.post(f"/api/v1/scenes/{scene['id']}/blocks", json=dialogue_data)
        dialogue_block = dialogue_response.json()
        test_data_cleanup["scene_blocks"].append(dialogue_block["id"])
        
        assert dialogue_block["speaker_id"] == inhabitants[0]["id"]
        
        print("✅ Location inhabitants workflow successful")


class TestGoalMilestoneWorkflow:
    """Test workflows involving story goals and milestone achievements"""
    
    def test_quest_completion_workflow(self, client, cleanup_test_data):
        """Test complete quest workflow from goal creation to completion"""
        # Create quest entities
        hero_data = {
            "name": "Sir Percival",
            "entity_type": "character",
            "description": "A noble knight seeking the Holy Grail",
            "metadata": {"quest_status": "active", "virtue": "purity"}
        }
        
        hero_response = client.post("/api/v1/entities", json=hero_data)
        hero = hero_response.json()
        test_data_cleanup["entities"].append(hero["id"])
        
        grail_data = {
            "name": "The Holy Grail",
            "entity_type": "artifact",
            "description": "The legendary cup of eternal life",
            "metadata": {"power": "healing", "location": "unknown", "status": "hidden"}
        }
        
        grail_response = client.post("/api/v1/entities", json=grail_data)
        grail = grail_response.json()
        test_data_cleanup["entities"].append(grail["id"])
        
        # Create the quest goal
        goal_data = {
            "subject_id": hero["id"],
            "verb": "find",
            "object_id": grail["id"],
            "description": "Sir Percival must find the Holy Grail",
            "status": "active",
            "priority": "critical"
        }
        
        goal_response = client.post("/api/v1/goals", json=goal_data)
        assert goal_response.status_code == 200
        goal = goal_response.json()
        test_data_cleanup["goals"].append(goal["id"])
        
        # Create scenes documenting the quest journey
        journey_scenes = [
            {"title": "The Quest Begins", "timestamp": 500},
            {"title": "Trials and Tribulations", "timestamp": 600}, 
            {"title": "The Final Challenge", "timestamp": 700}
        ]
        
        scenes = []
        for scene_data in journey_scenes:
            response = client.post("/api/v1/scenes", json=scene_data)
            scene = response.json()
            scenes.append(scene)
            test_data_cleanup["scenes"].append(scene["id"])
        
        # Add story content to each scene
        for i, scene in enumerate(scenes):
            prose_content = [
                "Sir Percival set forth on his sacred quest, determined to prove himself worthy.",
                "Through dark forests and treacherous mountains, the knight persevered against all odds.",
                "At last, Percival faced the final trial that would determine his destiny."
            ]
            
            prose_response = client.post(f"/api/v1/scenes/{scene['id']}/blocks", json={
                "block_type": "prose",
                "content": prose_content[i],
                "order": 1
            })
            prose_block = prose_response.json()
            test_data_cleanup["scene_blocks"].append(prose_block["id"])
        
        # Create milestone for quest completion
        completion_milestone = {
            "subject_id": hero["id"],
            "verb": "finds",
            "object_id": grail["id"],
            "description": "Sir Percival discovers the Holy Grail in the sacred chapel",
            "timestamp": 800,
            "significance": "critical"
        }
        
        milestone_response = client.post("/api/v1/milestones", json=completion_milestone)
        assert milestone_response.status_code == 200
        milestone = milestone_response.json()
        test_data_cleanup["milestones"].append(milestone["id"])
        
        # Update goal status to completed
        goal_update = {
            "status": "completed",
            "description": goal["description"] + " - COMPLETED!"
        }
        
        update_response = client.put(f"/api/v1/goals/{goal['id']}", json=goal_update)
        assert update_response.status_code == 200
        completed_goal = update_response.json()
        
        assert completed_goal["status"] == "completed"
        assert "COMPLETED!" in completed_goal["description"]
        
        # Update entities to reflect quest completion
        hero_update = {
            "metadata": {
                **hero["metadata"],
                "quest_status": "completed",
                "achievement": "found_holy_grail"
            }
        }
        
        client.put(f"/api/v1/entities/{hero['id']}", json=hero_update)
        
        grail_update = {
            "metadata": {
                **grail["metadata"],
                "location": "with_percival",
                "status": "found"
            }
        }
        
        client.put(f"/api/v1/entities/{grail['id']}", json=grail_update)
        
        # Verify the complete quest workflow
        final_goal_response = client.get(f"/api/v1/goals/{goal['id']}")
        final_goal = final_goal_response.json()
        assert final_goal["status"] == "completed"
        
        final_milestone_response = client.get(f"/api/v1/milestones/{milestone['id']}")
        final_milestone = final_milestone_response.json()
        assert final_milestone["subject_id"] == hero["id"]
        assert final_milestone["object_id"] == grail["id"]
        assert final_milestone["verb"] == "finds"
        
        print("✅ Quest completion workflow successful")


class TestComplexStoryWorkflow:
    """Test complex multi-character, multi-scene story workflows"""
    
    def test_multi_character_story_arc_workflow(self, client, cleanup_test_data):
        """Test a complex story with multiple characters, scenes, and plot developments"""
        # Create story setting - a magical academy
        academy_data = {
            "name": "Arcanum Academy",
            "entity_type": "location",
            "description": "A prestigious school of magical arts",
            "metadata": {
                "type": "educational_institution",
                "magical_level": "high",
                "student_capacity": 500,
                "specialties": ["elemental magic", "divination", "alchemy"]
            }
        }
        
        academy_response = client.post("/api/v1/entities", json=academy_data)
        academy = academy_response.json()
        test_data_cleanup["entities"].append(academy["id"])
        
        # Create main characters
        characters_data = [
            {
                "name": "Luna Starweaver",
                "entity_type": "character",
                "description": "A talented first-year student with a mysterious past",
                "metadata": {"year": 1, "house": "Celestial", "specialty": "divination", "secret": "royal_bloodline"}
            },
            {
                "name": "Professor Aldric",
                "entity_type": "character", 
                "description": "The stern but fair headmaster",
                "metadata": {"position": "headmaster", "years_service": 30, "specialty": "all_schools"}
            },
            {
                "name": "Zara Nightshade",
                "entity_type": "character",
                "description": "A rival student from a dark magical family",
                "metadata": {"year": 1, "house": "Shadow", "specialty": "dark_arts", "motivation": "family_honor"}
            }
        ]
        
        characters = []
        for char_data in characters_data:
            response = client.post("/api/v1/entities", json=char_data)
            character = response.json()
            characters.append(character)
            test_data_cleanup["entities"].append(character["id"])
        
        luna, professor, zara = characters
        
        # Create story goals
        goals_data = [
            {
                "subject_id": luna["id"],
                "verb": "master",
                "object_id": academy["id"],
                "description": "Luna must prove herself worthy at the academy",
                "status": "active",
                "priority": "high"
            },
            {
                "subject_id": zara["id"],
                "verb": "defeat",
                "object_id": luna["id"],
                "description": "Zara seeks to outperform Luna and claim supremacy",
                "status": "active", 
                "priority": "medium"
            }
        ]
        
        goals = []
        for goal_data in goals_data:
            response = client.post("/api/v1/goals", json=goal_data)
            goal = response.json()
            goals.append(goal)
            test_data_cleanup["goals"].append(goal["id"])
        
        # Create story scenes following a narrative arc
        scenes_data = [
            {"title": "Arrival at Arcanum", "timestamp": 1000},
            {"title": "The First Lesson", "timestamp": 1100},
            {"title": "Rivalry Emerges", "timestamp": 1200},
            {"title": "The Magical Duel", "timestamp": 1300},
            {"title": "Truth Revealed", "timestamp": 1400}
        ]
        
        scenes = []
        for scene_data in scenes_data:
            scene_data["location_id"] = academy["id"]
            response = client.post("/api/v1/scenes", json=scene_data)
            scene = response.json()
            scenes.append(scene)
            test_data_cleanup["scenes"].append(scene["id"])
        
        # Add detailed content to each scene
        scene_contents = [
            # Scene 1: Arrival
            [
                {
                    "block_type": "prose",
                    "content": "The ancient towers of Arcanum Academy pierced the morning sky as Luna approached the massive gates, her heart pounding with anticipation and nervousness.",
                    "order": 1
                },
                {
                    "block_type": "dialogue",
                    "content": "Welcome to Arcanum Academy, Miss Starweaver. Your destiny awaits within these walls.",
                    "order": 2,
                    "speaker_id": professor["id"],
                    "listener_ids": [luna["id"]],
                    "emotion": "formal"
                }
            ],
            # Scene 2: First Lesson
            [
                {
                    "block_type": "prose",
                    "content": "In the crystalline classroom, students gathered around floating orbs of light, each attempting their first spell.",
                    "order": 1
                },
                {
                    "block_type": "dialogue",
                    "content": "Focus your intent, young mages. Magic flows from the clarity of purpose.",
                    "order": 2,
                    "speaker_id": professor["id"],
                    "listener_ids": [luna["id"], zara["id"]],
                    "emotion": "instructive"
                }
            ],
            # Scene 3: Rivalry
            [
                {
                    "block_type": "dialogue",
                    "content": "You think you're special, don't you, Starweaver? We'll see about that.",
                    "order": 1,
                    "speaker_id": zara["id"],
                    "listener_ids": [luna["id"]],
                    "emotion": "challenging"
                },
                {
                    "block_type": "dialogue",
                    "content": "I'm here to learn, not to compete. But I won't back down from a challenge.",
                    "order": 2,
                    "speaker_id": luna["id"],
                    "listener_ids": [zara["id"]],
                    "emotion": "determined"
                }
            ],
            # Scene 4: Duel
            [
                {
                    "block_type": "prose",
                    "content": "The two students faced each other in the dueling circle, magical energy crackling between them as they prepared to settle their rivalry.",
                    "order": 1
                }
            ],
            # Scene 5: Truth
            [
                {
                    "block_type": "dialogue",
                    "content": "The royal bloodline carries great responsibility, Luna. Your true education begins now.",
                    "order": 1,
                    "speaker_id": professor["id"],
                    "listener_ids": [luna["id"]],
                    "emotion": "serious"
                }
            ]
        ]
        
        # Add content blocks to scenes
        for scene, contents in zip(scenes, scene_contents):
            for content in contents:
                response = client.post(f"/api/v1/scenes/{scene['id']}/blocks", json=content)
                block = response.json()
                test_data_cleanup["scene_blocks"].append(block["id"])
        
        # Create key milestones
        milestones_data = [
            {
                "subject_id": luna["id"],
                "verb": "arrives_at",
                "object_id": academy["id"],
                "description": "Luna arrives at Arcanum Academy to begin her magical education",
                "timestamp": 1000,
                "significance": "major"
            },
            {
                "subject_id": zara["id"],
                "verb": "challenges",
                "object_id": luna["id"],
                "description": "Zara formally challenges Luna to prove magical superiority",
                "timestamp": 1200,
                "significance": "major"
            },
            {
                "subject_id": luna["id"],
                "verb": "discovers",
                "object_id": luna["id"],  # Self-discovery
                "description": "Luna discovers her true royal heritage and magical potential",
                "timestamp": 1400,
                "significance": "critical"
            }
        ]
        
        milestones = []
        for milestone_data in milestones_data:
            response = client.post("/api/v1/milestones", json=milestone_data)
            milestone = response.json()
            milestones.append(milestone)
            test_data_cleanup["milestones"].append(milestone["id"])
        
        # Verify the complete story structure
        # Check that all scenes have content
        for scene in scenes:
            blocks_response = client.get(f"/api/v1/scenes/{scene['id']}/blocks")
            blocks = blocks_response.json()["blocks"]
            assert len(blocks) > 0, f"Scene '{scene['title']}' has no content blocks"
        
        # Check that milestones are properly created
        milestones_response = client.get("/api/v1/milestones")
        all_milestones = milestones_response.json()["milestones"]
        story_milestones = [
            m for m in all_milestones
            if m["subject_id"] in [luna["id"], zara["id"]]
        ]
        assert len(story_milestones) >= 3, "Not all story milestones were created"
        
        # Check that goals are tracking properly
        goals_response = client.get("/api/v1/goals")
        all_goals = goals_response.json()["goals"]
        story_goals = [
            g for g in all_goals
            if g["subject_id"] in [luna["id"], zara["id"]]
        ]
        assert len(story_goals) >= 2, "Not all story goals were created"
        
        print("✅ Complex multi-character story workflow successful")
        print(f"   Created {len(scenes)} scenes with content")
        print(f"   Created {len(milestones)} key milestones")
        print(f"   Created {len(goals)} story goals")
        print(f"   Established relationships between {len(characters)} characters")


class TestWorkflowErrorRecovery:
    """Test workflow resilience and error recovery"""
    
    def test_workflow_with_missing_dependencies(self, client, cleanup_test_data):
        """Test workflow behavior when dependencies are missing or deleted"""
        # Create a scene with a location
        location_response = client.post("/api/v1/entities", json={
            "name": "Temporary Location",
            "entity_type": "location",
            "description": "A location that will be deleted"
        })
        location = location_response.json()
        test_data_cleanup["entities"].append(location["id"])
        
        scene_response = client.post("/api/v1/scenes", json={
            "title": "Scene with Dependencies",
            "location_id": location["id"],
            "timestamp": 500
        })
        scene = scene_response.json()
        test_data_cleanup["scenes"].append(scene["id"])
        
        # Create a character and dialogue
        character_response = client.post("/api/v1/entities", json={
            "name": "Temporary Character", 
            "entity_type": "character",
            "description": "A character that will be deleted"
        })
        character = character_response.json()
        test_data_cleanup["entities"].append(character["id"])
        
        dialogue_response = client.post(f"/api/v1/scenes/{scene['id']}/blocks", json={
            "block_type": "dialogue",
            "content": "I am about to disappear!",
            "order": 1,
            "speaker_id": character["id"],
            "listener_ids": []
        })
        dialogue_block = dialogue_response.json()
        test_data_cleanup["scene_blocks"].append(dialogue_block["id"])
        
        # Verify everything is working
        scene_check = client.get(f"/api/v1/scenes/{scene['id']}")
        assert scene_check.status_code == 200
        assert scene_check.json()["location_id"] == location["id"]
        
        blocks_check = client.get(f"/api/v1/scenes/{scene['id']}/blocks")
        assert blocks_check.status_code == 200
        assert len(blocks_check.json()["blocks"]) == 1
        
        # Delete the character (simulating data corruption or cleanup)
        delete_response = client.delete(f"/api/v1/entities/{character['id']}")
        assert delete_response.status_code == 200
        test_data_cleanup["entities"].remove(character["id"])
        
        # Scene should still exist and be retrievable
        scene_after_deletion = client.get(f"/api/v1/scenes/{scene['id']}")
        assert scene_after_deletion.status_code == 200
        
        # Blocks should still exist (orphaned speaker_id is allowed)
        blocks_after_deletion = client.get(f"/api/v1/scenes/{scene['id']}/blocks")
        assert blocks_after_deletion.status_code == 200
        blocks = blocks_after_deletion.json()["blocks"]
        assert len(blocks) == 1
        assert blocks[0]["speaker_id"] == character["id"]  # Orphaned reference
        
        print("✅ Workflow error recovery test successful")
    
    def test_workflow_transaction_integrity(self, client, cleanup_test_data):
        """Test that workflow operations maintain data integrity"""
        # Create entities for a complex workflow
        entities_data = [
            {"name": "Hero", "entity_type": "character", "description": "Main character"},
            {"name": "Castle", "entity_type": "location", "description": "Main setting"},
            {"name": "Sword", "entity_type": "artifact", "description": "Important item"}
        ]
        
        entities = []
        for entity_data in entities_data:
            response = client.post("/api/v1/entities", json=entity_data)
            entity = response.json()
            entities.append(entity)
            test_data_cleanup["entities"].append(entity["id"])
        
        hero, castle, sword = entities
        
        # Create a goal
        goal_response = client.post("/api/v1/goals", json={
            "subject_id": hero["id"],
            "verb": "retrieve",
            "object_id": sword["id"],
            "description": "Hero must retrieve the sword",
            "status": "active"
        })
        goal = goal_response.json()
        test_data_cleanup["goals"].append(goal["id"])
        
        # Create a scene
        scene_response = client.post("/api/v1/scenes", json={
            "title": "The Quest for the Sword",
            "location_id": castle["id"],
            "timestamp": 600
        })
        scene = scene_response.json()
        test_data_cleanup["scenes"].append(scene["id"])
        
        # Create a milestone
        milestone_response = client.post("/api/v1/milestones", json={
            "subject_id": hero["id"],
            "verb": "retrieves",
            "object_id": sword["id"],
            "description": "Hero successfully retrieves the magical sword",
            "timestamp": 650,
            "significance": "critical"
        })
        milestone = milestone_response.json()
        test_data_cleanup["milestones"].append(milestone["id"])
        
        # Verify all relationships are intact
        final_goal = client.get(f"/api/v1/goals/{goal['id']}").json()
        final_scene = client.get(f"/api/v1/scenes/{scene['id']}").json()
        final_milestone = client.get(f"/api/v1/milestones/{milestone['id']}").json()
        
        # Check entity references are maintained
        assert final_goal["subject_id"] == hero["id"]
        assert final_goal["object_id"] == sword["id"]
        assert final_scene["location_id"] == castle["id"]
        assert final_milestone["subject_id"] == hero["id"]
        assert final_milestone["object_id"] == sword["id"]
        
        # Check that timestamps are logical
        assert final_milestone["timestamp"] > final_scene["timestamp"]
        
        print("✅ Workflow transaction integrity test successful")
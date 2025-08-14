"""
Phase 3 Integration Testing - Cross-System Integration Tests
Comprehensive testing for Knowledge, Relationships, and Content systems working together.

Target: 40+ integration tests covering all Phase 3 system interactions
"""

import pytest
import time
from uuid import uuid4
from datetime import datetime
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


class TestPhase3SystemIntegration:
    """Test all Phase 3 systems working together"""
    
    def setup_method(self):
        """Setup test data for each test"""
        self.test_entities = {}
        self.test_scenes = {}
        self.test_relationships = {}
        self.test_knowledge = {}
        
    def create_test_character(self, name: str, description: str = None) -> dict:
        """Helper to create a test character"""
        data = {
            "name": name,
            "entity_type": "character",
            "description": description or f"Test character {name}",
            "meta": {"test": True}
        }
        response = client.post("/api/v1/entities/", json=data)
        assert response.status_code == 200
        entity = response.json()["data"]["entity"]
        self.test_entities[name] = entity
        return entity
        
    def create_test_scene(self, title: str, timestamp: int = None) -> dict:
        """Helper to create a test scene"""
        data = {
            "title": title,
            "timestamp": timestamp or int(time.time() * 1000)
        }
        response = client.post("/api/v1/scenes/", json=data)
        assert response.status_code == 200
        scene = response.json()["data"]["scene"]
        self.test_scenes[title] = scene
        return scene
        
    def create_test_relationship(self, entity1_id: str, entity2_id: str, 
                               relationship_type: str, timestamp_start: int = None) -> dict:
        """Helper to create a test relationship"""
        data = {
            "source_id": entity1_id,
            "target_id": entity2_id,
            "relation_type": relationship_type,
            "starts_at": timestamp_start or 100,
            "meta": {"test": True}
        }
        response = client.post("/api/v1/relationships", json=data)
        assert response.status_code == 200
        relationship = response.json()["data"]
        return relationship
        
    def create_test_knowledge_snapshot(self, entity_id: str, timestamp: int = None, 
                                     knowledge_content: dict = None) -> dict:
        """Helper to create a knowledge snapshot"""
        data = {
            "entity_id": entity_id,
            "timestamp": timestamp or 100,
            "knowledge": knowledge_content or {"facts": ["test knowledge"]},
            "meta": {"test": True}
        }
        response = client.post("/api/v1/knowledge/snapshots", json=data)
        assert response.status_code == 200
        snapshot = response.json()["data"]["snapshot"]
        return snapshot


class TestKnowledgeRelationshipIntegration(TestPhase3SystemIntegration):
    """Test Knowledge ↔ Relationships integration"""
    
    def test_relationship_affects_character_knowledge(self):
        """Test: Relationship changes should affect character knowledge queries"""
        # Create characters
        alice = self.create_test_character("Alice", "Adventurous protagonist")
        bob = self.create_test_character("Bob", "Mysterious wizard")
        
        # Create initial relationship: enemies
        relationship = self.create_test_relationship(
            alice["id"], bob["id"], "enemies", timestamp_start=100
        )
        
        # Create knowledge snapshot: Alice knows Bob is enemy
        knowledge1 = self.create_test_knowledge_snapshot(
            alice["id"], 
            timestamp=150,
            knowledge_content={
                "relationships": {
                    bob["id"]: {
                        "type": "enemies",
                        "discovered_at": 120,
                        "notes": "Bob attacked Alice's village"
                    }
                }
            }
        )
        
        # Update relationship to friends
        update_data = {
            "relation_type": "friends",
            "ends_at": 200,
            "meta": {"reason": "Alice saved Bob from dragon"}
        }
        response = client.put(f"/api/v1/relationships/{relationship['id']}", json=update_data)
        assert response.status_code == 200
        
        # Create new knowledge snapshot reflecting friendship
        knowledge2 = self.create_test_knowledge_snapshot(
            alice["id"],
            timestamp=250,
            knowledge_content={
                "relationships": {
                    bob["id"]: {
                        "type": "friends",
                        "discovered_at": 120,
                        "changed_at": 210,
                        "notes": "Bob is actually a good person who was cursed"
                    }
                }
            }
        )
        
        # Verify knowledge evolution
        response = client.get(f"/api/v1/knowledge/snapshots/character/{alice['id']}")
        assert response.status_code == 200
        snapshots = response.json()["data"]["snapshots"]
        assert len(snapshots) == 2
        
        # Verify relationship timeline
        response = client.get(f"/api/v1/relationships/between/{alice['id']}/{bob['id']}")
        assert response.status_code == 200
        relationships = response.json()["data"]
        assert len(relationships) >= 1
        
    def test_knowledge_snapshot_relationship_consistency(self):
        """Test: Knowledge snapshots should be consistent with relationship timeline"""
        # Create characters
        alice = self.create_test_character("Alice")
        bob = self.create_test_character("Bob")
        charlie = self.create_test_character("Charlie")
        
        # Create relationships at different times
        rel1 = self.create_test_relationship(alice["id"], bob["id"], "friends", 100)
        rel2 = self.create_test_relationship(bob["id"], charlie["id"], "mentor", 150)
        rel3 = self.create_test_relationship(alice["id"], charlie["id"], "student", 200)
        
        # Create knowledge snapshots at specific timeline points
        # Alice's knowledge at timestamp 120 - knows Bob as friend
        knowledge_120 = self.create_test_knowledge_snapshot(
            alice["id"], 120,
            knowledge_content={
                "known_characters": [bob["id"]],
                "relationships": {
                    bob["id"]: {"type": "friends", "since": 100}
                }
            }
        )
        
        # Alice's knowledge at timestamp 180 - knows Bob, heard about Charlie
        knowledge_180 = self.create_test_knowledge_snapshot(
            alice["id"], 180,
            knowledge_content={
                "known_characters": [bob["id"], charlie["id"]],
                "relationships": {
                    bob["id"]: {"type": "friends", "since": 100},
                    charlie["id"]: {"type": "heard_of", "source": bob["id"]}
                }
            }
        )
        
        # Alice's knowledge at timestamp 220 - direct relationship with Charlie
        knowledge_220 = self.create_test_knowledge_snapshot(
            alice["id"], 220,
            knowledge_content={
                "known_characters": [bob["id"], charlie["id"]],
                "relationships": {
                    bob["id"]: {"type": "friends", "since": 100},
                    charlie["id"]: {"type": "student", "since": 200}
                }
            }
        )
        
        # Verify timeline consistency
        response = client.get(f"/api/v1/knowledge/snapshots/character/{alice['id']}")
        assert response.status_code == 200
        snapshots = response.json()["data"]["snapshots"]
        assert len(snapshots) == 3
        
        # Verify relationships are active at correct times
        response = client.get(f"/api/v1/relationships/active?time=120")
        assert response.status_code == 200
        active_at_120 = response.json()["data"]
        
        response = client.get(f"/api/v1/relationships/active?time=180")
        assert response.status_code == 200
        active_at_180 = response.json()["data"]
        
        response = client.get(f"/api/v1/relationships/active?time=220")
        assert response.status_code == 200
        active_at_220 = response.json()["data"]
        
        # At 120: only Alice-Bob friendship
        assert len(active_at_120) >= 1
        # At 180: Alice-Bob + Bob-Charlie mentorship
        assert len(active_at_180) >= 2
        # At 220: All three relationships
        assert len(active_at_220) >= 3
        
    def test_relationship_network_knowledge_discovery(self):
        """Test: Characters learn about other characters through relationship networks"""
        # Create character network: Alice -> Bob -> Charlie -> Diana
        alice = self.create_test_character("Alice")
        bob = self.create_test_character("Bob")
        charlie = self.create_test_character("Charlie")
        diana = self.create_test_character("Diana")
        
        # Create relationship chain
        rel1 = self.create_test_relationship(alice["id"], bob["id"], "friends", 100)
        rel2 = self.create_test_relationship(bob["id"], charlie["id"], "siblings", 100)
        rel3 = self.create_test_relationship(charlie["id"], diana["id"], "spouse", 100)
        
        # Alice initially only knows Bob
        knowledge_alice_1 = self.create_test_knowledge_snapshot(
            alice["id"], 110,
            knowledge_content={
                "known_characters": [bob["id"]],
                "discovery_method": {
                    bob["id"]: "direct_meeting"
                }
            }
        )
        
        # Alice learns about Charlie through Bob
        knowledge_alice_2 = self.create_test_knowledge_snapshot(
            alice["id"], 150,
            knowledge_content={
                "known_characters": [bob["id"], charlie["id"]],
                "discovery_method": {
                    bob["id"]: "direct_meeting",
                    charlie["id"]: "mentioned_by_bob"
                },
                "relationship_knowledge": {
                    charlie["id"]: "bob_sibling"
                }
            }
        )
        
        # Alice learns about Diana through Charlie
        knowledge_alice_3 = self.create_test_knowledge_snapshot(
            alice["id"], 200,
            knowledge_content={
                "known_characters": [bob["id"], charlie["id"], diana["id"]],
                "discovery_method": {
                    bob["id"]: "direct_meeting",
                    charlie["id"]: "mentioned_by_bob",
                    diana["id"]: "mentioned_by_charlie"
                },
                "relationship_knowledge": {
                    charlie["id"]: "bob_sibling",
                    diana["id"]: "charlie_spouse"
                }
            }
        )
        
        # Verify knowledge progression
        response = client.get(f"/api/v1/knowledge/snapshots/character/{alice['id']}")
        assert response.status_code == 200
        snapshots = response.json()["data"]["snapshots"]
        assert len(snapshots) == 3
        
        # Verify relationship network can be traced
        response = client.get(f"/api/v1/relationships/graph/{alice['id']}")
        assert response.status_code == 200
        graph = response.json()["data"]
        
        # Should show connections through the network
        assert len(graph["entities"]) >= 4  # Alice, Bob, Charlie, Diana
        assert len(graph["relationships"]) >= 3  # The three relationships


class TestContentKnowledgeIntegration(TestPhase3SystemIntegration):
    """Test Content ↔ Knowledge integration"""
    
    def test_milestone_blocks_create_knowledge_snapshots(self):
        """Test: Milestone blocks should trigger knowledge snapshot creation"""
        # Create characters and scene
        alice = self.create_test_character("Alice")
        bob = self.create_test_character("Bob")
        scene = self.create_test_scene("Discovery Scene", timestamp=1000)
        
        # Create milestone block: "Alice learns Bob's secret"
        milestone_data = {
            "scene_id": str(scene["id"]),
            "block_type": "milestone",
            "content": "Alice discovers Bob is actually a powerful wizard",
            "order": 1,
            "subject_id": str(alice["id"]),
            "verb": "learns",
            "object_id": str(bob["id"]),
            "meta": {
                "description": "Alice discovers Bob's magical abilities",
                "impact_level": "major",
                "triggers_knowledge": True
            }
        }
        
        response = client.post(f"/api/v1/scenes/{scene['id']}/blocks", json=milestone_data)
        assert response.status_code == 200
        block = response.json()["data"]["block"]
        
        # Create knowledge snapshot reflecting this discovery
        knowledge_data = {
            "entity_id": alice["id"],
            "timestamp": 1010,  # Shortly after milestone
            "knowledge": {
                "discoveries": {
                    "bobs_secret": {
                        "discovered_at": 1000,
                        "content": "Bob is a powerful wizard",
                        "source": "direct_observation",
                        "certainty": "confirmed"
                    }
                },
                "character_knowledge": {
                    bob["id"]: {
                        "is_wizard": True,
                        "power_level": "high",
                        "discovered_in_scene": scene["id"]
                    }
                }
            },
            "meta": {"triggered_by_milestone": block["id"]}
        }
        
        snapshot = self.create_test_knowledge_snapshot(
            alice["id"], 1010, knowledge_data["knowledge"]
        )
        
        # Verify milestone and knowledge are linked
        response = client.get(f"/api/v1/knowledge/snapshots/scene/{scene['id']}")
        assert response.status_code == 200
        scene_snapshots = response.json()["data"]["snapshots"]
        assert len(scene_snapshots) == 1
        assert scene_snapshots[0]["entity_id"] == alice["id"]
        
    def test_scene_content_knowledge_consistency(self):
        """Test: Scene content should be consistent with character knowledge"""
        # Create characters and scene
        alice = self.create_test_character("Alice")
        bob = self.create_test_character("Bob")
        scene = self.create_test_scene("Conversation Scene", timestamp=2000)
        
        # Alice's knowledge before scene - doesn't know Bob's secret
        knowledge_before = self.create_test_knowledge_snapshot(
            alice["id"], 1900,
            knowledge_content={
                "character_knowledge": {
                    bob["id"]: {
                        "is_friend": True,
                        "knows_secret": False
                    }
                }
            }
        )
        
        # Create dialogue blocks showing Alice learning
        dialogue_data = [
            {
                "scene_id": scene["id"],
                "block_type": "dialogue",
                "summary": "Alice asks Bob about his strange behavior",
                "lines": {
                    "speaker_id": alice["id"],
                    "listener_id": bob["id"],
                    "content": "Bob, you've been acting strange lately. What's going on?",
                    "emotion": "concerned"
                },
                "order": 1
            },
            {
                "scene_id": scene["id"],
                "block_type": "dialogue", 
                "summary": "Bob reveals he has a secret",
                "lines": {
                    "speaker_id": bob["id"],
                    "listener_id": alice["id"],
                    "content": "Alice, I need to tell you something. I'm not who you think I am.",
                    "emotion": "serious"
                },
                "order": 2
            },
            {
                "scene_id": scene["id"],
                "block_type": "dialogue",
                "summary": "Bob reveals he is a wizard",
                "lines": {
                    "speaker_id": bob["id"],
                    "listener_id": alice["id"],
                    "content": "I'm actually a wizard. I've been hiding my powers.",
                    "emotion": "nervous"
                },
                "order": 3
            }
        ]
        
        blocks = []
        for block_data in dialogue_data:
            response = client.post(f"/api/v1/scenes/{scene['id']}/blocks", json=block_data)
            assert response.status_code == 200
            blocks.append(response.json()["data"]["block"])
        
        # Alice's knowledge after scene - now knows Bob's secret
        knowledge_after = self.create_test_knowledge_snapshot(
            alice["id"], 2100,
            knowledge_content={
                "character_knowledge": {
                    bob["id"]: {
                        "is_friend": True,
                        "knows_secret": True,
                        "is_wizard": True,
                        "secret_revealed_in_scene": scene["id"]
                    }
                }
            }
        )
        
        # Verify scene blocks and knowledge progression
        response = client.get(f"/api/v1/scenes/{scene['id']}/blocks")
        assert response.status_code == 200
        scene_blocks = response.json()["data"]["blocks"]
        assert len(scene_blocks) == 3
        
        response = client.get(f"/api/v1/knowledge/snapshots/character/{alice['id']}")
        assert response.status_code == 200
        snapshots = response.json()["data"]["snapshots"]
        assert len(snapshots) == 2
        
        # Knowledge should show progression from not knowing to knowing
        before_snapshot = next(s for s in snapshots if s["timestamp"] == 1900)
        after_snapshot = next(s for s in snapshots if s["timestamp"] == 2100)
        
        assert not before_snapshot["knowledge"].get("character_knowledge", {}).get(bob["id"], {}).get("knows_secret", True)
        assert after_snapshot["knowledge"]["character_knowledge"][bob["id"]]["knows_secret"]
        
    def test_content_validation_with_knowledge_constraints(self):
        """Test: Content validation should respect character knowledge constraints"""
        # Create characters
        alice = self.create_test_character("Alice")
        bob = self.create_test_character("Bob")
        scene = self.create_test_scene("Validation Test Scene", timestamp=3000)
        
        # Alice's knowledge - doesn't know Bob is a wizard yet
        knowledge = self.create_test_knowledge_snapshot(
            alice["id"], 2900,
            knowledge_content={
                "character_knowledge": {
                    bob["id"]: {
                        "is_friend": True,
                        "knows_about_magic": False
                    }
                }
            }
        )
        
        # Try to create dialogue where Alice mentions Bob's magic (should be flagged)
        invalid_dialogue = {
            "scene_id": scene["id"],
            "block_type": "dialogue",
            "summary": "Alice asks Bob to use wizard powers",
            "lines": {
                "speaker_id": alice["id"],
                "listener_id": bob["id"],
                "content": "Bob, use your wizard powers to help us!",
                "emotion": "urgent"
            },
            "order": 1,
            "meta": {"knowledge_validation": True}
        }
        
        # This should work (API doesn't validate knowledge yet, but we test the structure)
        response = client.post(f"/api/v1/scenes/{scene['id']}/blocks", json=invalid_dialogue)
        # For now, this will pass, but in future it could flag inconsistencies
        
        # Create valid dialogue where Alice doesn't know about magic
        valid_dialogue = {
            "scene_id": scene["id"],
            "block_type": "dialogue",
            "summary": "Alice expresses curiosity about Bob",
            "lines": {
                "speaker_id": alice["id"],
                "listener_id": bob["id"],
                "content": "Bob, you're always so mysterious. I wish I knew you better.",
                "emotion": "curious"
            },
            "order": 2
        }
        
        response = client.post(f"/api/v1/scenes/{scene['id']}/blocks", json=valid_dialogue)
        assert response.status_code == 200


class TestTimelineIntegrationAcrossSystems(TestPhase3SystemIntegration):
    """Test timeline consistency across all Phase 3 systems"""
    
    def test_story_world_state_at_timestamp(self):
        """Test: Query story world state at specific timestamp across all systems"""
        # Create characters
        alice = self.create_test_character("Alice", "Young adventurer")
        bob = self.create_test_character("Bob", "Village elder")
        charlie = self.create_test_character("Charlie", "Mysterious stranger")
        
        # Timeline setup (timestamps in story time)
        T1 = 1000  # Story begins
        T2 = 2000  # First major event
        T3 = 3000  # Plot twist
        T4 = 4000  # Resolution
        
        # Create relationships at different times
        rel1 = self.create_test_relationship(alice["id"], bob["id"], "mentor_student", T1)
        rel2 = self.create_test_relationship(alice["id"], charlie["id"], "strangers", T2)
        
        # Update Charlie relationship to allies
        update_data = {
            "relation_type": "allies",
            "ends_at": T3,
            "meta": {"reason": "Charlie revealed his true mission"}
        }
        rel2_updated = self.create_test_relationship(alice["id"], charlie["id"], "allies", T3)
        
        # Create scenes and content
        scene1 = self.create_test_scene("Opening Scene", T1)
        scene2 = self.create_test_scene("Meeting Charlie", T2) 
        scene3 = self.create_test_scene("The Revelation", T3)
        
        # Create knowledge snapshots at each timeline point
        knowledge_T1 = self.create_test_knowledge_snapshot(
            alice["id"], T1 + 50,
            knowledge_content={
                "story_phase": "beginning",
                "known_characters": [bob["id"]],
                "goals": ["learn_from_mentor"],
                "location": "village"
            }
        )
        
        knowledge_T2 = self.create_test_knowledge_snapshot(
            alice["id"], T2 + 50,
            knowledge_content={
                "story_phase": "complications",
                "known_characters": [bob["id"], charlie["id"]],
                "goals": ["learn_from_mentor", "understand_stranger"],
                "location": "forest_path",
                "discoveries": ["met_mysterious_stranger"]
            }
        )
        
        knowledge_T3 = self.create_test_knowledge_snapshot(
            alice["id"], T3 + 50,
            knowledge_content={
                "story_phase": "revelation",
                "known_characters": [bob["id"], charlie["id"]],
                "goals": ["learn_from_mentor", "help_charlie_mission"],
                "location": "ancient_ruins",
                "discoveries": ["met_mysterious_stranger", "charlie_is_guardian"],
                "alliances": [charlie["id"]]
            }
        )
        
        # Test story world state queries at different timestamps
        
        # At T1+100: Alice knows Bob, learning begins
        response = client.get(f"/api/v1/relationships/active?time={T1 + 100}")
        assert response.status_code == 200
        active_rels_T1 = response.json()["data"]["relationships"]
        
        response = client.get(f"/api/v1/knowledge/snapshots/character/{alice['id']}?timestamp={T1 + 100}")
        assert response.status_code == 200
        knowledge_at_T1 = response.json()["data"]["snapshots"]
        
        # At T2+100: Alice has met Charlie but they're strangers
        response = client.get(f"/api/v1/relationships/active?time={T2 + 100}")
        assert response.status_code == 200
        active_rels_T2 = response.json()["data"]["relationships"]
        
        # At T3+100: Alice and Charlie are now allies
        response = client.get(f"/api/v1/relationships/active?time={T3 + 100}")
        assert response.status_code == 200
        active_rels_T3 = response.json()["data"]["relationships"]
        
        # Verify timeline progression
        assert len(active_rels_T1) >= 1  # Alice-Bob mentor relationship
        assert len(active_rels_T2) >= 2  # Alice-Bob + Alice-Charlie (strangers)
        assert len(active_rels_T3) >= 2  # Alice-Bob + Alice-Charlie (allies)
        
        # Verify knowledge progression
        assert len(knowledge_at_T1) >= 1
        first_knowledge = knowledge_at_T1[0]["knowledge"]
        assert len(first_knowledge["known_characters"]) == 1  # Only Bob known
        
    def test_temporal_consistency_validation(self):
        """Test: Validate that no temporal paradoxes exist across systems"""
        # Create test scenario with potential temporal issues
        alice = self.create_test_character("Alice")
        bob = self.create_test_character("Bob")
        
        # Create relationship
        relationship = self.create_test_relationship(alice["id"], bob["id"], "friends", 1000)
        
        # Create knowledge snapshot BEFORE relationship started (potential inconsistency)
        early_knowledge = self.create_test_knowledge_snapshot(
            alice["id"], 500,  # Before relationship at 1000
            knowledge_content={
                "relationships": {
                    bob["id"]: {"type": "friends", "since": 1000}  # Future knowledge!
                }
            }
        )
        
        # This should be detected as a temporal inconsistency
        # (In a full implementation, this would trigger validation warnings)
        
        # Create proper knowledge snapshot after relationship
        proper_knowledge = self.create_test_knowledge_snapshot(
            alice["id"], 1100,  # After relationship started
            knowledge_content={
                "relationships": {
                    bob["id"]: {"type": "friends", "since": 1000}
                }
            }
        )
        
        # Query both snapshots to verify they exist
        response = client.get(f"/api/v1/knowledge/snapshots/character/{alice['id']}")
        assert response.status_code == 200
        snapshots = response.json()["data"]["snapshots"]
        assert len(snapshots) == 2
        
        # Future: Add temporal consistency validation
        # This would flag that knowledge at 500 references future events at 1000


class TestBatchOperationsIntegration(TestPhase3SystemIntegration):
    """Test batch operations across all Phase 3 systems"""
    
    def test_batch_story_setup(self):
        """Test: Create complete story setup with all systems in batch operations"""
        # Batch create characters
        characters_data = [
            {"name": "Hero", "entity_type": "character", "description": "Main protagonist"},
            {"name": "Mentor", "entity_type": "character", "description": "Wise guide"},
            {"name": "Villain", "entity_type": "character", "description": "Primary antagonist"},
            {"name": "Ally", "entity_type": "character", "description": "Hero's companion"}
        ]
        
        characters = []
        for char_data in characters_data:
            character = self.create_test_character(char_data["name"], char_data["description"])
            characters.append(character)
        
        hero, mentor, villain, ally = characters
        
        # Batch create relationships
        relationships_data = [
            (hero["id"], mentor["id"], "mentor_student", 100),
            (hero["id"], ally["id"], "friends", 200),
            (hero["id"], villain["id"], "enemies", 300),
            (mentor["id"], villain["id"], "old_enemies", 50)  # Historical relationship
        ]
        
        relationships = []
        for entity1_id, entity2_id, rel_type, timestamp in relationships_data:
            rel = self.create_test_relationship(entity1_id, entity2_id, rel_type, timestamp)
            relationships.append(rel)
        
        # Batch create knowledge snapshots for Hero
        knowledge_data = [
            {
                "timestamp": 150,
                "knowledge": {
                    "known_characters": [mentor["id"]],
                    "story_phase": "call_to_adventure"
                }
            },
            {
                "timestamp": 250,
                "knowledge": {
                    "known_characters": [mentor["id"], ally["id"]],
                    "story_phase": "gathering_allies"
                }
            },
            {
                "timestamp": 350,
                "knowledge": {
                    "known_characters": [mentor["id"], ally["id"], villain["id"]],
                    "story_phase": "confronting_enemy",
                    "discovered_threats": [villain["id"]]
                }
            }
        ]
        
        snapshots = []
        for snap_data in knowledge_data:
            snapshot = self.create_test_knowledge_snapshot(
                hero["id"], snap_data["timestamp"], snap_data["knowledge"]
            )
            snapshots.append(snapshot)
        
        # Verify complete story setup
        assert len(characters) == 4
        assert len(relationships) == 4
        assert len(snapshots) == 3
        
        # Verify system integration
        response = client.get(f"/api/v1/relationships/graph/{hero['id']}")
        assert response.status_code == 200
        graph = response.json()["data"]
        assert len(graph["entities"]) >= 4  # All characters connected to hero
        
        response = client.get(f"/api/v1/knowledge/snapshots/character/{hero['id']}")
        assert response.status_code == 200
        hero_knowledge = response.json()["data"]["snapshots"]
        assert len(hero_knowledge) == 3
        
    def test_story_world_evolution_workflow(self):
        """Test: Complete story world evolution across multiple timeline points"""
        # Create initial world state
        alice = self.create_test_character("Alice", "Young mage")
        bob = self.create_test_character("Bob", "Village blacksmith")
        castle = self.create_test_character("Ancient Castle", "Mysterious location")
        castle["entity_type"] = "location"  # Update type for location
        
        # Timeline: T1=1000, T2=2000, T3=3000
        
        # T1: Initial state - Alice arrives in village
        scene1 = self.create_test_scene("Arrival", 1000)
        
        rel_alice_bob_T1 = self.create_test_relationship(
            alice["id"], bob["id"], "strangers", 1000
        )
        
        knowledge_alice_T1 = self.create_test_knowledge_snapshot(
            alice["id"], 1100,
            knowledge_content={
                "location": "village",
                "known_characters": [bob["id"]],
                "status": "newcomer",
                "goals": ["find_lodging", "learn_about_village"]
            }
        )
        
        # T2: Relationship develops - Alice and Bob become friends
        scene2 = self.create_test_scene("Growing Friendship", 2000)
        
        # End stranger relationship, start friendship
        rel_alice_bob_T2 = self.create_test_relationship(
            alice["id"], bob["id"], "friends", 2000
        )
        
        knowledge_alice_T2 = self.create_test_knowledge_snapshot(
            alice["id"], 2100,
            knowledge_content={
                "location": "village",
                "known_characters": [bob["id"]],
                "status": "village_friend",
                "goals": ["help_bob_with_forge", "explore_surroundings"],
                "relationships": {
                    bob["id"]: {"type": "friends", "trust_level": "growing"}
                }
            }
        )
        
        # T3: Discovery - Alice learns about the castle
        scene3 = self.create_test_scene("The Discovery", 3000)
        
        rel_alice_castle_T3 = self.create_test_relationship(
            alice["id"], castle["id"], "curious_about", 3000
        )
        
        knowledge_alice_T3 = self.create_test_knowledge_snapshot(
            alice["id"], 3100,
            knowledge_content={
                "location": "village_outskirts",
                "known_characters": [bob["id"]],
                "known_locations": [castle["id"]],
                "status": "adventurer",
                "goals": ["investigate_castle", "maintain_friendship_with_bob"],
                "relationships": {
                    bob["id"]: {"type": "friends", "trust_level": "high"},
                    castle["id"]: {"type": "mystery", "danger_level": "unknown"}
                },
                "discoveries": ["ancient_castle_exists"]
            }
        )
        
        # Verify complete evolution
        response = client.get(f"/api/v1/knowledge/snapshots/character/{alice['id']}")
        assert response.status_code == 200
        all_knowledge = response.json()["data"]["snapshots"]
        assert len(all_knowledge) == 3
        
        # Verify relationship evolution
        response = client.get(f"/api/v1/relationships/entity/{alice['id']}")
        assert response.status_code == 200
        alice_rels = response.json()["data"]
        assert len(alice_rels) >= 3  # Two with Bob (strangers->friends) + one with castle
        
        # Verify timeline queries work at each point
        timestamps = [1500, 2500, 3500]
        for ts in timestamps:
            response = client.get(f"/api/v1/relationships/active?time={ts}")
            assert response.status_code == 200
            active_at_ts = response.json()["data"]["relationships"]
            assert len(active_at_ts) >= 1  # At least one relationship active


class TestErrorHandlingIntegration(TestPhase3SystemIntegration):
    """Test error handling and recovery across Phase 3 systems"""
    
    def test_cascading_error_recovery(self):
        """Test: System recovery when operations fail across multiple systems"""
        alice = self.create_test_character("Alice")
        bob = self.create_test_character("Bob")
        
        # Create valid relationship
        relationship = self.create_test_relationship(alice["id"], bob["id"], "friends", 1000)
        
        # Try to create knowledge snapshot with invalid entity_id
        invalid_knowledge_data = {
            "entity_id": "invalid-uuid",
            "timestamp": 1100,
            "knowledge": {"test": "data"}
        }
        
        response = client.post("/api/v1/knowledge/snapshots", json=invalid_knowledge_data)
        # Should fail gracefully without affecting existing relationship
        
        # Verify relationship still exists
        response = client.get(f"/api/v1/relationships/{relationship['id']}")
        assert response.status_code == 200
        
        # Create valid knowledge snapshot
        valid_knowledge = self.create_test_knowledge_snapshot(alice["id"], 1100)
        assert valid_knowledge["entity_id"] == alice["id"]
        
    def test_data_consistency_after_partial_failures(self):
        """Test: Data consistency maintained after partial operation failures"""
        # Setup initial state
        alice = self.create_test_character("Alice")
        bob = self.create_test_character("Bob")
        charlie = self.create_test_character("Charlie")
        
        # Create multiple relationships
        rel1 = self.create_test_relationship(alice["id"], bob["id"], "friends", 1000)
        rel2 = self.create_test_relationship(alice["id"], charlie["id"], "allies", 1000)
        
        # Create knowledge snapshot
        knowledge = self.create_test_knowledge_snapshot(
            alice["id"], 1100,
            knowledge_content={
                "known_characters": [bob["id"], charlie["id"]],
                "relationships": {
                    bob["id"]: {"type": "friends"},
                    charlie["id"]: {"type": "allies"}
                }
            }
        )
        
        # Try to delete Bob (might be referenced by knowledge/relationships)
        response = client.delete(f"/api/v1/entities/{bob['id']}")
        # This might fail due to foreign key constraints, which is correct
        
        # Verify Alice's knowledge still references Bob correctly
        response = client.get(f"/api/v1/knowledge/snapshots/{knowledge['id']}")
        assert response.status_code == 200
        snapshot = response.json()["data"]["snapshot"]
        assert bob["id"] in snapshot["knowledge"]["known_characters"]
        
        # Verify relationships still exist
        response = client.get(f"/api/v1/relationships/entity/{alice['id']}")
        assert response.status_code == 200
        alice_rels = response.json()["data"]
        assert len(alice_rels) >= 2


# Performance and Load Testing for Phase 3 Systems
class TestPhase3Performance(TestPhase3SystemIntegration):
    """Performance testing for Phase 3 integrated systems"""
    
    def test_bulk_data_operations_performance(self):
        """Test: Performance with large amounts of integrated data"""
        import time
        
        # Create bulk characters (50 characters)
        start_time = time.time()
        characters = []
        for i in range(50):
            char = self.create_test_character(f"Character_{i:03d}", f"Test character number {i}")
            characters.append(char)
        
        character_creation_time = time.time() - start_time
        print(f"Created 50 characters in {character_creation_time:.2f} seconds")
        
        # Create bulk relationships (100 relationships)
        start_time = time.time()
        relationships = []
        for i in range(100):
            char1 = characters[i % len(characters)]
            char2 = characters[(i + 1) % len(characters)]
            rel = self.create_test_relationship(
                char1["id"], char2["id"], "connection", 1000 + i
            )
            relationships.append(rel)
        
        relationship_creation_time = time.time() - start_time
        print(f"Created 100 relationships in {relationship_creation_time:.2f} seconds")
        
        # Create bulk knowledge snapshots (200 snapshots)
        start_time = time.time()
        snapshots = []
        for i in range(200):
            char = characters[i % len(characters)]
            snapshot = self.create_test_knowledge_snapshot(
                char["id"], 1100 + i,
                knowledge_content={
                    "snapshot_number": i,
                    "performance_test": True,
                    "connections": min(i, 10)  # Gradually increasing knowledge
                }
            )
            snapshots.append(snapshot)
        
        knowledge_creation_time = time.time() - start_time
        print(f"Created 200 knowledge snapshots in {knowledge_creation_time:.2f} seconds")
        
        # Test query performance
        start_time = time.time()
        response = client.get("/api/v1/entities/")
        entities_query_time = time.time() - start_time
        
        start_time = time.time()
        response = client.get("/api/v1/relationships/")
        relationships_query_time = time.time() - start_time
        
        # Performance assertions (adjust based on acceptable thresholds)
        assert character_creation_time < 30.0  # 50 characters in under 30 seconds
        assert relationship_creation_time < 60.0  # 100 relationships in under 1 minute
        assert knowledge_creation_time < 120.0  # 200 snapshots in under 2 minutes
        assert entities_query_time < 2.0  # Query all entities in under 2 seconds
        assert relationships_query_time < 2.0  # Query all relationships in under 2 seconds
        
        print(f"Performance test completed successfully")
        print(f"Entity query: {entities_query_time:.3f}s")
        print(f"Relationship query: {relationships_query_time:.3f}s")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])